JEBAT INFERENCE — unified local + remote LLM stack
===================================================

WHY
---
vLLM, llama.cpp, and Ollama each do one thing best. This stack combines
them behind a SINGLE OpenAI-compatible endpoint so you never rewire your
clients:

  * Ollama        -> one-command model management, huge GGUF catalog,
                     auto-quant. Best "daily driver" on this laptop.
  * llama.cpp     -> fastest CPU/AVX-512 + Iris Xe path, long context,
                     embeddings, speculative decoding, offline file mode.
  * vLLM (remote) -> high-throughput GPU serving for many concurrent users,
                     FP8/AWQ/GPTQ. Run on a GPU box, point the router at it.
  * remote Ollama -> offload a big model to a GPU host, same protocol.

All four speak the OpenAI REST API. The router (router.py) proxies
/v1/chat/completions, /v1/completions, /v1/embeddings, /v1/models to the
right backend.

HARDWARE TARGET (this laptop)
-----------------------------
  CPU  : Intel i7-1185G7 (4C/8T, AVX-512)   -> llama.cpp CPU path shines
  RAM  : 15 GB                              -> up to ~7B Q4 / 3B Q6
  GPU  : Intel Iris Xe (iGPU, no VRAM)       -> Vulkan helps; CPU is rock-solid
  Disk : 411 GB free
  NOTE : CachyOS boots into a volatile overlay; only /home persists.
         Everything here installs to ~/.local (user space, no sudo).

LAYOUT
------
  ~/.local/jebat-infer/
    config.yaml     # backends + routing rules (edit me)
    router.py       # the proxy
    install.sh      # build llama.cpp + venv deps
    start.sh        # start ollama + llama.cpp + router
    stop.sh         # stop router + llama.cpp (--all also stops ollama)
    venv/           # python venv (router + llama.cpp binaries)
    llama.cpp/      # source build

QUICK START
-----------
1. Build (one time, ~few min):
     bash ~/.local/jebat-infer/install.sh

2. Pull a model into Ollama:
     ollama pull qwen2.5:3b        # or qwen2.5:7b for stronger answers
     ollama pull nomic-embed-text  # embeddings

3. Start the stack:
     bash ~/.local/jebat-infer/start.sh

4. Talk to it through the unified endpoint:
     curl http://127.0.0.1:8000/v1/chat/completions \
       -H 'Content-Type: application/json' \
       -d '{"model":"qwen2.5:3b","messages":[{"role":"user","content":"hi"}]}'

   Python SDK:
     from openai import OpenAI
     c = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="x")
     c.chat.completions.create(model="qwen2.5:3b",
        messages=[{"role":"user","content":"explain AVX-512"}])

ROUTING
-------
  * Force a backend with a suffix:  "qwen2.5:3b@ollama",
    "qwen2.5:7b@llamacpp", "llama3@vllm", "mixtral@remote_ollama".
  * Friendly aliases live in config.yaml (llamacpp.models / vllm.models).
  * Health:  curl http://127.0.0.1:8000/health
  * Model list: curl http://127.0.0.1:8000/v1/models

