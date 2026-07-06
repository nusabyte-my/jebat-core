"""JEBAT WebUI Launcher — Enterprise Edition

Launch the immersive web interface for JEBAT.
Includes rate limiting, CORS tightening, error pages, and health checks.

Usage:
    python -m jebat.services.webui.launch [--host 0.0.0.0] [--port 8787]
"""

import argparse
import logging
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from jebat.services.webui.webui_server import webui_router, _mount_static, STATIC_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Rate Limiting Middleware
# ═══════════════════════════════════════════════════════════════
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 120    # requests per window (generous for local dev)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, window=RATE_LIMIT_WINDOW, max_requests=RATE_LIMIT_MAX):
        super().__init__(app)
        self.window = window
        self.max_requests = max_requests
        self.hits = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for static files and health checks
        path = request.url.path
        if path.startswith("/webui/static/") or path == "/health" or path == "/favicon.ico":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        key = f"{client_ip}:{path.rsplit('/', 1)[0] if '/' in path else '/'}"

        # Clean old entries
        self.hits[key] = [t for t in self.hits[key] if now - t < self.window]

        if len(self.hits[key]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded. Try again later.", "retry_after": self.window},
                headers={"Retry-After": str(self.window)},
            )

        self.hits[key].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.max_requests - len(self.hits[key])))
        return response


# ═══════════════════════════════════════════════════════════════
# Error Pages
# ═══════════════════════════════════════════════════════════════
ERROR_PAGE = """<!DOCTYPE html>
<html><head><title>{code} — JEBAT</title>
<link rel="stylesheet" href="/webui/static/css/stealth.css" />
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600&display=swap" rel="stylesheet"/>
</head><body style="display:flex;align-items:center;justify-content:center;min-height:100vh;background:#030303;color:#e5e5e5;font-family:Space Grotesk,sans-serif;text-align:center">
<div>
  <div style="font-size:72px;margin-bottom:16px">{icon}</div>
  <div style="font-size:48px;font-weight:700;color:#00f0ff;margin-bottom:8px">{code}</div>
  <div style="font-size:18px;color:#a3a3a3;margin-bottom:24px">{title}</div>
  <div style="font-size:14px;color:#525252;margin-bottom:32px">{detail}</div>
  <a href="/webui/" style="display:inline-block;padding:12px 24px;background:#00f0ff;color:#030303;border-radius:8px;font-weight:600;text-decoration:none">← Back to Dashboard</a>
</div></body></html>"""


# ═══════════════════════════════════════════════════════════════
# Create App
# ═══════════════════════════════════════════════════════════════
app = FastAPI(
    title="JEBAT WebUI",
    description="Sovereign AI Platform — Enterprise Web Interface",
    version="6.1.0",
)

# CORS — tightened for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8787", "http://127.0.0.1:8787", "http://0.0.0.0:8787"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# Include WebUI router
app.include_router(webui_router)
_mount_static(app)


@app.get("/favicon.ico")
@app.get("/favicon.svg")
async def favicon():
    """Serve favicon."""
    fav = STATIC_DIR / "favicon.svg"
    if fav.exists():
        return FileResponse(fav, media_type="image/svg+xml")
    return JSONResponse(status_code=404, content={"error": "favicon not found"})


LANDING_DIR = Path(__file__).resolve().parent.parent.parent.parent
_static_mounted = False


def _mount_landing_assets(app: FastAPI):
    global _static_mounted
    if _static_mounted:
        return
    for fname in ("JebatLogo-transparent.png", "robots.txt", "sitemap.xml"):
        fpath = LANDING_DIR / fname
        if fpath.exists():
            @app.get(f"/{fname}", include_in_schema=False)
            async def serve_asset(path=fpath):
                return FileResponse(path, media_type="application/octet-stream")
    _static_mounted = True


_mount_landing_assets(app)


@app.get("/", include_in_schema=False)
async def landing_page():
    index = LANDING_DIR / "index.html"
    if index.exists():
        return FileResponse(index, media_type="text/html")
    return RedirectResponse(url="/webui/", status_code=307)


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "service": "jebat-webui",
        "version": "6.1.0",
        "timestamp": time.time(),
        "features": ["rate-limiting", "cors", "error-pages", "activity-log"],
    }


# ═══════════════════════════════════════════════════════════════
# Custom Error Handlers
# ═══════════════════════════════════════════════════════════════
@app.exception_handler(404)
async def not_found(request: Request, exc):
    path = request.url.path
    # JSON for API paths, styled HTML for everything else
    if path.startswith("/webui/api") or path.startswith("/api"):
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return HTMLResponse(
        ERROR_PAGE.format(code=404, icon="🔍", title="Page Not Found", detail=f"The page <code>{path}</code> doesn't exist."),
        status_code=404,
    )


@app.exception_handler(500)
async def server_error(request: Request, exc):
    return HTMLResponse(ERROR_PAGE.format(code=500, icon="💥", title="Internal Server Error", detail="Something went wrong. Check the server logs."), status_code=500)


@app.exception_handler(429)
async def rate_limited(request: Request, exc):
    return HTMLResponse(ERROR_PAGE.format(code=429, icon="⏳", title="Rate Limited", detail="Too many requests. Please slow down."), status_code=429)


def main():
    parser = argparse.ArgumentParser(description="JEBAT WebUI Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8787, help="Port to bind to")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("  JEBAT WebUI Server — Enterprise Edition")
    logger.info("=" * 70)
    logger.info(f"  Starting on http://{args.host}:{args.port}")
    logger.info("")
    logger.info("  Routes:")
    logger.info("    /webui       — Stealth-Dark Tactical SPA")
    logger.info("    /health      — Health check endpoint")
    logger.info("    /webui/api/* — REST API")
    logger.info("    /webui/ws/*  — WebSocket")
    logger.info("")
    logger.info("  Features:")
    logger.info("    ✓ Rate limiting (120 req/min per IP)")
    logger.info("    ✓ CORS tightened (localhost only)")
    logger.info("    ✓ Error pages (404/429/500)")
    logger.info("    ✓ Health check endpoint")
    logger.info("=" * 70)

    uvicorn.run(
        "jebat.services.webui.launch:app",
        host=args.host,
        port=args.port,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
