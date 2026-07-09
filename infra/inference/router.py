#!/usr/bin/env python3
"""
Jebat Inference Router
======================
A single, dependency-light FastAPI proxy that unifies local + remote
OpenAI-compatible inference backends behind ONE /v1 API:

  * llama.cpp  (llama-server, local, CPU/AVX512 + Iris Xe Vulkan)
  * Ollama     (local, GGUF registry)
  * vLLM       (remote, high-throughput GPU serving)
  * remote Ollama (remote GPU host)

Why unify? All four speak the OpenAI REST protocol. Clients (OpenWebUI,
curl, the python `openai` SDK, your own code) only ever talk to
http://127.0.0.1:8000/v1 and the router fans out to the right engine.

Routing rules
-------------
  1. Explicit backend via model suffix:  "qwen2.5:7b@llamacpp", "llama3@vllm"
  2. Friendly alias defined in config.yaml (llamacpp.models / vllm.models)
  3. First backend that already lists the model under /v1/models
  4. config default_backend

Endpoints (proxied transparently):
  GET  /v1/models
  POST /v1/chat/completions   (streaming supported)
  POST /v1/completions        (streaming supported)
  POST /v1/embeddings
  GET  /health                (router + each backend status)
  GET  /                       (this doc)
"""
from __future__ import annotations

import os
import re
import yaml
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse

CONFIG_PATH = os.environ.get("JEBAT_INFER_CONFIG",
                             os.path.expanduser("~/.local/jebat-infer/config.yaml"))

app = FastAPI(title="Jebat Inference Router")

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

CFG = load_config()

# Backend registry: name -> {base_url, api_key, enabled, kind}
BACKENDS: dict[str, dict] = {}

def rebuild_backends(cfg=None):
    global CFG, BACKENDS
    CFG = cfg or load_config()
    b: dict[str, dict] = {}
    if CFG.get("llamacpp", {}).get("enabled"):
        b["llamacpp"] = {"base_url": CFG["llamacpp"]["base_url"].rstrip("/"),
                         "api_key": "", "enabled": True, "kind": "llamacpp"}
    if CFG.get("ollama", {}).get("enabled"):
        b["ollama"] = {"base_url": CFG["ollama"]["base_url"].rstrip("/"),
                       "api_key": "", "enabled": True, "kind": "ollama"}
    if CFG.get("vllm", {}).get("enabled"):
        b["vllm"] = {"base_url": CFG["vllm"]["base_url"].rstrip("/"),
                     "api_key": CFG["vllm"].get("api_key", "EMPTY"),
                     "enabled": True, "kind": "vllm"}
    if CFG.get("remote_ollama", {}).get("enabled"):
        b["remote_ollama"] = {"base_url": CFG["remote_ollama"]["base_url"].rstrip("/"),
                              "api_key": "", "enabled": True, "kind": "ollama"}
    BACKENDS = b

rebuild_backends(CFG)

# Cache of model -> backend, refreshed on each /v1/models call.
_model_cache: dict[str, str] = {}


async def backend_models(name: str, info: dict) -> list[str]:
    """Return list of model ids a backend reports, if reachable."""
    try:
        headers = {}
        if info.get("api_key"):
            headers["Authorization"] = f"Bearer {info['api_key']}"
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{info['base_url']}/v1/models", headers=headers)
            if r.status_code == 200:
                data = r.json()
                return [m["id"] for m in data.get("data", [])]
    except Exception:
        pass
    return []


async def resolve_backend(model: str):
    """Pick a backend for `model`. Supports 'name@backend' suffix."""
    # 1. explicit suffix
    m = re.match(r"^(.*)@([a-z_]+)$", model)
    if m:
        base_model, forced = m.group(1), m.group(2)
        if forced in BACKENDS:
            return forced, base_model
        # unknown suffix -> fall through but keep original model string
    # 2. alias maps
    for bname, info in BACKENDS.items():
        aliases = CFG.get(bname, {}).get("models", {})
        if isinstance(aliases, dict) and model in aliases:
            return bname, model
    # 3. model listed by a backend
    for bname, info in BACKENDS.items():
        if model in _model_cache.get(bname, []):
            return bname, model
    # 4. default
    default = CFG.get("default_backend", "ollama")
    if default in BACKENDS:
        return default, model
    # last resort: first enabled
    if BACKENDS:
        return next(iter(BACKENDS)), model
    raise RuntimeError("No backends enabled in config.yaml")


