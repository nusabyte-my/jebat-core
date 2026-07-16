"""Request logging middleware for JEBAT API.

Records method, path, status code, latency, and client IP for all /api/* requests.
Stores recent requests in Redis (capped list) and aggregate stats (counters).

Provides:
    RequestLoggingMiddleware — ASGI middleware for /api/* request logging
    get_request_stats — helper to retrieve stats from Redis for /ready

Redis keys:
    jebat:logs:recent      — LPUSH list of recent request JSON objects (capped at 500)
    jebat:logs:count        — Hash of path -> count
    jebat:logs:status:{code} — Counter for each HTTP status code
    jebat:logs:total        — Total request counter
    jebat:logs:errors       — Total error (4xx+5xx) counter
    jebat:logs:latency_sum  — Sum of all latencies (for avg calc)
"""

from __future__ import annotations

import csv
import inspect
import io
import json
import logging
import time
from typing import Any, Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

_REDIS_KEY_PREFIX = "jebat:logs:"
_MAX_RECENT = 500  # keep last N requests in the list


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that logs /api/* request details to Redis.

    For non-/api/* paths, the request passes through without logging.
    If Redis is unavailable, logging silently degrades (no errors raised).
    """

    def __init__(self, app, redis_url: Optional[str] = None) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path

        # Only log /api/* routes (skip /api/logs to avoid self-logging loop)
        if not path.startswith("/api/") or path.startswith("/api/logs"):
            return await call_next(request)

        # Capture timing
        start = time.time()
        client_ip = request.client.host if request.client else "unknown"
        method = request.method

        # Process request
        try:
            response = await call_next(request)
        except Exception:
            # Re-raise but still try to log the error
            latency_ms = round((time.time() - start) * 1000, 2)
            await self._log_request(method, path, 500, latency_ms, client_ip)
            raise

        latency_ms = round((time.time() - start) * 1000, 2)
        status_code = response.status_code

        # Log asynchronously (fire-and-forget, don't block response)
        await self._log_request(method, path, status_code, latency_ms, client_ip)

        return response

    async def _log_request(
        self, method: str, path: str, status_code: int, latency_ms: float, client_ip: str
    ) -> None:
        """Write request data to Redis. Silently skips if Redis is unavailable."""
        try:
            from jebat.database.connection_manager import get_redis_manager
            rm = get_redis_manager()
            client = rm.client
            if client is None:
                return

            entry = json.dumps({
                "ts": time.time(),
                "method": method,
                "path": path,
                "status": status_code,
                "latency_ms": latency_ms,
                "ip": client_ip,
            })

            pipe = client.pipeline()
            if inspect.isawaitable(pipe):
                pipe = await pipe

            async def queue(command, *args):
                result = command(*args)
                if inspect.isawaitable(result):
                    await result

            # 1. Push to recent list (capped at _MAX_RECENT)
            await queue(pipe.lpush, f"{_REDIS_KEY_PREFIX}recent", entry)
            await queue(pipe.ltrim, f"{_REDIS_KEY_PREFIX}recent", 0, _MAX_RECENT - 1)

            # 2. Increment total counter
            await queue(pipe.incr, f"{_REDIS_KEY_PREFIX}total")

            # 3. Increment status code counter
            await queue(pipe.incr, f"{_REDIS_KEY_PREFIX}status:{status_code}")

            # 4. Increment path counter
            await queue(pipe.hincrby, f"{_REDIS_KEY_PREFIX}count", path, 1)

            # 5. Accumulate latency
            await queue(pipe.incrbyfloat, f"{_REDIS_KEY_PREFIX}latency_sum", latency_ms)

            # 6. Increment error counter if 4xx or 5xx
            if status_code >= 400:
                await queue(pipe.incr, f"{_REDIS_KEY_PREFIX}errors")

            result = pipe.execute()
            if inspect.isawaitable(result):
                await result
        except Exception as exc:
            # Never let logging failures affect the request
            logger.debug("Request logging failed: %s", exc)


async def get_request_stats() -> dict[str, Any]:
    """Retrieve aggregated request stats from Redis.

    Returns a dict suitable for inclusion in the /ready endpoint.
    Falls back to empty stats if Redis is unavailable.
    """
    try:
        from jebat.database.connection_manager import get_redis_manager
        rm = get_redis_manager()
        client = rm.client
        if client is None:
            return {
            "total_requests": 0,
            "total_errors": 0,
            "error_rate_pct": 0.0,
            "avg_latency_ms": 0.0,
            "status_codes": {},
            "top_paths": {},
            "recent_window": _MAX_RECENT,
            "storage": "memory-only (Redis unavailable)",
        }

        total_raw = await client.get(f"{_REDIS_KEY_PREFIX}total")
        errors_raw = await client.get(f"{_REDIS_KEY_PREFIX}errors")
        latency_raw = await client.get(f"{_REDIS_KEY_PREFIX}latency_sum")
        top_paths_raw = await client.hgetall(f"{_REDIS_KEY_PREFIX}count")

        total = int(total_raw) if total_raw else 0
        errors = int(errors_raw) if errors_raw else 0
        latency_sum = float(latency_raw) if latency_raw else 0.0

        # Top 5 paths by count
        if top_paths_raw:
            sorted_paths = sorted(top_paths_raw.items(), key=lambda x: int(x[1]), reverse=True)[:5]
            top_paths = {p: int(c) for p, c in sorted_paths}
        else:
            top_paths = {}

        # Status code breakdown
        status_codes = {}
        for code in ["200", "201", "400", "401", "403", "404", "500", "502", "503"]:
            val = await client.get(f"{_REDIS_KEY_PREFIX}status:{code}")
            if val:
                status_codes[code] = int(val)

        return {
            "total_requests": total,
            "total_errors": errors,
            "error_rate_pct": round((errors / total * 100), 2) if total > 0 else 0.0,
            "avg_latency_ms": round(latency_sum / total, 2) if total > 0 else 0.0,
            "status_codes": status_codes,
            "top_paths": top_paths,
            "recent_window": _MAX_RECENT,
        }
    except Exception as exc:
        return {
            "total_requests": 0,
            "total_errors": 0,
            "error_rate_pct": 0.0,
            "avg_latency_ms": 0.0,
            "status_codes": {},
            "top_paths": {},
            "recent_window": _MAX_RECENT,
            "storage": "error",
            "error": str(exc),
        }


async def clear_all_logs() -> dict[str, Any]:
    """Flush all request log data from Redis.

    Deletes:
        - jebat:logs:recent       (list)
        - jebat:logs:count        (hash)
        - jebat:logs:total        (counter)
        - jebat:logs:errors       (counter)
        - jebat:logs:latency_sum  (float counter)
        - jebat:logs:status:*     (per-status counters, scanned)

    Returns a summary of what was cleared.
    """
    try:
        from jebat.database.connection_manager import get_redis_manager
        rm = get_redis_manager()
        client = rm.client
        if client is None:
            return {"cleared": False, "reason": "Redis unavailable"}

        # Collect all keys to delete
        keys_to_delete: list[str] = []

        # 1. Scan for status counters: jebat:logs:status:*
        cursor = 0
        while True:
            cursor, found = await client.scan(
                cursor=cursor,
                match=f"{_REDIS_KEY_PREFIX}status:*",
                count=100,
            )
            keys_to_delete.extend(found)
            if cursor == 0:
                break

        # 2. Add the known fixed keys
        keys_to_delete.extend([
            f"{_REDIS_KEY_PREFIX}recent",
            f"{_REDIS_KEY_PREFIX}count",
            f"{_REDIS_KEY_PREFIX}total",
            f"{_REDIS_KEY_PREFIX}errors",
            f"{_REDIS_KEY_PREFIX}latency_sum",
        ])

        if not keys_to_delete:
            return {
                "cleared": True,
                "keys_deleted": 0,
                "message": "No log data to clear.",
            }

        deleted = await client.delete(*keys_to_delete)

        return {
            "cleared": True,
            "keys_deleted": deleted,
            "message": "All request logs and counters flushed.",
        }
    except Exception as exc:
        return {
            "cleared": False,
            "error": str(exc),
        }


async def export_logs(format: str = "json") -> tuple[bytes, str, str]:
    """Export all logged requests from Redis as CSV or JSON.

    Args:
        format: "json" or "csv".

    Returns:
        Tuple of (content_bytes, media_type, filename).
    """
    try:
        from jebat.database.connection_manager import get_redis_manager
        rm = get_redis_manager()
        client = rm.client
        if client is None:
            return (json.dumps({"entries": [], "error": "Redis unavailable"}).encode(), "application/json", "logs.json")

        # Fetch ALL entries from the recent list
        raw_entries = await client.lrange(f"{_REDIS_KEY_PREFIX}recent", 0, -1)

        entries: list[dict[str, Any]] = []
        for raw in raw_entries:
            try:
                entry = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue

            # Convert timestamp to ISO string for readability
            ts = entry.get("ts")
            if isinstance(ts, (int, float)):
                entry["ts_iso"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))

            entries.append(entry)

        # Sort chronologically (oldest first) — LPUSH puts newest first
        entries.sort(key=lambda e: e.get("ts", 0))

        if format == "csv":
            buf = io.StringIO()
            fieldnames = ["ts_iso", "method", "path", "status", "latency_ms", "ip"]
            writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for entry in entries:
                writer.writerow(entry)
            content = buf.getvalue().encode("utf-8")
            return (content, "text/csv; charset=utf-8", "jebat-request-logs.csv")

        # Default: JSON
        payload = {"entries": entries, "total": len(entries)}
        content = json.dumps(payload, indent=2).encode("utf-8")
        return (content, "application/json", "jebat-request-logs.json")

    except Exception as exc:
        error_payload = {"entries": [], "error": str(exc)}
        return (json.dumps(error_payload).encode(), "application/json", "logs.json")


async def get_recent_logs(
    limit: int = 50,
    status: Optional[int] = None,
    path_filter: Optional[str] = None,
    method: Optional[str] = None,
) -> dict[str, Any]:
    """Retrieve the last N logged requests from Redis, with optional filters.

    Args:
        limit: Max entries to return (capped at 500).
        status: Filter by HTTP status code (e.g. 404, 500).
        path_filter: Substring match on request path.
        method: Filter by HTTP method (GET, POST, etc.).

    Returns:
        Dict with ``entries`` list, ``total`` count, and applied ``filters``.
    """
    limit = min(max(limit, 1), _MAX_RECENT)

    try:
        from jebat.database.connection_manager import get_redis_manager
        rm = get_redis_manager()
        client = rm.client
        if client is None:
            return {
                "entries": [],
                "total": 0,
                "filters": {},
                "storage": "unavailable",
            }

        # LRANGE gets the most recent entries (LPUSH puts newest first)
        raw_entries = await client.lrange(f"{_REDIS_KEY_PREFIX}recent", 0, limit * 3)
        # Over-fetch by 3x to account for filters

        entries: list[dict[str, Any]] = []
        for raw in raw_entries:
            if len(entries) >= limit:
                break
            try:
                entry = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue

            # Apply filters
            if status is not None and entry.get("status") != status:
                continue
            if path_filter and path_filter not in entry.get("path", ""):
                continue
            if method and entry.get("method", "").upper() != method.upper():
                continue

            # Convert timestamp to ISO string for readability
            ts = entry.get("ts")
            if isinstance(ts, (int, float)):
                entry["ts_iso"] = time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)
                )

            entries.append(entry)

        filters_applied: dict[str, Any] = {}
        if status is not None:
            filters_applied["status"] = status
        if path_filter:
            filters_applied["path_contains"] = path_filter
        if method:
            filters_applied["method"] = method.upper()

        return {
            "entries": entries,
            "total": len(entries),
            "filters": filters_applied,
            "window": _MAX_RECENT,
        }

    except Exception as exc:
        return {
            "entries": [],
            "total": 0,
            "filters": {},
            "error": str(exc),
        }
