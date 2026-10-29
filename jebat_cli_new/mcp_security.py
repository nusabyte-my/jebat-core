"""MCP catalog integrity, bounded schema validation, and token binding."""
from __future__ import annotations

import base64
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from jsonschema import Draft202012Validator

MAX_SCHEMA_BYTES = 256_000
MAX_SCHEMA_DEPTH = 32
MAX_REFS = 64


class MCPSecurityError(RuntimeError):
    pass


def catalog_fingerprint(tools: Iterable[Dict[str, Any]]) -> str:
    normalized = [
        {"name": t.get("name"), "description": t.get("description"), "inputSchema": t.get("inputSchema"), "outputSchema": t.get("outputSchema")}
        for t in tools if isinstance(t, dict)
    ]
    normalized.sort(key=lambda t: str(t["name"]))
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def integrity_path(config_file: Path) -> Path:
    return config_file.parent / "mcp-integrity.json"


def check_catalog_integrity(server: str, tools: list, config_file: Path) -> Dict[str, Any]:
    current = catalog_fingerprint(tools)
    path = integrity_path(config_file)
    records = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    previous = records.get(server, {}).get("sha256")
    records[server] = {"sha256": current, "updated_at": time.time()}
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    if previous and previous != current:
        raise MCPSecurityError(
            f"MCP tool catalog for {server!r} changed after review. "
            f"Expected SHA-256 {previous}, got {current}. Inspect drift before calling tools."
        )
    return {"server": server, "sha256": current, "status": "pinned" if previous else "recorded"}


def _check_schema(schema: Any, depth: int = 0) -> None:
    if depth > MAX_SCHEMA_DEPTH:
        raise MCPSecurityError("MCP schema exceeds nesting limit")
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key == "$ref" and not isinstance(value, str):
                raise MCPSecurityError("MCP $ref must be a string")
            _check_schema(value, depth + 1)
    elif isinstance(schema, list):
        for value in schema:
            _check_schema(value, depth + 1)


def validate_structured_content(content: Any, schema: Optional[Dict[str, Any]]) -> None:
    if not schema:
        return
    if len(json.dumps(schema, ensure_ascii=False)) > MAX_SCHEMA_BYTES:
        raise MCPSecurityError("MCP output schema exceeds size limit")
    _check_schema(schema)
    if json.dumps(schema).count("$ref") > MAX_REFS:
        raise MCPSecurityError("MCP output schema exceeds reference limit")
    try:
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(content))
    except Exception as exc:
        raise MCPSecurityError(f"invalid MCP output schema: {exc}") from exc
    if errors:
        raise MCPSecurityError(f"MCP structuredContent violates outputSchema: {errors[0].message}")


def _b64_json(segment: str) -> Dict[str, Any]:
    try:
        return json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
    except Exception as exc:
        raise MCPSecurityError("invalid JWT encoding") from exc


def validate_bearer_binding(headers: Dict[str, str], *, issuer: Optional[str], audience: Optional[str]) -> None:
    if not issuer and not audience:
        return
    authorization = next((v for k, v in headers.items() if k.lower() == "authorization"), "")
    if not authorization.lower().startswith("bearer "):
        raise MCPSecurityError("OAuth-bound MCP server requires a Bearer token")
    token = authorization.split(" ", 1)[1]
    parts = token.split(".")
    if len(parts) != 3:
        raise MCPSecurityError("OAuth-bound MCP server requires a JWT for issuer/audience validation")
    claims = _b64_json(parts[1])
    if issuer and claims.get("iss") != issuer:
        raise MCPSecurityError("MCP Bearer token issuer does not match configured authorization server")
    if audience:
        actual = claims.get("aud", [])
        actual = [actual] if isinstance(actual, str) else actual
        if audience not in actual:
            raise MCPSecurityError("MCP Bearer token is not intended for this resource server")
