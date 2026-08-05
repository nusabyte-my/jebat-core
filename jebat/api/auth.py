"""API key / Bearer token authentication middleware for JEBAT API.

Provides:
    APIKeyMiddleware — ASGI middleware that validates API keys on /api/* routes

Environment:
    JEBAT_API_KEY — Master API key (if unset, auth is disabled in dev mode)
    JEBAT_API_KEY_ALLOW_QUERY — If "true", also accept ?api_key= query param
"""

from __future__ import annotations

import hmac
import logging
import os
from typing import Optional, Set

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Routes that are always public (no auth required)
_PUBLIC_PATHS: Set[str] = {
    "/",
    "/health",
    "/ready",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# Route prefixes that are always public
_PUBLIC_PREFIXES: tuple[str, ...] = (
    "/docs",
    "/redoc",
    "/openapi",
)


def _constant_time_compare(a: str, b: str) -> bool:
    """Timing-safe string comparison."""
    return hmac.compare_digest(a.encode(), b.encode())


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """Extract token from 'Bearer <token>' header."""
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


class APIKeyMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that enforces API key authentication on /api/* routes.

    Behavior:
        - If JEBAT_API_KEY is not set, auth is completely disabled (dev mode)
        - Public paths (/health, /ready, /metrics, /docs, /, /openapi.json) are always allowed
        - For /api/* routes, requires either:
            - Authorization: Bearer <api_key> header
            - X-API-Key: <api_key> header
            - ?api_key=<api_key> query parameter (if JEBAT_API_KEY_ALLOW_QUERY=true)
    """

    def __init__(self, app, api_key: Optional[str] = None) -> None:
        super().__init__(app)
        self._api_key = api_key or os.getenv("JEBAT_API_KEY", "")
        self._allow_query = os.getenv("JEBAT_API_KEY_ALLOW_QUERY", "false").lower() in ("true", "1", "yes")
        environment = os.getenv("JEBAT_ENV", "development").lower()
        if environment == "production" and not self._api_key:
            raise RuntimeError("JEBAT_API_KEY must be set when JEBAT_ENV=production")
        if self._api_key:
            logger.info("API key authentication enabled for /api/* routes")
        else:
            logger.info("API key authentication DISABLED (no JEBAT_API_KEY set — dev mode)")

    def _is_public_path(self, path: str) -> bool:
        """Check if the path is always public."""
        if path in _PUBLIC_PATHS:
            return True
        for prefix in _PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True
        return False

    def _validate_key(self, provided_key: str) -> bool:
        """Validate the provided API key using constant-time comparison."""
        if not self._api_key:
            return True  # No key configured = allow all
        return _constant_time_compare(provided_key, self._api_key)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):
        path = request.url.path

        # Skip auth for public paths
        if self._is_public_path(path):
            return await call_next(request)

        # Skip auth entirely if no key is configured
        if not self._api_key:
            return await call_next(request)

        # Skip OPTIONS preflight — CORS middleware must handle these
        if request.method == "OPTIONS":
            return await call_next(request)

        # Only protect /api/* routes
        if not path.startswith("/api/"):
            return await call_next(request)

        # Try multiple auth methods
        api_key: Optional[str] = None

        # 1. Authorization: Bearer <token>
        auth_header = request.headers.get("authorization")
        api_key = _extract_bearer_token(auth_header)

        # 2. X-API-Key header
        if api_key is None:
            api_key = request.headers.get("x-api-key")

        # 3. Query parameter (if enabled)
        if api_key is None and self._allow_query:
            api_key = request.query_params.get("api_key")

        # Validate
        if api_key is None:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "unauthorized",
                    "message": "API key required. Send via Authorization: Bearer <key>, X-API-Key header, or ?api_key= query param.",
                    "docs": "/docs",
                },
                headers={"WWW-Authenticate": 'Bearer realm="jebat-api"'},
            )

        # Check env var key first, then Redis-stored keys (current + grace period)
        valid = self._validate_key(api_key)
        if not valid:
            try:
                from jebat.api.keys import validate_api_key_against_redis
                valid = await validate_api_key_against_redis(api_key)
            except Exception:
                valid = False

        if not valid:
            logger.warning(
                "Invalid API key attempt from %s for %s",
                request.client.host if request.client else "unknown",
                path,
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "forbidden",
                    "message": "Invalid API key.",
                },
            )

        return await call_next(request)