ADDING A LOCAL llama.cpp MODEL
------------------------------
1. Download a GGUF (e.g. from HF bartowski/*-GGGUF) into ~/.cache/llama/.
2. Edit config.yaml under `llamacpp.models`:
     "qwen2.5-7b":
       path: /home/humm1ngb1rd/.cache/llama/qwen2.5-7b-instruct-q4_k_m.gguf
       ctx: 16384
3. start.sh will auto-launch llama-server on :8081 with that model.
   GPU offload to Iris Xe: set llamacpp.launch.gpu: "0" (Vulkan).

ADDING A REMOTE vLLM / OLLAMA
-----------------------------
Edit config.yaml:
  vllm.enabled: true
  vllm.base_url: http://<gpu-box>:8000
  vllm.api_key: "..."        # if required
Then the router routes "model@vllm" to it. No code changes needed.

WHICH ENGINE FOR WHAT (on this machine)
---------------------------------------
  Task                          Use
  ----------------------------  --------------------------------
  Daily chat, quick experiments Ollama (qwen2.5:7b / llama3.1:8b)
  Max single-thread CPU speed,   llama.cpp (AVX-512 + Vulkan iGPU)
  long context, embeddings
  Many concurrent users /        Remote vLLM (GPU box)
  high throughput, FP8/AWQ
  Big model you can't fit here   Remote Ollama or remote vLLM

OPENWEBUI
--------
OpenWebUI gives you one chat UI for every backend, routed automatically.
Installed into its own venv (python3.11, since open-webui needs <3.13).
Managed by systemd --user (see AUTOSTART below) or manually:
  bash ~/.local/jebat-infer/openwebui.sh
Opens on http://127.0.0.1:8080 with OPENAI_API_BASE_URL=http://127.0.0.1:8000/v1

  First run pulls the all-MiniLM-L6-v2 embedding model (for RAG/search) —
  takes a minute. Then:
    1. Open http://127.0.0.1:8080
    2. Workspace (top-left) -> Models -> click "+"
    3. Type a model ID exactly as the router exposes it, e.g.:
         qwen2.5:3b          (Ollama, local)
         qwen2.5-3b-cpp      (llama.cpp, local)
         qwen2.5:14b@remote_ollama   (Jebat remote box, when reachable)
    4. Save. The model now shows in the chat dropdown and is served
       through the router -> the right engine.

AUTOSTART (systemd --user)
--------------------------
The whole stack runs as user services (no sudo; survives shell disconnects;
starts on login). Units in ~/.config/systemd/user/:
  jebat-ollama.service      ollama serve
  jebat-llamacpp.service    llama-server (qwen2.5-3b Q4_K_M, :8081)
  jebat-router.service      router.py (:8000)
  jebat-openwebui.service   open-webui serve (:8080, -> router)
  jebat-infer.target        aggregate; enabled in default.target (autostart)

  Manage:
    systemctl --user start jebat-infer.target     # bring up all 4
    systemctl --user stop   jebat-infer.target     # stop all 4
    systemctl --user restart jebat-router.service   # just the router
    systemctl --user status jebat-infer.target
    journalctl --user -u jebat-router.service -f    # logs
  Disable autostart:  systemctl --user disable jebat-infer.target
  (Linger is off, so services stop at logout and start at next login —
   normal laptop behavior. Enable `loginctl enable-linger $USER` only if you
   want them to keep running with no active session.)

REMOTE BACKENDS (already wired)
-------------------------------
  remote_ollama:
    The Jebat central Ollama box (72.62.255.206:11434) is configured as
    `remote_ollama` in config.yaml. It serves bigger models (qwen2.5:14b,
    hermes3, phi3, llama3.1:8b) that won't fit this 15GB laptop.
    - It is reachable from the VPS network / tunnel, NOT from local Wi-Fi,
      so from this laptop it shows "down" in /health — the router keeps
      working and the other backends stay up.
    - To use it locally, reach it via the VPS (ssh -L 11434:72.62.255.206:11434
      user@vps) or a tunnel, then `model@remote_ollama` routes there.
    - The remote-routing code path is verified (stand-in test passed).

  vllm (remote):
    For high-throughput GPU serving. Set vllm.enabled:true and vllm.base_url
    to your GPU box's OpenAI endpoint, then route with `model@vllm`.

FORCING A BACKEND
-----------------
  Suffix any model name:  name@ollama  name@llamacpp  name@vllm  name@remote_ollama
  (verified working through the router)

HEALTH / DEBUG
--------------
  curl http://127.0.0.1:8000/health     # router + each backend status
  curl http://127.0.0.1:8000/v1/models  # merged model list w/ owning backend
  curl http://127.0.0.1:8080/health     # OpenWebUI status
