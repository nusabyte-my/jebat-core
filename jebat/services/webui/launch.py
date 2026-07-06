"""JEBAT WebUI Launcher

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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from jebat.services.webui.webui_server import webui_router, _mount_static

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include WebUI router
app.include_router(webui_router)

# Mount static files for the Brutalist SPA
_mount_static(app)


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
    """Health check endpoint"""
    return {"status": "healthy", "service": "jebat-webui"}


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
    logger.info("    /webui      - Brutalist SPA shell")
    logger.info("    /chat       - AI chat interface (legacy)")
    logger.info("    /webui/api/* - REST API endpoints")
    logger.info("    /webui/ws/* - WebSocket endpoint")
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