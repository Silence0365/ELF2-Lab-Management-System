# ======================== ReadMe ========================
# 源代码引用：
# 项目名    ：rknn-llm
# 作者      ：Rockchip AI Team (GitHub: @airockchip)
# 源仓库    ：https://github.com/airockchip/rknn-llm
# 文件路径  ：examples/rkllm_server_demo/rkllm_server/flask_server.py
# 引用时间  ：2025-07-03
# 引用目的  ：参考 Flask 架构搭建 RKLLM 推理接口服务，适配 RK3588 推理环境
# 修改说明  ：根据本地模型路径与推理逻辑做适配；集成 Function Calling 与流式返回
# License   ：Apache License 2.0
# ======================== ReadMe ========================

import ctypes
import sys
import os
import subprocess
import resource
import threading
import time
import argparse
import json
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ===================== RKLLM 常量定义 =====================
class LLMCallState:
    RKLLM_RUN_NORMAL = 0
    RKLLM_RUN_WAITING = 1
    RKLLM_RUN_FINISH = 2
    RKLLM_RUN_ERROR = 3

class RKLLMInputMode:
    RKLLM_INPUT_PROMPT = 0
    RKLLM_INPUT_TOKEN = 1
    RKLLM_INPUT_EMBED = 2
    RKLLM_INPUT_MULTIMODAL = 3

class RKLLMInferMode:
    RKLLM_INFER_GENERATE = 0
    RKLLM_INFER_GET_LAST_HIDDEN_LAYER = 1
    RKLLM_INFER_GET_LOGITS = 2

# ===================== RKLLM 结构体定义 =====================
class RKLLMExtendParam(ctypes.Structure):
    _fields_ = [
        ("base_domain_id", ctypes.c_int32),
        ("embed_flash", ctypes.c_int8),
        ("enabled_cpus_num", ctypes.c_int8),
        ("enabled_cpus_mask", ctypes.c_uint32),
        ("reserved", ctypes.c_uint8 * 106)
    ]

class RKLLMParam(ctypes.Structure):
    _fields_ = [
        ("model_path", ctypes.c_char_p),
        ("max_context_len", ctypes.c_int32),
        ("max_new_tokens", ctypes.c_int32),
        ("top_k", ctypes.c_int32),
        ("n_keep", ctypes.c_int32),
        ("top_p", ctypes.c_float),
        ("temperature", ctypes.c_float),
        ("repeat_penalty", ctypes.c_float),
        ("frequency_penalty", ctypes.c_float),
        ("presence_penalty", ctypes.c_float),
        ("mirostat", ctypes.c_int32),
        ("mirostat_tau", ctypes.c_float),
        ("mirostat_eta", ctypes.c_float),
        ("skip_special_token", ctypes.c_bool),
        ("is_async", ctypes.c_bool),
        ("img_start", ctypes.c_char_p),
        ("img_end", ctypes.c_char_p),
        ("img_content", ctypes.c_char_p),
        ("extend_param", RKLLMExtendParam),
    ]

class RKLLMLoraAdapter(ctypes.Structure):
    _fields_ = [
        ("lora_adapter_path", ctypes.c_char_p),
        ("lora_adapter_name", ctypes.c_char_p),
        ("scale", ctypes.c_float)
    ]

class RKLLMEmbedInput(ctypes.Structure):
    _fields_ = [
        ("embed", ctypes.POINTER(ctypes.c_float)),
        ("n_tokens", ctypes.c_size_t)
    ]

class RKLLMTokenInput(ctypes.Structure):
    _fields_ = [
        ("input_ids", ctypes.POINTER(ctypes.c_int32)),
        ("n_tokens", ctypes.c_size_t)
    ]

class RKLLMMultiModelInput(ctypes.Structure):
    _fields_ = [
        ("prompt", ctypes.c_char_p),
        ("image_embed", ctypes.POINTER(ctypes.c_float)),
        ("n_image_tokens", ctypes.c_size_t),
        ("n_image", ctypes.c_size_t),
        ("image_width", ctypes.c_size_t),
        ("image_height", ctypes.c_size_t)
    ]

class RKLLMInputUnion(ctypes.Union):
    _fields_ = [
        ("prompt_input", ctypes.c_char_p),
        ("embed_input", RKLLMEmbedInput),
        ("token_input", RKLLMTokenInput),
        ("multimodal_input", RKLLMMultiModelInput)
    ]

class RKLLMInput(ctypes.Structure):
    _fields_ = [
        ("input_mode", ctypes.c_int),
        ("input_data", RKLLMInputUnion)
    ]

class RKLLMLoraParam(ctypes.Structure):
    _fields_ = [
        ("lora_adapter_name", ctypes.c_char_p)
    ]

class RKLLMPromptCacheParam(ctypes.Structure):
    _fields_ = [
        ("save_prompt_cache", ctypes.c_int),
        ("prompt_cache_path", ctypes.c_char_p)
    ]

