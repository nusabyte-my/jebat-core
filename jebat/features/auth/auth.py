"""JEBAT Auth & Provider Management — credential storage and provider health.

Supports three storage backends (in priority order):
  1. OS keyring (via `keyring` library)
  2. Environment file (~/.jebat/secrets.env)
  3. Encrypted file (~/.jebat/auth.enc, XOR with derived key)

Supported providers: openai, anthropic, google, openrouter, groq, together,
                     deepseek, mistral, cohere, custom
"""

from __future__ import annotations

import hashlib
import os
import platform
from pathlib import Path
from typing import Any

from jebat.tools import register_tool

from .custom_providers import CUSTOM_PROVIDERS, CUSTOM_PROVIDER_IDS, CustomProvider

# ── Constants ────────────────────────────────────────────────────────────────

SUPPORTED_PROVIDERS = [
    "openai",
    "anthropic",
    "google",
    "openrouter",
    "groq",
    "together",
    "deepseek",
    "mistral",
    "cohere",
    "custom",
    *CUSTOM_PROVIDER_IDS,
]

JEBAT_DIR = Path.home() / ".jebat"
SECRETS_ENV = JEBAT_DIR / "secrets.env"
AUTH_ENC = JEBAT_DIR / "auth.enc"

KEYRING_SERVICE = "jebat-cli"


# ── Custom Providers ─────────────────────────────────────────────────────────
# Helpers `is_custom_provider` / `get_custom_provider` live in custom_providers
# (pure module, no import cycle) and are re-exported here for convenience.

from .custom_providers import get_custom_provider, is_custom_provider  # noqa: E402,F401


def _resolve_custom_base_url(provider: CustomProvider) -> str:
    return os.getenv(provider.base_url_env, provider.default_base_url).strip()


def fetch_provider_models(
    provider: str,
    api_key: str | None = None,
    base_url: str | None = None,
) -> list[str]:
    """Fetch the model catalog from a custom (OpenAI-compatible) gateway.

    Returns a list of model ids. Returns an empty list on any failure so the
    caller can fall back to a free-text prompt or the provider defaults.
    """
    cp = get_custom_provider(provider)
    if cp is None:
        return []
    url = (base_url or _resolve_custom_base_url(cp)).rstrip("/")
    if not url:
        return []
    path = cp.models_path if cp.models_path.startswith("/") else f"/{cp.models_path}"
    full = f"{url}{path}"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    try:
        import requests

        resp = requests.get(full, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        return [str(m["id"]) for m in data["data"] if isinstance(m, dict) and m.get("id")]
    if isinstance(data, list):
        return [str(m.get("id") or m) for m in data if m]
    return []


def select_provider_model(
    provider: str,
    api_key: str | None = None,
    base_url: str | None = None,
    current: str | None = None,
) -> str:
    """Interactively list and select a model for a custom provider.

    Fetches the live catalog when reachable; otherwise falls back to the
    provider's static defaults and finally to free-text input.
    """
    cp = get_custom_provider(provider)
    models = fetch_provider_models(provider, api_key, base_url)
    if not models and cp is not None:
        models = list(cp.default_models)
    if not models:
        prompt = "Enter model id"
        if current:
            prompt += f" [{current}]"
        prompt += ": "
        return input(prompt).strip() or (current or "")
    print("\nAvailable models:")
    for i, m in enumerate(models, 1):
        marker = " (current)" if m == current else ""
        print(f"  {i:>3}) {m}{marker}")
    choice = input(f"Select model [1]{' (' + current + ')' if current else ''}: ").strip()
    if not choice:
        return current or models[0]
    if choice.isdigit() and 1 <= int(choice) <= len(models):
        return models[int(choice) - 1]
    return choice


# ── Backend Detection ────────────────────────────────────────────────────────

def _keyring_available() -> bool:
    """Check if the OS keyring library is available and functional."""
    try:
        import keyring as kr
        # Attempt a benign read to verify backend works
        kr.get_password(KEYRING_SERVICE, "__jebat_probe__")
        return True
    except Exception:
        return False


def _derive_xor_key() -> bytes:
    """Derive a repeating XOR key from JEBAT_AUTH_SECRET env or hostname hash."""
    secret = os.environ.get("JEBAT_AUTH_SECRET")
    if not secret:
        secret = platform.node() or "jebat-default-host"
    return hashlib.sha256(secret.encode()).digest()


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    """XOR data with a repeating key."""
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))


