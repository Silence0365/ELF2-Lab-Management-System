# ======================== ReadMe ========================
# 源代码引用：
# 项目名    ：rknn_model_zoo
# 作者      ：Rockchip AI Team (GitHub: @airockchip)
# 源仓库    ：https://github.com/airockchip/rknn_model_zoo
# 文件路径  ：examples/whisper/python/whisper.py
# 引用时间  ：2025-07-03
# 引用目的  ：参考 Whisper 模型的 RKNN 加载与推理流程,部署Flask以配合前端实现语音转文字输入功能
# 修改说明  ：根据本地部署需求适配 Flask 接口、加入音频上传与中文识别、支持 encoder + decoder 分模型加载
# License   ：Apache License 2.0
# ======================== ReadMe ========================


from flask import Flask, request, jsonify
import numpy as np
import torch
import torch.nn.functional as F
import scipy
import onnxruntime
from rknnlite.api import RKNNLite
from pydub import AudioSegment
from flask_cors import CORS
import io
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# 参数
SAMPLE_RATE = 16000
N_FFT = 400
HOP_LENGTH = 160
CHUNK_LENGTH = 20
MAX_LENGTH = CHUNK_LENGTH * 100
N_MELS = 80

# base64 解码函数
def get_char_index(c):
    if 'A' <= c <= 'Z':
        return ord(c) - ord('A')
    elif 'a' <= c <= 'z':
        return ord(c) - ord('a') + 26
    elif '0' <= c <= '9':
        return ord(c) - ord('0') + 52
    elif c == '+':
        return 62
    elif c == '/':
        return 63
    else:
        raise ValueError(f"Unknown base64 character: {c}")

def base64_decode(encoded_string):
    if not encoded_string:
        return ""
    output_bytes = bytearray()
    i = 0
    while i < len(encoded_string):
        if encoded_string[i] == '=':
            break
        b1 = get_char_index(encoded_string[i])
        b2 = get_char_index(encoded_string[i+1])
        output_bytes.append((b1 << 2) | (b2 >> 4))
        if encoded_string[i+2] == '=':
            break
        b3 = get_char_index(encoded_string[i+2])
        output_bytes.append(((b2 & 0xF) << 4) | (b3 >> 2))
        if encoded_string[i+3] == '=':
            break
        b4 = get_char_index(encoded_string[i+3])
        output_bytes.append(((b3 & 0x3) << 6) | b4)
        i += 4
    return output_bytes.decode('utf-8', errors='replace')

# 模型加载与推理
def init_model(model_path):
    if model_path.endswith(".rknn"):
        model = RKNNLite()
        ret = model.load_rknn(model_path)
        if ret != 0:
            raise RuntimeError(f"Load RKNN model \"{model_path}\" failed!")
        ret = model.init_runtime()
        if ret != 0:
            raise RuntimeError("RKNN runtime init failed")
    else:
        model = onnxruntime.InferenceSession(model_path, providers=['CPUExecutionProvider'])
    return model

def release_model(model):
    if isinstance(model, RKNNLite):
        model.release()

def run_encoder(model, x):
    if isinstance(model, RKNNLite):
        return model.inference(inputs=x)[0]
    else:
        return model.run(None, {"x": x})[0]

def _decode(model, tokens, enc_out):
    tokens_np = np.asarray([tokens], dtype="int64")
    inputs = [tokens_np, enc_out]
    out = model.inference(inputs=inputs)
    if out is None:
        raise RuntimeError("❌ Decoder 推理失败，返回 None，可能是 tokens 太长")
    return out[0]

