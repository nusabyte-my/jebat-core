import os
os.environ["HF_HUB_OFFLINE"] = "1"

# IMPORTANT: Import trl BEFORE torch to avoid segfault on Windows
from trl import SFTTrainer, SFTConfig
print("trl OK")

import torch
print(f"torch OK ({torch.__version__}, CUDA={torch.cuda.is_available()})")

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
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

CHECKPOINT = "output/checkpoint-6"

# Tokenizer from checkpoint (has adapter tokenizer)
tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT, local_files_only=True)
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

# Tokenize dataset — use shorter sequences to save VRAM
def tokenize_fn(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=512,  # Shorter to avoid OOM
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
print("Loading base model...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL,
    quantization_config=bnb_config,
    device_map="auto",
    local_files_only=True,
    torch_dtype=torch.float16,
)
print(f"Base model OK ({torch.cuda.memory_allocated()/1024**3:.2f}GB)")

# Resume from checkpoint adapter
print("Loading LoRA from checkpoint-6...")
model = PeftModel.from_pretrained(model, CHECKPOINT)
model.print_trainable_parameters()

# Unfreeze LoRA params for continued training
for name, param in model.named_parameters():
    if "lora_" in name:
        param.requires_grad = True
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"After unfreeze: {trainable:,} trainable params")

# Training — 2 more epochs (we already did 1)
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=2,          # 2 more epochs (total will be 3)
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    learning_rate=1e-4,          # Lower LR for resume
    lr_scheduler_type="cosine",
    warmup_ratio=0.05,
    logging_steps=5,
    save_strategy="epoch",
    fp16=True,
    max_seq_length=512,          # Shorter to avoid OOM
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

print("\n=== RESUMING TRAINING (epochs 2-3) ===")
trainer.train()
print("\n=== TRAINING COMPLETE ===")

# Save final adapter
adapter_dir = f"{OUTPUT_DIR}/jebat-coder-adapter"
model.save_pretrained(adapter_dir)
tokenizer.save_pretrained(adapter_dir)
print(f"Adapter saved: {adapter_dir}")
print(f"GPU peak: {torch.cuda.max_memory_allocated()/1024**3:.2f}GB")