# ── Low-Level Backend Operations ────────────────────────────────────────────

def _store_keyring(provider: str, key_type: str, value: str) -> None:
    import keyring as kr
    entry_name = f"{provider}:{key_type}"
    kr.set_password(KEYRING_SERVICE, entry_name, value)


def _retrieve_keyring(provider: str, key_type: str) -> str | None:
    import keyring as kr
    entry_name = f"{provider}:{key_type}"
    return kr.get_password(KEYRING_SERVICE, entry_name)


def _delete_keyring(provider: str, key_type: str) -> bool:
    import keyring as kr
    entry_name = f"{provider}:{key_type}"
    try:
        kr.delete_password(KEYRING_SERVICE, entry_name)
        return True
    except Exception:
        return False


def _read_env_file() -> dict[str, str]:
    """Read all entries from secrets.env into a dict."""
    entries: dict[str, str] = {}
    if not SECRETS_ENV.exists():
        return entries
    for line in SECRETS_ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            entries[k.strip()] = v.strip()
    return entries


def _write_env_file(entries: dict[str, str]) -> None:
    """Write all entries back to secrets.env."""
    JEBAT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}={v}" for k, v in sorted(entries.items())]
    SECRETS_ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _store_env(provider: str, key_type: str, value: str) -> None:
    entries = _read_env_file()
    entry_name = f"{provider.upper()}_{key_type.upper()}"
    entries[entry_name] = value
    _write_env_file(entries)


def _retrieve_env(provider: str, key_type: str) -> str | None:
    entries = _read_env_file()
    entry_name = f"{provider.upper()}_{key_type.upper()}"
    return entries.get(entry_name)


def _delete_env(provider: str, key_type: str) -> bool:
    entries = _read_env_file()
    entry_name = f"{provider.upper()}_{key_type.upper()}"
    if entry_name in entries:
        del entries[entry_name]
        _write_env_file(entries)
        return True
    return False


def _read_enc_file() -> dict[str, str]:
    """Read and decrypt auth.enc into a dict."""
    entries: dict[str, str] = {}
    if not AUTH_ENC.exists():
        return entries
    raw = AUTH_ENC.read_bytes()
    key = _derive_xor_key()
    decrypted = _xor_bytes(raw, key).decode("utf-8", errors="replace")
    for line in decrypted.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            entries[k.strip()] = v.strip()
    return entries


def _write_enc_file(entries: dict[str, str]) -> None:
    """Encrypt and write entries to auth.enc."""
    JEBAT_DIR.mkdir(parents=True, exist_ok=True)
    plaintext = "\n".join(f"{k}={v}" for k, v in sorted(entries.items())) + "\n"
    key = _derive_xor_key()
    encrypted = _xor_bytes(plaintext.encode("utf-8"), key)
    AUTH_ENC.write_bytes(encrypted)


def _store_enc(provider: str, key_type: str, value: str) -> None:
    entries = _read_enc_file()
    entry_name = f"{provider.upper()}_{key_type.upper()}"
    entries[entry_name] = value
    _write_enc_file(entries)


def _retrieve_enc(provider: str, key_type: str) -> str | None:
    entries = _read_enc_file()
    entry_name = f"{provider.upper()}_{key_type.upper()}"
    return entries.get(entry_name)


def _delete_enc(provider: str, key_type: str) -> bool:
    entries = _read_enc_file()
    entry_name = f"{provider.upper()}_{key_type.upper()}"
    if entry_name in entries:
        del entries[entry_name]
        _write_enc_file(entries)
        return True
    return False


# ── Unified Backend Dispatcher ───────────────────────────────────────────────

def _active_backend() -> str:
    """Return the name of the active storage backend."""
    if _keyring_available():
        return "keyring"
    if SECRETS_ENV.exists() or not AUTH_ENC.exists():
        return "env"
    return "enc"


def _store(provider: str, key_type: str, value: str) -> str:
    """Store a credential using the best available backend. Returns backend name."""
    if _keyring_available():
        _store_keyring(provider, key_type, value)
        return "keyring"
    # Try env file; fallback to enc
    try:
        _store_env(provider, key_type, value)
        return "env"
    except Exception:
        _store_enc(provider, key_type, value)
        return "enc"


