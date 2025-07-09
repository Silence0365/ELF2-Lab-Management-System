# ======================== ReadMe ========================
#此代码是LORA与原模型整合代码
#本代码是将LORA写入原始权重，不动态加载LORA-->经测试RKLLM转化LORA模型时会出现找不到Config.json文件
# ======================== ReadMe ========================
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

# 基础模型和 LoRA 路径
base_model_path = "DeepSeek-R1-Distill-Qwen-1.5B"
lora_path = "output/lora/checkpoint-750"
merged_save_path = "merged-model"

# 加载基础模型和 LoRA 增量权重
model = AutoModelForCausalLM.from_pretrained(base_model_path, torch_dtype=torch.float16)
model = PeftModel.from_pretrained(model, lora_path)

# 合并 LoRA 权重
model = model.merge_and_unload() 

# 保存为一个完整模型
model.save_pretrained(merged_save_path, safe_serialization=True)
tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)
tokenizer.save_pretrained(merged_save_path)
