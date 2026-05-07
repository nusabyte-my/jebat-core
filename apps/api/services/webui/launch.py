"""
JEBAT WebUI Launcher

Launch the immersive web interface for JEBAT.

Usage:
    python -m jebat.services.webui.launch [--host 0.0.0.0] [--port 8787]
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

try:
    from ..auth import (
        COOKIE_NAME,
        apply_security_headers,
        current_auth_context,
        ensure_request_token,
        get_cors_settings,
        log_security_event,
    )
    from .webui_server import webui_router
except ModuleNotFoundError:
    from apps.api.services.auth import (
        COOKIE_NAME,
        apply_security_headers,
        current_auth_context,
        ensure_request_token,
        get_cors_settings,
        log_security_event,
    )
    from apps.api.services.webui.webui_server import webui_router

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="JEBAT WebUI",
    description="Immersive Web Interface for JEBAT AI Assistant",
    version="1.0.0",
)

cors_origins, cors_allow_credentials = get_cors_settings()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include WebUI router
app.include_router(webui_router)

# Also mount at root for convenience
app.include_router(webui_router, prefix="")


@app.middleware("http")
async def protect_webui_routes(request, call_next):
    """Require an operator token for all WebUI routes and persist it as a cookie for browser use."""
    if request.method == "OPTIONS" or not request.url.path.startswith("/webui"):
        response = await call_next(request)
        return apply_security_headers(response)

    try:
        token = ensure_request_token(request, allow_query=True)
    except Exception as exc:  # HTTPException, but kept broad to avoid leaking internals in the browser path
        status_code = getattr(exc, "status_code", 500)
        detail = getattr(exc, "detail", "operator token required")
        if request.url.path.startswith("/webui/api/"):
            return apply_security_headers(JSONResponse({"detail": detail}, status_code=status_code))
        return apply_security_headers(HTMLResponse(
            (
                "<main style=\"font-family: ui-monospace, SFMono-Regular, Menlo, monospace; "
                "background:#020617; color:#e2e8f0; min-height:100vh; padding:48px;\">"
                "<h1 style=\"margin:0 0 16px; color:#10b981;\">Operator Token Required</h1>"
                "<p style=\"max-width:720px; line-height:1.7;\">Set <code>JEBAT_API_TOKEN</code> or "
                "<code>JEBAT_GATEWAY_TOKEN</code> on the server, then open this console with "
                "<code>?token=YOUR_TOKEN</code> once so the browser can establish an authenticated session.</p>"
                "</main>"
            ),
            status_code=status_code,
        ))

    response = await call_next(request)
    query_token = request.query_params.get("token", "").strip()
    if token and query_token and request.cookies.get(COOKIE_NAME) != token:
        context = current_auth_context(request)
        response.set_cookie(
            COOKIE_NAME,
            token,
            httponly=True,
            samesite="strict",
            secure=request.url.scheme == "https",
            max_age=60 * 60 * 12,
            path="/webui",
        )
        log_security_event(
            action="webui.session.bootstrap",
            actor=context,
            resource="webui.session",
            details={"path": request.url.path},
        )
    return apply_security_headers(response)


@app.get("/", include_in_schema=False)
async def root_redirect(request):
    """Redirect the bare host to the WebUI entrypoint."""
    token = request.query_params.get("token", "").strip()
    url = "/webui/"
    if token:
        url = f"{url}?token={token}"
    return RedirectResponse(url=url, status_code=307)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "jebat-webui"}


@app.get("/webui/api/session")
async def webui_session(request: Request):
    """Return the authenticated operator session context for the WebUI."""
    context = current_auth_context(request)
    return {
        "authenticated": True,
        "token_id": context.token_id,
        "subject": context.subject,
        "source": context.source,
        "roles": list(context.roles),
        "permissions": list(context.permissions),
        "expires_at": context.expires_at,
        "has_cookie": bool(request.cookies.get(COOKIE_NAME)),
    }


@app.post("/webui/api/logout")
async def webui_logout(request: Request):
    """Clear the WebUI operator session cookie."""
    context = current_auth_context(request)
    response = JSONResponse({"ok": True, "logged_out": True})
    response.delete_cookie(
        COOKIE_NAME,
        path="/webui",
        httponly=True,
        samesite="strict",
        secure=request.url.scheme == "https",
    )
    log_security_event(
        action="webui.session.logout",
        actor=context,
        resource="webui.session",
        details={"path": request.url.path},
    )
    return apply_security_headers(response)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="JEBAT WebUI Server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8787,
        help="Port to bind to (default: 8787)",
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("  JEBAT WebUI Server")
    logger.info("=" * 70)
    logger.info(f"  Starting server on http://{args.host}:{args.port}")
    logger.info("")
    logger.info("  Available routes:")
    logger.info("    /           - Main landing page")
    logger.info("    /chat       - AI chat interface")
    logger.info("    /dashboard  - System dashboard")
    logger.info("    /memory     - Memory explorer")
    logger.info("    /api/*      - REST API endpoints")
    logger.info("    /ws/{user}  - WebSocket endpoint")
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