def _retrieve(provider: str, key_type: str) -> str | None:
    """Retrieve a credential from any backend (cascading lookup)."""
    # Try keyring first
    if _keyring_available():
        val = _retrieve_keyring(provider, key_type)
        if val is not None:
            return val
    # Try env file
    val = _retrieve_env(provider, key_type)
    if val is not None:
        return val
    # Try encrypted file
    val = _retrieve_enc(provider, key_type)
    return val


def _delete(provider: str, key_type: str) -> bool:
    """Delete a credential from all backends. Returns True if found in any."""
    deleted = False
    if _keyring_available():
        deleted |= _delete_keyring(provider, key_type)
    deleted |= _delete_env(provider, key_type)
    deleted |= _delete_enc(provider, key_type)
    return deleted


# ── Masking Helper ───────────────────────────────────────────────────────────

def _mask(value: str) -> str:
    """Mask a secret: show first 4 + '...' + last 4 chars."""
    if len(value) <= 8:
        return value[:2] + "..." + value[-2:] if len(value) > 4 else "****"
    return value[:4] + "..." + value[-4:]


# ── Provider Test Endpoints ─────────────────────────────────────────────────

async def _test_provider_api(provider: str, api_key: str) -> dict[str, Any]:
    """Attempt a lightweight API call to verify the key works."""
    import aiohttp

    endpoints: dict[str, tuple[str, dict[str, str]]] = {
        "openai": (
            "https://api.openai.com/v1/models",
            {"Authorization": f"Bearer {api_key}"},
        ),
        "anthropic": (
            "https://api.anthropic.com/v1/messages",
            {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        ),
        "google": (
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
            {},
        ),
        "openrouter": (
            "https://openrouter.ai/api/v1/models",
            {"Authorization": f"Bearer {api_key}"},
        ),
        "groq": (
            "https://api.groq.com/openai/v1/models",
            {"Authorization": f"Bearer {api_key}"},
        ),
        "together": (
            "https://api.together.xyz/v1/models",
            {"Authorization": f"Bearer {api_key}"},
        ),
        "deepseek": (
            "https://api.deepseek.com/v1/models",
            {"Authorization": f"Bearer {api_key}"},
        ),
        "mistral": (
            "https://api.mistral.ai/v1/models",
            {"Authorization": f"Bearer {api_key}"},
        ),
        "cohere": (
            "https://api.cohere.com/v1/models",
            {"Authorization": f"Bearer {api_key}"},
        ),
    }

    if provider == "custom":
        return {"valid": True, "note": "Custom provider — no built-in test endpoint."}

    if provider not in endpoints:
        return {"valid": False, "error": f"Unknown provider: {provider}"}

    url, headers = endpoints[provider]

    # Anthropic requires a POST body for messages endpoint; use models instead
    if provider == "anthropic":
        url = "https://api.anthropic.com/v1/models"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as resp:
                status = resp.status
                if status == 200:
                    return {"valid": True, "status_code": status}
                body = await resp.text()
                return {
                    "valid": False,
                    "status_code": status,
                    "error": body[:300],
                }
    except ImportError:
        # aiohttp not installed — fall back to urllib
        return await _test_provider_api_urllib(provider, url, headers)
    except Exception as exc:
        return {"valid": False, "error": str(exc)}


async def _test_provider_api_urllib(
    provider: str, url: str, headers: dict[str, str]
) -> dict[str, Any]:
    """Fallback test using only stdlib urllib."""
    import urllib.request
    import urllib.error

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"valid": True, "status_code": resp.status}
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        return {"valid": False, "status_code": e.code, "error": body}
    except Exception as exc:
        return {"valid": False, "error": str(exc)}


# ── Internal API (no @register_tool) ────────────────────────────────────────

def get_provider_secret(provider: str, key_type: str = "API_KEY") -> str | None:
    """Retrieve a credential for a provider from any backend.

    This is an internal helper — not exposed as a CLI tool.
    Usage: secret = get_provider_secret("openai")
    """
    return _retrieve(provider, key_type)


# ── Tool: auth_add ───────────────────────────────────────────────────────────