def run_decoder(model, enc_out, vocab, task_code):
    end_token = 50257
    timestamp_begin = 50364
    tokens = [50258, task_code, 50359, 50363]
    tokens = tokens * 3
    max_tokens = 12
    pop_id = max_tokens
    tokens_str = ''
    next_token = 50258

    while next_token != end_token:
        out_decoder = _decode(model, tokens, enc_out)
        next_token = out_decoder[0, -1].argmax()
        next_token_str = vocab.get(str(next_token), "")
        tokens.append(next_token)

        if next_token == end_token:
            tokens.pop(-1)
            break
        if next_token > timestamp_begin:
            continue
        if pop_id > 4:
            pop_id -= 1
        tokens.pop(pop_id)
        tokens_str += next_token_str

    result = tokens_str.replace('\u0120', ' ').replace('<|endoftext|>', '').replace('\n', '')
    return result.strip()

def read_vocab(path):
    vocab = {}
    with open(path, 'r') as f:
        for line in f:
            parts = line.strip().split(' ', 1)
            if len(parts) == 2:
                vocab[parts[0]] = parts[1]
            else:
                vocab[parts[0]] = ''
    return vocab

# 特征提取
def mel_filters(n_mels):
    filters_path = "../model/mel_80_filters.txt"
    mels_data = np.loadtxt(filters_path, dtype=np.float32).reshape((n_mels, 201))
    return torch.from_numpy(mels_data)

def log_mel_spectrogram(audio, n_mels):
    if not torch.is_tensor(audio):
        audio = torch.from_numpy(audio)
    window = torch.hann_window(N_FFT)
    stft = torch.stft(audio, N_FFT, HOP_LENGTH, window=window, return_complex=True)
    magnitudes = stft[..., :-1].abs() ** 2
    filters = mel_filters(n_mels)
    mel_spec = filters @ magnitudes
    log_spec = torch.clamp(mel_spec, min=1e-10).log10()
    log_spec = torch.maximum(log_spec, log_spec.max() - 8.0)
    log_spec = (log_spec + 4.0) / 4.0
    return log_spec

def pad_or_trim(mel, length=MAX_LENGTH):
    if mel.shape[1] < length:
        mel = np.pad(mel, ((0, 0), (0, length - mel.shape[1])), constant_values=0)
    elif mel.shape[1] > length:
        mel = mel[:, :length]
    return mel

# ========== Whisper 推理接口 ==========
@app.route('/whisper', methods=['POST'])
def whisper():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    file_ext = filename.split('.')[-1].lower()
    file_bytes = file.read()

    # ✅ 自动判断 webm 或其他格式
    try:
        if file_ext == "webm":
            audio = AudioSegment.from_file(io.BytesIO(file_bytes), format="webm")
        else:
            audio = AudioSegment.from_file(io.BytesIO(file_bytes))  # 尝试自动识别
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio_np = np.array(audio.get_array_of_samples()).astype(np.float32) / 32768.0
    except Exception as e:
        return jsonify({'error': f'音频解析失败: {str(e)}'}), 500

    # 特征提取
    x_mel = log_mel_spectrogram(audio_np, N_MELS).numpy()
    x_mel = pad_or_trim(x_mel)
    x_mel = np.expand_dims(x_mel, 0)

    # 加载模型
    encoder_model = init_model('/home/elf/Desktop/Project/AI/whisper/rknn_whisper_demo/model/whisper_encoder_base_20s.rknn')#encoder路径
    decoder_model = init_model('/home/elf/Desktop/Project/AI/whisper/rknn_whisper_demo/model/whisper_decoder_base_20s.rknn')#decoder路径
    vocab = read_vocab('/home/elf/Desktop/Project/AI/whisper/rknn_whisper_demo/model/vocab_zh.txt')#vocab路径-->中文需对应中文的vocab

    # 推理
    out_encoder = run_encoder(encoder_model, x_mel)
    result = run_decoder(decoder_model, out_encoder, vocab, task_code=50260)
    print("📝 推理结果(编码):", result)

    # base64 解码
    result = base64_decode(result)
    print("📝 推理结果(解码后):", result)

    release_model(encoder_model)
    release_model(decoder_model)

    return jsonify({'transcript': result})

# 启动服务
if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=5000)
