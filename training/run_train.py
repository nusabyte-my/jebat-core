import os
os.environ["HF_HUB_OFFLINE"] = "1"

# IMPORTANT: Import trl BEFORE torch to avoid segfault on Windows
from trl import SFTTrainer, SFTConfig
print("trl OK")

import torch
print(f"torch OK ({torch.__version__}, CUDA={torch.cuda.is_available()})")

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
import json
print("All imports OK")

# Load data
data = []
with open("training_data.jsonl") as f:
    for line in f:
        if line.strip():
            data.append(json.loads(line))
print(f"Loaded {len(data)} examples")

MODEL = os.path.expanduser(
    "~/.cache/huggingface/hub/models--Qwen--Qwen2.5-Coder-3B-Instruct"
    "/snapshots/488639f1ff808d1d3d0ba301aef8c11461451ec5"
)

# Tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
print("Tokenizer OK")

# Format for SFT
def fmt(ex):
    msgs = [
        {"role": "system", "content": ex.get("system", "You are JEBAT-Builder.")},
        {"role": "user", "content": ex["instruction"] + ("\n\n" + ex["input"] if ex.get("input") else "")},
        {"role": "assistant", "content": ex["output"]},
    ]
    return tokenizer.apply_chat_template(msgs, tokenize=False)

texts = [fmt(ex) for ex in data]
dataset = Dataset.from_dict({"text": texts})
print(f"Dataset OK ({len(dataset)} samples)")

# Tokenize dataset for training
def tokenize_fn(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=1024,
        padding="max_length",
    )
tokenized_dataset = dataset.map(tokenize_fn, batched=True, remove_columns=["text"])
print(f"Tokenized OK ({len(tokenized_dataset)} samples)")

# 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)
print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL,
    quantization_config=bnb_config,
    device_map="auto",
    local_files_only=True,
    torch_dtype=torch.float16,
)
print(f"Model OK, GPU: {torch.cuda.memory_allocated()/1024**3:.2f}GB")

# LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)
model = get_peft_model(model, lora_config)
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"LoRA OK ({trainable:,} trainable / {total:,} total)")

# Training
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.1,
    logging_steps=10,
    save_strategy="epoch",
    fp16=True,
    max_seq_length=1024,
    dataset_text_field="text",
    optim="paged_adamw_8bit",
    report_to="none",
    remove_unused_columns=False,
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=tokenized_dataset,
    args=training_args,
)

print("\n=== TRAINING START ===")
trainer.train()
print("\n=== TRAINING DONE ===")

model.save_pretrained(f"{OUTPUT_DIR}/jebat-coder-adapter")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/jebat-coder-adapter")
print(f"Adapter saved to {OUTPUT_DIR}/jebat-coder-adapter")
print(f"GPU peak: {torch.cuda.max_memory_allocated()/1024**3:.2f}GB")