@register_tool(
    "auth_add",
    schema={
        "type": "object",
        "properties": {
            "provider": {
                "type": "string",
                "description": f"Provider name. One of: {', '.join(SUPPORTED_PROVIDERS)}",
            },
            "key_type": {
                "type": "string",
                "description": "Credential type (e.g. API_KEY, SECRET_KEY). Default: API_KEY",
            },
            "key_value": {
                "type": "string",
                "description": "The secret value to store.",
            },
        },
        "required": ["provider", "key_value"],
    },
    safety_tier="confirm",
    timeout=15,
    description="Store a credential for an AI provider.",
)
async def auth_add(
    provider: str, key_value: str, key_type: str = "API_KEY"
) -> dict[str, Any]:
    """Store a credential for the given provider."""
    provider = provider.lower().strip()
    key_type = key_type.upper().strip()

    if provider not in SUPPORTED_PROVIDERS:
        return {
            "error": f"Unsupported provider '{provider}'. Supported: {', '.join(SUPPORTED_PROVIDERS)}"
        }

    if not key_value.strip():
        return {"error": "key_value must not be empty."}

    backend = _store(provider, key_type, key_value.strip())
    return {
        "status": "stored",
        "provider": provider,
        "key_type": key_type,
        "backend": backend,
        "masked": _mask(key_value.strip()),
    }


# ── Tool: auth_list ──────────────────────────────────────────────────────────

@register_tool(
    "auth_list",
    schema={"type": "object", "properties": {}},
    safety_tier="auto",
    timeout=10,
    description="List all stored provider credentials (masked).",
)
async def auth_list() -> dict[str, Any]:
    """Show providers with keys masked (first 4 ... last 4)."""
    results: list[dict[str, str]] = []

    # Gather from all backends
    seen: set[str] = set()

    # Keyring
    if _keyring_available():
        try:
            import keyring as kr
            # keyring doesn't support listing; probe known providers
            for prov in SUPPORTED_PROVIDERS:
                for kt in ("API_KEY", "SECRET_KEY"):
                    val = _retrieve_keyring(prov, kt)
                    if val is not None:
                        tag = f"{prov}:{kt}"
                        if tag not in seen:
                            seen.add(tag)
                            results.append({
                                "provider": prov,
                                "key_type": kt,
                                "masked": _mask(val),
                                "backend": "keyring",
                            })
        except Exception:
            pass

    # Env file
    env_entries = _read_env_file()
    for k, v in env_entries.items():
        parts = k.rsplit("_", 1)
        if len(parts) == 2:
            prov = parts[0].lower()
            kt = parts[1]
            tag = f"{prov}:{kt}"
            if tag not in seen:
                seen.add(tag)
                results.append({
                    "provider": prov,
                    "key_type": kt,
                    "masked": _mask(v),
                    "backend": "env",
                })

    # Encrypted file
    enc_entries = _read_enc_file()
    for k, v in enc_entries.items():
        parts = k.rsplit("_", 1)
        if len(parts) == 2:
            prov = parts[0].lower()
            kt = parts[1]
            tag = f"{prov}:{kt}"
            if tag not in seen:
                seen.add(tag)
                results.append({
                    "provider": prov,
                    "key_type": kt,
                    "masked": _mask(v),
                    "backend": "enc",
                })

    return {
        "count": len(results),
        "credentials": results,
        "active_backend": _active_backend(),
    }


# ── Tool: auth_test ──────────────────────────────────────────────────────────

