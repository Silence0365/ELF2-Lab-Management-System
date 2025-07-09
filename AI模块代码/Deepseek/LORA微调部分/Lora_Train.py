# ======================== ReadMe ========================
#此代码是LORA训练代码
#DeepSeek-R1-Distill-Qwen-1.5B属于Qwen2蒸馏模型；q_proj, k_proj, v_proj, o_proj 是注意力机制中的四个核心线性层；"gate_proj, up_proj, down_proj" 是 Transformer 中的 前馈子层（FeedForward sublayer）
#Lora需插入到这几个层以便改变模型对输入训练集的关注部分，进而使得模型能够理解并处理训练集的信息
#target_modules的选择需取决于训练JSON的大小，若训练集较小，则优先改变["q_proj", "v_proj"]两层以确保模型稳定性，若训练集优质且数量足够，则可扩展至上面几个层
#采用ChatML 格式模板，确定<system>角色，以便用更少的训练集引导模型按设定好的角色进行对话，降低训练成本
#对于DeepSeek-R1-Distill-Qwen-1.5B模型，其具有思考推理模式，经验证，其tokenizer可以识别<think></think>,故为了保持其思考链不会受到破坏，建议在json中加上<think>COT</think>的思考链格式
# ======================== ReadMe ========================

from datasets import Dataset
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM, DataCollatorForSeq2Seq, TrainingArguments, Trainer

import torch
from peft import LoraConfig, TaskType, get_peft_model


# ======================== 数据集处理函数 ========================
def process_func(example):
    MAX_LENGTH = 1024    # Llama分词器会将一个中文字切分为多个token，因此需要放开一些最大长度，保证数据的完整性
    input_ids, attention_mask, labels = [], [], []
    instruction = tokenizer(f"<|im_start|>system\n现在你要扮演一个实验室智能助手--小黑<|im_end|>\n<|im_start|>user\n{example['instruction'] + example['input']}<|im_end|>\n<|im_start|>assistant\n", add_special_tokens=False)  # add_special_tokens 不在开头加 special_tokens
    response = tokenizer(f"{example['output']}", add_special_tokens=False)
    input_ids = instruction["input_ids"] + response["input_ids"] + [tokenizer.pad_token_id]
    attention_mask = instruction["attention_mask"] + response["attention_mask"] + [1]  # 补充eos token
    labels = [-100] * len(instruction["input_ids"]) + response["input_ids"] + [tokenizer.pad_token_id]
    if len(input_ids) > MAX_LENGTH:  # 截断使得Input对齐
        input_ids = input_ids[:MAX_LENGTH]
        attention_mask = attention_mask[:MAX_LENGTH]
        labels = labels[:MAX_LENGTH]
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels
    }


# ======================== LORA配置 ========================
config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    inference_mode=False, # 训练模式
    r=8, # Lora 秩-->Lora为低秩修改
    lora_alpha=32, # Lora alaph，具体作用参见 Lora 原理
    lora_dropout=0.1# Dropout 比例
)

# ======================== 训练配置 ========================
args = TrainingArguments(
    output_dir="./output/lora",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=16,
    logging_steps=10,
    num_train_epochs=3,
    save_steps=100,
    learning_rate=1e-4,
    save_on_each_node=True,
    gradient_checkpointing=True
)


if "__main__" == __name__:
    # 处理数据集
    # 将JSON文件转换为CSV文件
    df = pd.read_json('data/train_lora.json')
    ds = Dataset.from_pandas(df)
    # 加载tokenizer
    tokenizer = AutoTokenizer.from_pretrained('DeepSeek-R1-Distill-Qwen-1.5B', use_fast=False, trust_remote_code=True)
    tokenizer.pad_token_id = tokenizer.eos_token_id
    # 将数据集变化为token形式
    tokenized_id = ds.map(process_func, remove_columns=ds.column_names)

    # 创建模型并以半精度形式加载
    model = AutoModelForCausalLM.from_pretrained('DeepSeek-R1-Distill-Qwen-1.5B', device_map="auto",torch_dtype=torch.bfloat16)
    model.enable_input_require_grads() # 开启梯度检查点
    # 加载lora参数
    model = get_peft_model(model, config)
    # 使用trainer训练
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized_id,
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True),
    )
    trainer.train()
    response, history = model.chat(tokenizer, "你是谁", history=[], system="现在你要扮演一个实验室智能助手--小黑")
    print(response)