# wa-router/app/main.py
"""Hybrid WhatsApp Router - Meta primary, Baileys fallback."""
import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx

app = FastAPI(title="WA Hybrid Router", version="1.0.0")

META_URL = os.getenv("META_URL", "http://wa-meta:8084")
BAILEYS_URL = os.getenv("BAILEYS_URL", "http://wa-baileys:8085")
DEFAULT_BACKEND = os.getenv("DEFAULT_BACKEND", "meta")
FALLBACK_ENABLED = os.getenv("FALLBACK_ENABLED", "true").lower() == "true"

logging.basicConfig(level=os.getenv("LOG_LEVEL", "info").upper())
logger = logging.getLogger("wa-router")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "wa-router"}


@app.get("/api/v1/admin/overview")
async def overview():
    """Return status of both backends."""
    meta_ok = False
    baileys_ok = False
    
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{META_URL}/health")
            meta_ok = r.status_code == 200
    except:
        pass
    
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{BAILEYS_URL}/health")
            baileys_ok = r.status_code == 200
    except:
        pass
    
    return {
        "meta": "online" if meta_ok else "offline",
        "baileys": "online" if baileys_ok else "offline",
        "default_backend": DEFAULT_BACKEND,
        "fallback_enabled": FALLBACK_ENABLED
    }


@app.post("/api/v1/send")
async def send_message(request: Request):
    """Route message to Meta, fallback to Baileys on failure."""
    body = await request.json()
    tenant = body.get("tenant", {})
    backend = tenant.get("backend", DEFAULT_BACKEND)
    
    # Try primary backend
    if backend == "meta":
        result = await _try_meta(body)
        if result.get("success") or not FALLBACK_ENABLED:
            return result
        # Fallback to Baileys
        logger.warning("Meta failed, falling back to Baileys")
        return await _try_baileys(body)
    else:
        result = await _try_baileys(body)
        if result.get("success") or not FALLBACK_ENABLED:
            return result
        # Fallback to Meta
        logger.warning("Baileys failed, falling back to Meta")
        return await _try_meta(body)


async def _try_meta(body: dict) -> dict:
    """Send via Meta API."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{META_URL}/api/v1/send", json=body)
            result = r.json()
            result["backend"] = "meta"
            return result
    except Exception as e:
        logger.error(f"Meta error: {e}")
        return {"success": False, "backend": "meta", "error": str(e)}


async def _try_baileys(body: dict) -> dict:
    """Send via Baileys."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{BAILEYS_URL}/api/v1/send", json=body)
            result = r.json()
            result["backend"] = "baileys"
            return result
    except Exception as e:
        logger.error(f"Baileys error: {e}")
        return {"success": False, "backend": "baileys", "error": str(e)}


@app.post("/api/v1/tenants/{tenant_id}")
async def manage_tenant(tenant_id: str, request: Request):
    """Route tenant management to Meta."""
    body = await request.json()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{META_URL}/api/v1/tenants/{tenant_id}", json=body)
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/openapi.json")
async def openapi():
    return app.openapi()