@register_tool(
    "auth_test",
    schema={
        "type": "object",
        "properties": {
            "provider": {
                "type": "string",
                "description": f"Provider to test. One of: {', '.join(SUPPORTED_PROVIDERS)}",
            },
        },
        "required": ["provider"],
    },
    safety_tier="auto",
    timeout=15,
    description="Test a provider's stored credential by making a real API call.",
)
async def auth_test(provider: str) -> dict[str, Any]:
    """Attempt a real API call to verify the stored key works."""
    provider = provider.lower().strip()

    if provider not in SUPPORTED_PROVIDERS:
        return {
            "error": f"Unsupported provider '{provider}'. Supported: {', '.join(SUPPORTED_PROVIDERS)}"
        }

    api_key = _retrieve(provider, "API_KEY")
    if api_key is None:
        return {
            "provider": provider,
            "valid": False,
            "error": "No API_KEY found for this provider. Use auth_add first.",
        }

    if is_custom_provider(provider):
        cp = get_custom_provider(provider)
        # Base URL for custom providers lives in ~/.jebat/secrets.env; make sure
        # it is loaded into os.environ before resolving (cross-process safety).
        try:
            from jebat.llm.auth import _ensure_secrets_loaded

            _ensure_secrets_loaded()
        except Exception:
            pass
        base_url = _resolve_custom_base_url(cp)
        models = fetch_provider_models(provider, api_key, base_url)
        if models:
            return {
                "provider": provider,
                "valid": True,
                "models_available": len(models),
                "message": f"{len(models)} models available from {base_url or 'default endpoint'}",
                "masked_key": _mask(api_key),
            }
        return {
            "provider": provider,
            "valid": False,
            "error": "Could not fetch model catalog (check base URL / API key).",
            "masked_key": _mask(api_key),
        }

    result = await _test_provider_api(provider, api_key)
    result["provider"] = provider
    result["masked_key"] = _mask(api_key)
    return result


# ── Tool: auth_remove ────────────────────────────────────────────────────────

@register_tool(
    "auth_remove",
    schema={
        "type": "object",
        "properties": {
            "provider": {
                "type": "string",
                "description": f"Provider to remove. One of: {', '.join(SUPPORTED_PROVIDERS)}",
            },
            "key_type": {
                "type": "string",
                "description": "Credential type to remove. Default: API_KEY",
            },
        },
        "required": ["provider"],
    },
    safety_tier="confirm",
    timeout=10,
    description="Remove a stored credential for a provider.",
)
async def auth_remove(provider: str, key_type: str = "API_KEY") -> dict[str, Any]:
    """Remove stored credential from all backends."""
    provider = provider.lower().strip()
    key_type = key_type.upper().strip()

    if provider not in SUPPORTED_PROVIDERS:
        return {
            "error": f"Unsupported provider '{provider}'. Supported: {', '.join(SUPPORTED_PROVIDERS)}"
        }

    deleted = _delete(provider, key_type)
    if deleted:
        return {"status": "removed", "provider": provider, "key_type": key_type}
    return {
        "status": "not_found",
        "provider": provider,
        "key_type": key_type,
        "message": "No credential found for this provider/key_type.",
    }


# ── Tool: auth_status ────────────────────────────────────────────────────────

@register_tool(
    "auth_status",
    schema={"type": "object", "properties": {}},
    safety_tier="auto",
    timeout=30,
    description="Show all configured providers with health status.",
)
async def auth_status() -> dict[str, Any]:
    """Show all configured providers with health status."""
    list_result = await auth_list()
    creds = list_result.get("credentials", [])

    providers_seen: dict[str, dict[str, Any]] = {}
    for cred in creds:
        prov = cred["provider"]
        if prov not in providers_seen:
            providers_seen[prov] = {
                "provider": prov,
                "configured": True,
                "key_types": [],
                "backends": [],
                "health": "unknown",
            }
        providers_seen[prov]["key_types"].append(cred["key_type"])
        if cred["backend"] not in providers_seen[prov]["backends"]:
            providers_seen[prov]["backends"].append(cred["backend"])

    # Test each provider that has an API_KEY
    for prov, info in providers_seen.items():
        if "API_KEY" in info["key_types"]:
            api_key = _retrieve(prov, "API_KEY")
            if api_key:
                test_result = await _test_provider_api(prov, api_key)
                info["health"] = "healthy" if test_result.get("valid") else "unhealthy"
                if not test_result.get("valid"):
                    info["error"] = test_result.get("error", "unknown error")
        else:
            info["health"] = "no_api_key"

    # Include supported but unconfigured providers
    for prov in SUPPORTED_PROVIDERS:
        if prov not in providers_seen:
            providers_seen[prov] = {
                "provider": prov,
                "configured": False,
                "key_types": [],
                "backends": [],
                "health": "not_configured",
            }

    all_providers = sorted(providers_seen.values(), key=lambda x: x["provider"])

    return {
        "active_backend": list_result.get("active_backend", "unknown"),
        "total_configured": sum(1 for p in all_providers if p["configured"]),
        "total_supported": len(SUPPORTED_PROVIDERS),
        "providers": all_providers,
    }
