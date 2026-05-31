# llama.cpp On VPS For JEBAT

This runbook makes `llama.cpp` the primary local chat backend for JEBAT.

## What This Changes

- JEBAT shared LLM config gains a `llamacpp` provider backed by a `llama-server` OpenAI-compatible endpoint.
- WebUI chat now uses the configured LLM provider instead of hardwiring `UltraThink`.
- `/api/v1/chat/completions` can use the configured local model as the main chat backend.
- `/webui/api/think` still keeps the existing `UltraThink` path for explicit deep reasoning.

## Reality Check

Do not plan full base-model training on a typical VPS. For most VPS deployments, use:

1. A Hugging Face instruct model that already fits your RAM or VRAM budget.
2. Optional LoRA fine-tuning off-box or on a GPU machine.
3. Merge the adapter into the base model.
4. Convert or export to `GGUF`.
5. Serve the merged `GGUF` with `llama-server`.

The official `llama.cpp` README documents:

- `llama-server` as an OpenAI-compatible HTTP server.
- direct Hugging Face loading with `-hf`.
- `GGUF` as the required runtime format.

## Install On The VPS

CPU build with OpenBLAS:

```bash
sudo apt-get update
sudo apt-get install -y git build-essential cmake ninja-build pkg-config libopenblas-dev
git clone https://github.com/ggml-org/llama.cpp.git /opt/llama.cpp
cmake -S /opt/llama.cpp -B /opt/llama.cpp/build -G Ninja -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS
cmake --build /opt/llama.cpp/build --config Release -j
```

CUDA build if the VPS has an NVIDIA GPU:

```bash
cmake -S /opt/llama.cpp -B /opt/llama.cpp/build -G Ninja -DGGML_CUDA=ON
cmake --build /opt/llama.cpp/build --config Release -j
```

## Choose A Model That Fits

Practical defaults:

- 2 to 4 vCPU, 8 GB RAM, CPU-only: 1B to 3B instruct model, `Q4_K_M`
- 4 to 8 vCPU, 16 GB RAM, CPU-only: 3B to 7B instruct model, `Q4_K_M`
- 8+ vCPU, 32 GB RAM, CPU-only: 7B to 8B instruct model, `Q4_K_M` or `Q5_K_M`
- GPU with 12 GB VRAM: 7B to 8B instruct model, offload as many layers as fit
- GPU with 24 GB VRAM: 8B to 14B instruct model, usually `Q4_K_M` or `Q5_K_M`

Good starting point for constrained VPS installs:

- `Qwen/Qwen2.5-3B-Instruct`
- `Qwen/Qwen2.5-7B-Instruct`
- `meta-llama/Llama-3.2-3B-Instruct`
- a ready-made GGUF from a trusted Hugging Face GGUF publisher if you do not want to convert yourself

## Fine-Tuning Path

Recommended:

1. Fine-tune with PEFT LoRA on the original Hugging Face model.
2. Merge the LoRA adapter into the base model.
3. Convert the merged model to `GGUF`.
4. Quantize for the VPS.

That keeps the expensive step outside the inference server and matches `llama.cpp` runtime requirements.

## Export Path

Example high-level flow:

```bash
python train_lora.py
python merge_lora.py
python /opt/llama.cpp/convert_hf_to_gguf.py /srv/models/my-merged-model --outfile /srv/models/my-model-f16.gguf
/opt/llama.cpp/build/bin/llama-quantize /srv/models/my-model-f16.gguf /srv/models/my-model-q4_k_m.gguf Q4_K_M
```

## Run llama-server

CPU-only example:

```bash
/opt/llama.cpp/build/bin/llama-server \
  --model /srv/models/my-model-q4_k_m.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --ctx-size 4096 \
  --threads 6 \
  --parallel 2
```

GPU example:

```bash
/opt/llama.cpp/build/bin/llama-server \
  --model /srv/models/my-model-q4_k_m.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --ctx-size 8192 \
  --threads 8 \
  --parallel 4 \
  --n-gpu-layers 999
```

## JEBAT Runtime Configuration

Set these on the VPS:

```bash
export JEBAT_LLM_PROVIDER=llamacpp
export JEBAT_LLM_MODEL=my-model-q4_k_m.gguf
export LLAMA_CPP_HOST=http://127.0.0.1:8080
export JEBAT_LLM_FALLBACKS=ollama,local
```

Or update `jebat/config/config.yaml`:

```yaml
llm:
  provider: llamacpp
  model: my-model-q4_k_m.gguf
  llamacpp_host: "http://127.0.0.1:8080"
  fallback_providers:
    - ollama
    - local
```

## Tuning Checklist

- Start with `Q4_K_M`, not `Q8`, unless the VPS has abundant RAM.
- Keep `--ctx-size` conservative. Bigger context increases KV-cache memory sharply.
- Set `--threads` close to physical cores, not hyperthreads, then benchmark.
- Use `--parallel` only if you truly need concurrent users. It trades memory for concurrency.
- On GPU, increase `--n-gpu-layers` until VRAM pressure starts causing instability.
- Run `llama-bench` on the actual VPS before locking in thread and context settings.

## systemd Service Template

```ini
[Unit]
Description=llama.cpp server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/llama.cpp
ExecStart=/opt/llama.cpp/build/bin/llama-server --model /srv/models/my-model-q4_k_m.gguf --host 127.0.0.1 --port 8080 --ctx-size 4096 --threads 6 --parallel 2
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

## What I Still Need From The VPS

To optimize this correctly, collect:

- CPU model
- vCPU count
- total RAM
- whether a GPU exists, and if so its VRAM
- target concurrent users
- acceptable latency target

Without those numbers, model size and runtime flags are still educated defaults rather than final tuning.
