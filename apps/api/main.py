"""
Unified JEBAT API entry point.

Usage:
    python -m apps.api.main api
    python -m apps.api.main webui
    python -m apps.api.main all
"""

from __future__ import annotations

import argparse
import logging
from typing import Literal

import uvicorn
from fastapi import FastAPI

from .config import settings

logger = logging.getLogger(__name__)


def create_app(mode: Literal["api", "webui", "all"] = "all") -> FastAPI:
    """Create a FastAPI app for API, WebUI, or both."""
    if mode == "api":
        from .services.api.jebat_api import app as api_app
        return api_app

    if mode == "webui":
        from .services.webui.launch import app as webui_app
        return webui_app

    app = FastAPI(
        title="JEBAT Unified Server",
        description="Unified API + WebUI server for JEBAT",
        version=settings.version,
    )

    from .services.api.jebat_api import app as api_app
    from .services.webui.launch import app as webui_app

    # Mount complete sub-apps to preserve each app's middleware and routes.
    app.mount("/api-server", api_app)
    app.mount("/", webui_app)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run JEBAT API/WebUI")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=("api", "webui", "all"),
        default="all",
        help="Server mode to run (default: all)",
    )
    parser.add_argument("--host", default=None, help="Bind host")
    parser.add_argument("--port", type=int, default=None, help="Bind port")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn reload")
    args = parser.parse_args()

    host = args.host or (settings.api.host if args.mode == "api" else settings.webui.host)
    port = args.port or (settings.api.port if args.mode == "api" else settings.webui.port)

    logger.info("Starting JEBAT %s server on %s:%s", args.mode, host, port)
    uvicorn.run(
        create_app(args.mode),
        host=host,
        port=port,
        reload=args.reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