class RKLLMInferParam(ctypes.Structure):
    _fields_ = [
        ("mode", ctypes.c_int),
        ("lora_params", ctypes.POINTER(RKLLMLoraParam)),
        ("prompt_cache_params", ctypes.POINTER(RKLLMPromptCacheParam)),
        ("keep_history", ctypes.c_int)
    ]

class RKLLMResultLastHiddenLayer(ctypes.Structure):
    _fields_ = [
        ("hidden_states", ctypes.POINTER(ctypes.c_float)),
        ("embd_size", ctypes.c_int),
        ("num_tokens", ctypes.c_int)
    ]

class RKLLMResultLogits(ctypes.Structure):
    _fields_ = [
        ("logits", ctypes.POINTER(ctypes.c_float)),
        ("vocab_size", ctypes.c_int),
        ("num_tokens", ctypes.c_int)
    ]

class RKLLMResult(ctypes.Structure):
    _fields_ = [
        ("text", ctypes.c_char_p),
        ("token_id", ctypes.c_int),
        ("last_hidden_layer", RKLLMResultLastHiddenLayer),
        ("logits", RKLLMResultLogits)
    ]

# 定义句柄类型
RKLLM_Handle_t = ctypes.c_void_p

# ===================== 初始化模型回调 =====================
global_text = ""
global_state = -1

def callback_impl(result, userdata, state):
    global global_text, global_state
    if state == LLMCallState.RKLLM_RUN_FINISH:
        global_state = state
    elif state == LLMCallState.RKLLM_RUN_ERROR:
        global_state = state
    elif state == LLMCallState.RKLLM_RUN_NORMAL:
        global_state = state
        global_text += result.contents.text.decode('utf-8')
        print("recv text:", result.contents.text.decode('utf-8'))
        sys.stdout.flush()

callback_type = ctypes.CFUNCTYPE(None, ctypes.POINTER(RKLLMResult), ctypes.c_void_p, ctypes.c_int)
callback = callback_type(callback_impl)

# ===================== RKLLM类封装 =====================
class RKLLM(object):
    def __init__(self, model_path, lora_model_path=None, prompt_cache_path=None):
        self.handle = RKLLM_Handle_t()

        rkllm_param = RKLLMParam()
        rkllm_param.model_path = bytes(model_path, 'utf-8')
        rkllm_param.max_context_len = 4096
        rkllm_param.max_new_tokens = -1
        rkllm_param.skip_special_token = True
        rkllm_param.n_keep = -1
        rkllm_param.top_k = 1
        rkllm_param.top_p = 0.9
        rkllm_param.temperature = 0.8
        rkllm_param.repeat_penalty = 1.1
        rkllm_param.frequency_penalty = 0.0
        rkllm_param.presence_penalty = 0.0
        rkllm_param.mirostat = 0
        rkllm_param.mirostat_tau = 5.0
        rkllm_param.mirostat_eta = 0.1
        rkllm_param.is_async = False
        rkllm_param.img_start = b""
        rkllm_param.img_end = b""
        rkllm_param.img_content = b""
        rkllm_param.extend_param.base_domain_id = 0
        rkllm_param.extend_param.enabled_cpus_num = 4
        rkllm_param.extend_param.enabled_cpus_mask = (1 << 4) | (1 << 5) | (1 << 6) | (1 << 7)

        # 加载动态库函数
        self.rkllm_init = rkllm_lib.rkllm_init
        self.rkllm_init.argtypes = [ctypes.POINTER(RKLLM_Handle_t), ctypes.POINTER(RKLLMParam), callback_type]
        self.rkllm_init.restype = ctypes.c_int

        self.rkllm_run = rkllm_lib.rkllm_run
        self.rkllm_run.argtypes = [RKLLM_Handle_t, ctypes.POINTER(RKLLMInput), ctypes.POINTER(RKLLMInferParam), ctypes.c_void_p]
        self.rkllm_run.restype = ctypes.c_int

        self.rkllm_destroy = rkllm_lib.rkllm_destroy
        self.rkllm_destroy.argtypes = [RKLLM_Handle_t]
        self.rkllm_destroy.restype = ctypes.c_int

        # 初始化模型
        ret = self.rkllm_init(ctypes.byref(self.handle), ctypes.byref(rkllm_param), callback)
        if ret != 0:
            raise RuntimeError("rkllm_init failed!")

        # LoRA 加载（如果有）
        self.rkllm_infer_params = RKLLMInferParam()
        ctypes.memset(ctypes.byref(self.rkllm_infer_params), 0, ctypes.sizeof(RKLLMInferParam))
        self.rkllm_infer_params.mode = RKLLMInferMode.RKLLM_INFER_GENERATE
        self.rkllm_infer_params.lora_params = None
        self.rkllm_infer_params.keep_history = 0

        if lora_model_path:
            lora_adapter = RKLLMLoraAdapter()
            lora_adapter.lora_adapter_path = lora_model_path.encode('utf-8')
            lora_adapter.lora_adapter_name = b"default"
            lora_adapter.scale = 1.0

            rkllm_load_lora = rkllm_lib.rkllm_load_lora
            rkllm_load_lora.argtypes = [RKLLM_Handle_t, ctypes.POINTER(RKLLMLoraAdapter)]
            rkllm_load_lora.restype = ctypes.c_int

            rkllm_load_lora(self.handle, ctypes.byref(lora_adapter))

    def run(self, prompt: str):
        rkllm_input = RKLLMInput()
        rkllm_input.input_mode = RKLLMInputMode.RKLLM_INPUT_PROMPT
        rkllm_input.input_data.prompt_input = prompt.encode('utf-8')
        self.rkllm_run(self.handle, ctypes.byref(rkllm_input), ctypes.byref(self.rkllm_infer_params), None)

    def release(self):
        self.rkllm_destroy(self.handle)

