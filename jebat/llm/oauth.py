"""Provider OAuth — device-flow credentials for providers that support OAuth.

Currently implements Google (Gemini API) via the OAuth 2.0 Device
Authorization Grant, which works from headless/remote deployments (the
WebUI host polls Google; the user just visits a URL and types a code).

Credential precedence for Google: ``GOOGLE_API_KEY``/``GEMINI_API_KEY``
(env or provider_auth store) wins; OAuth is the keyless fallback.

Requires a Google OAuth client of type *TVs and Limited Input devices*
created in the user's own Google Cloud project (client id + secret).
Nothing here ships a shared client — that would be someone else's quota.

OpenAI has no public OAuth for API access (ChatGPT sign-in is first-party
only), so it stays API-key. Anthropic likewise.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"
# Gemini API scope: view models and use them to generate content.
DEFAULT_SCOPES: tuple[str, ...] = ("https://www.googleapis.com/auth/generative-language.retriever",)
REFRESH_MARGIN_SECONDS = 120


# ── Token store ────────────────────────────────────────────────────────────


def _store_path() -> Path:
    override = os.getenv("JEBAT_OAUTH_STORE", "").strip()
    if override:
        return Path(override)
    return Path.home() / ".jebat" / "oauth_tokens.json"


def _load_store() -> dict[str, dict[str, Any]]:
    path = _store_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_store(store: dict[str, dict[str, Any]]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, indent=2), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _entry(provider: str) -> dict[str, Any] | None:
    entry = _load_store().get(provider)
    return entry if isinstance(entry, dict) else None


# ── HTTP helpers (monkeypatch points for tests) ────────────────────────────


def _post_sync(url: str, data: dict[str, Any]) -> dict[str, Any]:
    import httpx

    with httpx.Client(timeout=30) as client:
        response = client.post(url, data=data)
    try:
        return response.json()
    except Exception:
        return {"error": f"http_{response.status_code}"}


async def _post_async(url: str, data: dict[str, Any]) -> dict[str, Any]:
    import httpx

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, data=data)
    try:
        return response.json()
    except Exception:
        return {"error": f"http_{response.status_code}"}


# ── Google device flow ─────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class GoogleOAuthStatus:
    connected: bool
    expires_at: float = 0.0
    scopes: tuple[str, ...] = ()
    error: str = ""


def google_oauth_status() -> GoogleOAuthStatus:
    entry = _entry("google")
    if not entry or not entry.get("refresh_token"):
        return GoogleOAuthStatus(connected=False, error="not connected")
    return GoogleOAuthStatus(
        connected=True,
        expires_at=float(entry.get("expires_at") or 0.0),
        scopes=tuple(entry.get("scopes") or ()),
    )


async def google_device_start(
    client_id: str,
    client_secret: str = "",
    scopes: tuple[str, ...] = DEFAULT_SCOPES,
) -> dict[str, Any]:
    """Begin the device flow. Returns user_code / verification_url / device_code."""
    if not client_id.strip():
        raise ValueError("client_id is required")
    payload = {
        "client_id": client_id.strip(),
        "scope": " ".join(scopes),
    }
    if client_secret.strip():
        payload["client_secret"] = client_secret.strip()
    data = await _post_async(DEVICE_CODE_URL, payload)
    if data.get("error"):
        raise RuntimeError(str(data.get("error_description") or data["error"]))
    verification_url = data.get("verification_url") or data.get("verification_uri")
    for key, value in (
        ("device_code", data.get("device_code")),
        ("user_code", data.get("user_code")),
        ("verification_url", verification_url),
        ("expires_in", data.get("expires_in")),
    ):
        if not value:
            raise RuntimeError(f"device authorization response missing {key}")
    return {
        "device_code": data["device_code"],
        "user_code": data["user_code"],
        "verification_url": verification_url,
        "expires_in": int(data.get("expires_in") or 1800),
        "interval": int(data.get("interval") or 5),
        "scopes": list(scopes),
    }


async def google_device_poll(
    device_code: str,
    client_id: str,
    client_secret: str = "",
) -> dict[str, Any]:
    """Poll once for device-flow completion.

    Returns ``{"status": "pending"|"slow_down"|"ok"|"expired"|"denied"|"error", ...}``.
    On ``ok`` the refresh/access tokens are persisted to the OAuth store.
    """
    payload = {
        "client_id": client_id.strip(),
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    }
    if client_secret.strip():
        payload["client_secret"] = client_secret.strip()
    data = await _post_async(TOKEN_URL, payload)
    error = str(data.get("error") or "")
    if error == "authorization_pending":
        return {"status": "pending"}
    if error == "slow_down":
        return {"status": "slow_down"}
    if error == "expired_token":
        return {"status": "expired"}
    if error == "access_denied":
        return {"status": "denied"}
    if error:
        return {"status": "error", "error": str(data.get("error_description") or error)}
    access_token = str(data.get("access_token") or "")
    refresh_token = str(data.get("refresh_token") or "")
    if not access_token:
        return {"status": "error", "error": "token response missing access_token"}

    expires_in = float(data.get("expires_in") or 3600)
    store = _load_store()
    previous = store.get("google") or {}
    store["google"] = {
        "client_id": client_id.strip(),
        "client_secret": client_secret.strip(),
        "scopes": data.get("scope", "").split() or list(previous.get("scopes") or DEFAULT_SCOPES),
        "access_token": access_token,
        "refresh_token": refresh_token or str(previous.get("refresh_token") or ""),
        "expires_at": time.time() + expires_in,
        "connected_at": time.time(),
    }
    _save_store(store)
    return {"status": "ok", "expires_at": store["google"]["expires_at"]}


def google_oauth_disconnect() -> bool:
    store = _load_store()
    existed = "google" in store
    store.pop("google", None)
    _save_store(store)
    return existed


def get_google_access_token() -> str | None:
    """Return a valid Google access token, refreshing when needed.

    Sync by design: called from ``build_provider`` which is sync. Returns
    ``None`` when Google OAuth is not connected (callers then fall back to
    API-key auth or fail with a clear error).
    """
    entry = _entry("google")
    if not entry:
        return None
    access_token = str(entry.get("access_token") or "")
    expires_at = float(entry.get("expires_at") or 0.0)
    if access_token and time.time() < expires_at - REFRESH_MARGIN_SECONDS:
        return access_token

    refresh_token = str(entry.get("refresh_token") or "")
    if not refresh_token:
        return None
    payload: dict[str, Any] = {
        "client_id": entry.get("client_id", ""),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    if entry.get("client_secret"):
        payload["client_secret"] = entry["client_secret"]
    data = _post_sync(TOKEN_URL, payload)
    if data.get("error"):
        # invalid_grant: the refresh token was revoked/expired — keep the
        # entry but mark it so the UI can prompt a reconnect.
        store = _load_store()
        current = store.get("google")
        if isinstance(current, dict):
            current["last_error"] = str(data.get("error_description") or data["error"])
            current["expires_at"] = 0.0
            _save_store(store)
        return None

    new_access = str(data.get("access_token") or "")
    if not new_access:
        return None
    store = _load_store()
    current = store.get("google")
    if isinstance(current, dict):
        current["access_token"] = new_access
        current["expires_at"] = time.time() + float(data.get("expires_in") or 3600)
        current.pop("last_error", None)
        _save_store(store)
    return new_access
