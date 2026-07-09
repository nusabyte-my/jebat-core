#!/usr/bin/env python3
"""
Jebat Inference Router
======================
A single, dependency-light FastAPI proxy that unifies local + remote
OpenAI-compatible inference backends behind ONE /v1 API:

  * llama.cpp      (llama-server, local, CPU/AVX512 + Iris Xe Vulkan)
  * Ollama         (local, GGUF registry)
  * vLLM           (remote, high-throughput GPU serving)
  * remote Ollama  (remote GPU host)

Why unify? All four speak the OpenAI REST protocol. Clients (OpenWebUI,
curl, the python `openai` SDK, your own code) only ever talk to
http://127.0.0.1:8000/v1 and the router fans out to the right engine.

Routing rules
-------------
  1. Explicit backend via model suffix:  "qwen2.5:7b@llamacpp", "llama3@vllm"
  2. Explicit backend via ?backend= query param (takes precedence over suffix)
  3. Friendly alias defined in config.yaml (llamacpp.models / vllm.models)
  4. First backend that already lists the model under /v1/models
  5. config default_backend

Endpoints (proxied transparently):
  GET  /v1/models
  POST /v1/chat/completions   (streaming supported)
  POST /v1/completions        (streaming supported)
  POST /v1/embeddings
  GET  /health                (router + each backend status)
  GET  /healthz               (liveness probe, no backend checks)
  GET  /metrics               (Prometheus-style counters)
  POST /admin/reload          (rebuild backends from config.yaml)
  GET  /                       (this doc)
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from collections import defaultdict

import json
import yaml
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse

logging.basicConfig(
    level=os.environ.get("JEBAT_INFER_LOGLEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [router] %(message)s",
)
log = logging.getLogger("router")

CONFIG_PATH = os.environ.get(
    "JEBAT_INFER_CONFIG",
    os.path.expanduser("~/.local/jebat-infer/config.yaml"),
)

app = FastAPI(title="Jebat Inference Router")

# ── metrics ──────────────────────────────────────────────────────────
METRICS = {
    "requests_total": 0,
    "errors_total": 0,
    "backend_latency": defaultdict(float),   # backend -> cumulative seconds
    "backend_requests": defaultdict(int),     # backend -> count
}

# ── model cache (TTL) ────────────────────────────────────────────────
_model_cache: dict[str, list[str]] = {}
_model_cache_ts: float = 0.0


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


CFG = load_config()
TIMEOUT = float(CFG.get("router", {}).get("timeout", 120))
MODEL_CACHE_TTL = float(CFG.get("router", {}).get("model_cache_ttl", 30))

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
    log.info("rebuilt backends: %s", list(BACKENDS.keys()))


rebuild_backends(CFG)

# Single pooled client (connection reuse across requests).
CLIENT = httpx.AsyncClient(timeout=TIMEOUT)


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


async def resolve_backend(model: str, override: str | None = None):
    """Pick a backend for `model`. Supports 'name@backend' suffix and ?backend=."""
    if override and override in BACKENDS:
        return override, _strip_suffix(model)
    # 1. explicit suffix
    m = re.match(r"^(.*)@([a-z_]+)$", model)
    if m:
        base_model, forced = m.group(1), m.group(2)
        if forced in BACKENDS:
            return forced, base_model
    # 2. alias maps
    for bname, info in BACKENDS.items():
        aliases = CFG.get(bname, {}).get("models", {})
        if isinstance(aliases, dict) and model in aliases:
            return bname, model
    # 3. model listed by a backend
    for bname, ids in _model_cache.items():
        if model in ids:
            return bname, model
    # 4. default
    default = CFG.get("default_backend", "ollama")
    if default in BACKENDS:
        return default, model
    # 5. last resort
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
                "Force a backend with 'model@backend' or ?backend=.",
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


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


@app.get("/metrics")
async def metrics():
    lines = ["# HELP jebat_requests_total Total proxied requests",
             "# TYPE jebat_requests_total counter",
             f"jebat_requests_total {METRICS['requests_total']}",
             "# HELP jebat_errors_total Total upstream errors (502/timeout)",
             "# TYPE jebat_errors_total counter",
             f"jebat_errors_total {METRICS['errors_total']}"]
    for bname in BACKENDS:
        reqs = METRICS["backend_requests"][bname]
        lat = METRICS["backend_latency"][bname]
        lines.append(f'jebat_backend_requests{{backend="{bname}"}} {reqs}')
        lines.append(f'jebat_backend_latency_seconds{{backend="{bname}"}} {lat:.3f}')
    return Response("\n".join(lines) + "\n", media_type="text/plain")


@app.post("/admin/reload")
async def admin_reload():
    rebuild_backends()
    global _model_cache, _model_cache_ts
    _model_cache, _model_cache_ts = {}, 0.0
    return {"status": "reloaded", "backends": list(BACKENDS.keys())}


@app.get("/v1/models")
async def list_models(refresh: bool = False):
    global _model_cache, _model_cache_ts
    now = time.time()
    if refresh or (now - _model_cache_ts) > MODEL_CACHE_TTL:
        _model_cache = {}
        for bname, info in BACKENDS.items():
            _model_cache[bname] = await backend_models(bname, info)
        _model_cache_ts = now
    out, seen = [], set()
    for bname, ids in _model_cache.items():
        for mid in ids:
            if mid not in seen:
                seen.add(mid)
                out.append({"id": mid, "object": "model", "owned_by": bname})
    for bname, info in BACKENDS.items():
        aliases = CFG.get(bname, {}).get("models", {})
        if isinstance(aliases, dict):
            for alias in aliases:
                if alias not in seen:
                    seen.add(alias)
                    out.append({"id": alias, "object": "model", "owned_by": bname})
    return {"object": "list", "data": out}


async def _proxy(request: Request, path: str, method: str = "POST"):
    METRICS["requests_total"] += 1
    body = await request.body()
    try:
        payload = json.loads(body) if body else {}
    except Exception:
        payload = {}
    model = payload.get("model", "")
    override = request.query_params.get("backend")
    backend_name, real_model = await resolve_backend(model, override)
    info = BACKENDS[backend_name]
    if real_model != model:
        payload["model"] = _strip_suffix(real_model)
        body = json.dumps(payload).encode()

    url = f"{info['base_url']}/v1/{path}"
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    if info.get("api_key"):
        headers["Authorization"] = f"Bearer {info['api_key']}"

    t0 = time.time()
    req = CLIENT.build_request(method, url, content=body, headers=headers)
    try:
        resp = await CLIENT.send(req, stream=True)
    except Exception as e:
        METRICS["errors_total"] += 1
        return JSONResponse(
            {"error": f"backend '{backend_name}' unreachable: {e}"},
            status_code=502,
        )

    METRICS["backend_requests"][backend_name] += 1
    METRICS["backend_latency"][backend_name] += time.time() - t0
    log.info("%s /v1/%s -> %s (model=%s)", method, path, backend_name, real_model)

    is_sse = ("text/event-stream" in resp.headers.get("content-type", "")
              or payload.get("stream"))

    async def gen():
        try:
            async for chunk in resp.aiter_raw():
                yield chunk
        finally:
            await resp.aclose()

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