def _strip_suffix(model: str) -> str:
    return re.sub(r"@([a-z_]+)$", "", model)


@app.get("/")
async def index():
    return {
        "service": "Jebat Inference Router",
        "backends": {k: v["base_url"] for k, v in BACKENDS.items()},
        "note": "All endpoints under /v1 are OpenAI-compatible. "
                "Force a backend with 'model@backend' (e.g. 'llama3@vllm').",
    }


@app.get("/health")
async def health():
    status = {}
    for bname, info in BACKENDS.items():
        try:
            async with httpx.AsyncClient(timeout=4.0) as c:
                r = await c.get(f"{info['base_url']}/v1/models")
                status[bname] = "up" if r.status_code == 200 else f"http_{r.status_code}"
        except Exception as e:
            status[bname] = f"down:{type(e).__name__}"
    return {"router": "up", "backends": status,
            "enabled": list(BACKENDS.keys())}


@app.get("/v1/models")
async def list_models():
    # refresh model cache
    global _model_cache
    out = []
    seen = set()
    for bname, info in BACKENDS.items():
        ids = await backend_models(bname, info)
        _model_cache[bname] = ids
        for mid in ids:
            if mid not in seen:
                seen.add(mid)
                out.append({"id": mid, "object": "model", "owned_by": bname})
    # also advertise alias names from config
    for bname, info in BACKENDS.items():
        aliases = CFG.get(bname, {}).get("models", {})
        if isinstance(aliases, dict):
            for alias in aliases:
                if alias not in seen:
                    seen.add(alias)
                    out.append({"id": alias, "object": "model", "owned_by": bname})
    return {"object": "list", "data": out}


async def _proxy(request: Request, path: str, method: str = "POST"):
    body = await request.body()
    # parse model + route
    import json
    try:
        payload = json.loads(body) if body else {}
    except Exception:
        payload = {}
    model = payload.get("model", "")
    backend_name, real_model = await resolve_backend(model)
    info = BACKENDS[backend_name]
    # rewrite model to the backend's actual id (strip @suffix)
    if real_model != model:
        payload["model"] = _strip_suffix(real_model)
        import json as _j
        body = _j.dumps(payload).encode()

    url = f"{info['base_url']}/v1/{path}"
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    if info.get("api_key"):
        headers["Authorization"] = f"Bearer {info['api_key']}"

    client = httpx.AsyncClient(timeout=None)
    req = client.build_request(method, url, content=body, headers=headers)
    try:
        resp = await client.send(req, stream=True)
    except Exception as e:
        await client.aclose()
        return JSONResponse({"error": f"backend '{backend_name}' unreachable: {e}"},
                            status_code=502)

    # Streaming passthrough (SSE for chat/completions)
    is_sse = ("text/event-stream" in resp.headers.get("content-type", "")
              or payload.get("stream"))

    async def gen():
        async for chunk in resp.aiter_raw():
            yield chunk
        await client.aclose()

    return StreamingResponse(
        gen(),
        status_code=resp.status_code,
        headers={"content-type": resp.headers.get("content-type", "application/json"),
                 "x-routed-backend": backend_name},
        media_type=resp.headers.get("content-type"),
    )


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    return await _proxy(request, "chat/completions")


@app.post("/v1/completions")
async def completions(request: Request):
    return await _proxy(request, "completions")


@app.post("/v1/embeddings")
async def embeddings(request: Request):
    return await _proxy(request, "embeddings")


if __name__ == "__main__":
    import uvicorn
    r = CFG.get("router", {})
    uvicorn.run(app, host=r.get("host", "127.0.0.1"),
                port=int(r.get("port", 8000)), log_level="info")
