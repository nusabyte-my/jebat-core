#!/usr/bin/env python3
"""
train.py — CLI fine-tuner for JEBAT-Builder
Trains qwen2.5-coder:7b on expert training data using QLoRA on RTX 3060 6GB.

Usage:
    python train.py                    # Full training (3 epochs)
    python train.py --epochs 1         # Quick test
    python train.py --test-only        # Test a saved model
    python train.py --deploy           # Upload GGUF to .206 server
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────
TRAINING_DATA = Path(__file__).parent / "training_data.jsonl"
OUTPUT_DIR = Path(__file__).parent / "output"
GGUF_DIR = Path(__file__).parent / "gguf"
MODEL_NAME = "Qwen/Qwen2.5-Coder-7B-Instruct"
MAX_SEQ_LENGTH = 2048
LORA_RANK = 16
SERVER = "root@72.62.255.206"
REMOTE_GGUF = "/tmp/jebat-builder.gguf"
REMOTE_MODELFILE = "/tmp/Modelfile"


def banner(text, width=60):
    print(f"\n{'═'*width}")
    print(f"  {text}")
    print(f"{'═'*width}\n")


def check_gpu():
    """Check CUDA GPU availability."""
    import torch
    if not torch.cuda.is_available():
        print("ERROR: No CUDA GPU available. Training requires a GPU.")
        sys.exit(1)
    name = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"  GPU: {name}")
    print(f"  VRAM: {vram:.1f} GB")
    if vram < 5:
        print("  WARNING: Less than 5GB VRAM. Training may fail.")
    return name, vram


def load_data(path):
    """Load training data from JSONL file."""
    examples = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            examples.append(json.loads(line))
    return examples


def format_chat(example):
    """Format example as ChatML for Qwen2.5."""
    instruction = example["instruction"]
    input_ctx = example.get("input", "")
    output = example["output"]

    if input_ctx:
        prompt = f"{instruction}\n\nContext: {input_ctx}"
    else:
        prompt = instruction

    return {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": output},
        ]
    }


def train(args):
    """Run QLoRA fine-tuning."""
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, TaskType
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from trl import SFTTrainer, SFTConfig

    banner("JEBAT-BUILDER Fine-Tuning (QLoRA)")

    # ── GPU check ──
    gpu_name, vram = check_gpu()

    # ── Load data ──
    print(f"\nLoading training data from {TRAINING_DATA}...")
    raw_data = load_data(TRAINING_DATA)
    print(f"  Loaded {len(raw_data)} examples")

    # Convert to chat format
    formatted = [format_chat(ex) for ex in raw_data]
    dataset = Dataset.from_list(formatted)
    print(f"  Dataset ready ({len(dataset)} samples)")

    # ── Quantization config (4-bit for 6GB VRAM) ──
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # ── Load model ──
    print(f"\nLoading model: {MODEL_NAME}")
    print("  (Downloading ~5GB on first run, cached after)")
    start = time.time()

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )
    print(f"  Model loaded in {time.time()-start:.1f}s")

    # ── LoRA config ──
    lora_config = LoraConfig(
        r=LORA_RANK,
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                         "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"  LoRA applied: {trainable:,} trainable / {total:,} total ({100*trainable/total:.2f}%)")

    # ── Training args ──
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    training_args = SFTConfig(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        save_strategy="epoch",
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_text_field="messages",
        packing=True,
    )

    # ── Trainer ──
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
    )

    # ── Train ──
    banner(f"Training: {args.epochs} epochs, batch {args.batch_size}, LR 2e-4")
    start = time.time()
    trainer.train()
    elapsed = time.time() - start
    print(f"\nTraining complete in {elapsed/60:.1f} minutes")

    # ── Save LoRA adapter ──
    model.save_pretrained(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print(f"LoRA adapter saved to {OUTPUT_DIR}")

    return str(OUTPUT_DIR)


def export_gguf(adapter_dir):
    """Export LoRA adapter to GGUF format using llama.cpp."""
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    banner("Exporting to GGUF")

    GGUF_DIR.mkdir(parents=True, exist_ok=True)

    # Check if llama.cpp export script exists
    export_script = None
    for candidate in [
        Path.home() / ".llama.cpp" / "convert_hf_to_gguf.py",
        Path("/opt/llama.cpp/convert_hf_to_gguf.py"),
        Path("C:/llama.cpp/convert_hf_to_gguf.py"),
    ]:
        if candidate.exists():
            export_script = candidate
            break

    # Merge LoRA and save full model
    print("Merging LoRA adapter into base model...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    model = PeftModel.from_pretrained(base_model, adapter_dir)
    model = model.merge_and_unload()

    merged_dir = GGUF_DIR / "merged"
    merged_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(merged_dir))
    tokenizer.save_pretrained(str(merged_dir))
    print(f"Merged model saved to {merged_dir}")

    if export_script:
        print(f"\nConverting to GGUF (Q4_K_M)...")
        gguf_out = GGUF_DIR / "jebat-builder-Q4_K_M.gguf"
        subprocess.run([
            sys.executable, str(export_script),
            str(merged_dir),
            "--outfile", str(gguf_out),
            "--outtype", "q4_k_m",
        ], check=True)
        print(f"GGUF saved: {gguf_out}")
        return str(gguf_out)
    else:
        print("\nllama.cpp not found. To convert manually:")
        print(f"  1. Install llama.cpp: git clone https://github.com/ggerganov/llama.cpp")
        print(f"  2. Convert: python convert_hf_to_gguf.py {merged_dir} --outfile {GGUF_DIR}/jebat-builder-Q4_K_M.gguf --outtype q4_k_m")
        print(f"\nMerged model available at: {merged_dir}")
        print("  (Can be used directly with transformers)")
        return str(merged_dir)


def deploy(gguf_path):
    """Upload GGUF to .206 server and create Ollama model."""
    banner("Deploying to .206 Server")

    print(f"  File: {gguf_path}")
    print(f"  Server: {SERVER}")

    # Upload GGUF
    print("\n[1/3] Uploading GGUF...")
    subprocess.run(["scp", gguf_path, f"{SERVER}:{REMOTE_GGUF}"], check=True)
    print("  Done.")

    # Create Modelfile on server
    print("[2/3] Creating Modelfile...")
    modelfile_content = """FROM /tmp/jebat-builder.gguf

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096