# ===================== Flask 接口 =====================
lock = threading.Lock()
is_blocking = False

@app.route('/rkllm_chat', methods=['POST'])
def receive_message():
    global global_text, global_state, is_blocking

    if is_blocking or global_state == LLMCallState.RKLLM_RUN_NORMAL:
        return jsonify({'status': 'error', 'message': 'RKLLM_Server is busy! Try later.'}), 503

    lock.acquire()
    try:
        is_blocking = True

        data = request.json
        if not data or 'messages' not in data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON data!'}), 400

        messages = data['messages']

        rkllm_responses = {
            "id": "rkllm_chat",
            "object": "rkllm_chat",
            "created": None,
            "choices": [],
            "usage": {
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None
            }
        }

        # 非流模式处理
        if not data.get("stream", False):
            global_text = ""
            global_state = -1
            for index, message in enumerate(messages):
                input_prompt = message['content']
                model_thread = threading.Thread(target=rkllm_model.run, args=(input_prompt,))
                model_thread.start()
                model_thread.join()

                rkllm_output = global_text
                global_text = ""

                rkllm_responses["choices"].append({
                    "index": index,
                    "message": {
                        "role": "assistant",
                        "content": rkllm_output
                    },
                    "logprobs": None,
                    "finish_reason": "stop"
                })

            return jsonify(rkllm_responses), 200

        # 流模式处理
        else:
            def generate():
                global global_text, global_state

                # 如果没有 system 提示，则插入默认 system 指令
                if not any(m["role"] == "system" for m in messages):
                    messages.insert(0, {
                        "role": "system",
                        "content": "现在你要扮演一个实验室智能助手--小黑"
                    })

                # 构造一次完整 prompt（历史全部拼接 + assistant 段落）
                prompt_text = ""
                for msg in messages:
                    prompt_text += f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>\n"
                prompt_text += "<|im_start|>assistant\n"

                # 启动模型推理线程
                global_text = ""
                global_state = -1
                model_thread = threading.Thread(target=rkllm_model.run, args=(prompt_text,))
                model_thread.start()

                last_len = 0
                while model_thread.is_alive() or last_len < len(global_text):
                    if last_len < len(global_text):
                        new_text = global_text[last_len:]
                        last_len = len(global_text)


                        rkllm_responses["choices"] = [{
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": new_text
                            },
                            "logprobs": None,
                            "finish_reason": "stop" if global_state == LLMCallState.RKLLM_RUN_FINISH else None
                        }]

                        yield f"{json.dumps(rkllm_responses)}\n\n"
                    else:
                        time.sleep(0.01)

                model_thread.join()

                1
            return Response(generate(), content_type='text/plain')

    finally:
        is_blocking = False
        lock.release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--rkllm_model_path', type=str, required=True)
    parser.add_argument('--target_platform', type=str, required=True)
    parser.add_argument('--lora_model_path', type=str)
    parser.add_argument('--prompt_cache_path', type=str)
    args = parser.parse_args()

    if not os.path.exists(args.rkllm_model_path):
        print("Error: Invalid model path")
        sys.exit(1)

    if args.lora_model_path and not os.path.exists(args.lora_model_path):
        print("Error: Invalid lora model path")
        sys.exit(1)

    if args.prompt_cache_path and not os.path.exists(args.prompt_cache_path):
        print("Error: Invalid prompt cache path")
        sys.exit(1)

    # 频率修正脚本（根据平台）
    subprocess.run(f"sudo bash fix_freq_{args.target_platform}.sh", shell=True)

    # 资源限制
    resource.setrlimit(resource.RLIMIT_NOFILE, (102400, 102400))

    # 加载动态库（请修改为你的librkllmrt.so路径）
    rkllm_lib = ctypes.CDLL("lib/librkllmrt.so")

    print("=========init....===========")
    sys.stdout.flush()
    rkllm_model = RKLLM(args.rkllm_model_path, args.lora_model_path, args.prompt_cache_path)
    print("RKLLM Model has been initialized successfully！")
    print("==============================")
    sys.stdout.flush()

    app.run(host='0.0.0.0', port=8080, threaded=True, debug=False)

    print("====================")
    print("Releasing RKLLM model resources...")
    rkllm_model.release()
    print("====================")