SYSTEM \"\"\"You are JEBAT-Builder, a specialized coding AI assistant created by NusaByte. You are part of the JEBAT Sovereign AI Platform v7.0. Write clean, production-ready code. Follow JEBAT coding conventions. Prefer dark-themed terminal UIs. Reference DESIGN.md tokens for UI code. Always consider security implications.\"\"\"
"""
    subprocess.run([
        "ssh", SERVER, f"cat > {REMOTE_MODELFILE} << 'MODELEOF'\n{modelfile_content}MODELEOF"
    ], check=True)
    print("  Done.")

    # Create Ollama model
    print("[3/3] Creating Ollama model...")
    subprocess.run(["ssh", SERVER, "ollama create jebat-builder -f /tmp/Modelfile"], check=True)
    print("  Done.")

    # Verify
    print("\nVerifying...")
    result = subprocess.run(
        ["curl", "-s", "https://jebat.online/ollama/api/tags"],
        capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
        models = [m["name"] for m in data.get("models", [])]
        print(f"Models: {models}")
        if any("jebat-builder" in m for m in models):
            print("SUCCESS: jebat-builder is live!")
        else:
            print("WARNING: jebat-builder not in model list")
    except Exception:
        print("Could not verify (curl failed)")

    print(f"\nTest it:")
    print(f'  curl https://jebat.online/ollama/v1/chat/completions \\')
    print(f'    -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"model":"jebat-builder","messages":[{{"role":"user","content":"Create a FastAPI endpoint"}}]}}\'')


def test_model():
    """Test a fine-tuned model locally."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import PeftModel

    banner("Testing Fine-Tuned Model")

    if not OUTPUT_DIR.exists():
        print(f"ERROR: No trained model found at {OUTPUT_DIR}")
        print("Run training first: python train.py")
        sys.exit(1)

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    model = PeftModel.from_pretrained(base_model, str(OUTPUT_DIR))
    model.eval()

    prompts = [
        "Create a FastAPI endpoint with JWT authentication and rate limiting",
        "Write a Python port scanner with multi-threading",
        "How do I use JEBAT multi-agent system?",
    ]

    for prompt in prompts:
        print(f"\n{'='*60}")
        print(f"Prompt: {prompt}")
        print(f"{'='*60}")

        messages = [{"role": "user", "content": prompt}]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
            )
        response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        print(response[:600])
        print("...")


def main():
    parser = argparse.ArgumentParser(
        description="JEBAT-Builder Fine-Tuning CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python train.py                    # Full training (3 epochs)
  python train.py --epochs 1         # Quick test run
  python train.py --test-only        # Test saved model
  python train.py --export           # Export to GGUF
  python train.py --deploy           # Deploy to .206 server
  python train.py --export --deploy  # Export and deploy
        """,
    )
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs (default: 3)")
    parser.add_argument("--batch-size", type=int, default=1, help="Per-device batch size (default: 1)")
    parser.add_argument("--test-only", action="store_true", help="Test a saved model")
    parser.add_argument("--export", action="store_true", help="Export to GGUF after training")
    parser.add_argument("--deploy", action="store_true", help="Deploy to .206 server")
    args = parser.parse_args()

    if args.test_only:
        test_model()
        return

    if not TRAINING_DATA.exists():
        print(f"ERROR: Training data not found: {TRAINING_DATA}")
        sys.exit(1)

    # Train
    adapter_dir = train(args)

    # Export
    gguf_path = None
    if args.export:
        gguf_path = export_gguf(adapter_dir)

    # Deploy
    if args.deploy:
        if gguf_path:
            deploy(gguf_path)
        else:
            # Look for existing GGUF
            existing = list(GGUF_DIR.glob("jebat-builder-*.gguf"))
            if existing:
                deploy(str(existing[0]))
            else:
                print("ERROR: No GGUF found. Run with --export first.")
                sys.exit(1)

    banner("Done!")
    if not args.export and not args.deploy:
        print(f"Model saved to: {OUTPUT_DIR}")
        print(f"\nNext steps:")
        print(f"  python train.py --test-only    # Test locally")
        print(f"  python train.py --export       # Export to GGUF")
        print(f"  python train.py --export --deploy  # Export + deploy to .206")


if __name__ == "__main__":
    main()
