"""JEBAT Vision Pipeline — image analysis and generation via vision-capable LLMs.

Provides two tools:
  - vision_analyze: Send an image (URL or local path) + question to a
    vision-capable LLM (OpenAI GPT-4o, Anthropic Claude, Google Gemini).
    Falls back to base64 encoding for local files.
  - image_generate: Generate an image from a text prompt via OpenAI DALL-E
    or a configurable gateway fallback.

Both tools use the JEBAT config system for API keys and provider selection,
with httpx for HTTP requests and proper timeout / error handling.
"""

from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path
from typing import Any

import httpx

from jebat.config import load_config
from jebat.llm.auth import get_provider_secret
from jebat.tools import register_tool

# ── Constants ──────────────────────────────────────────────────────────────

MAX_IMAGE_BYTES = 20 * 1024 * 1024      # 20 MB (matches video limit)
MAX_VIDEO_BYTES = 20 * 1024 * 1024      # 20 MB
HTTP_TIMEOUT = 60                        # seconds
VISION_MODEL_MAP = {
    "openai": "gpt-4o",
    "anthropic": "claude-3-5-sonnet-20241022",
    "google": "gemini-1.5-flash",
}
DALLE_MODEL = "dall-e-3"
ASPECT_SIZE_MAP = {
    "landscape": "1792x1024",
    "square":    "1024x1024",
    "portrait":  "1024x1792",
}

# Supported image MIME types for vision analysis
_IMAGE_MIME_TYPES = {
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".webp": "image/webp",
    ".bmp":  "image/bmp",
    ".tiff": "image/tiff",
    ".tif":  "image/tiff",
    ".svg":  "image/svg+xml",
}

_VIDEO_MIME_TYPES = {
    ".mp4":  "video/mp4",
    ".webm": "video/webm",
    ".avi":  "video/avi",
    ".mov":  "video/quicktime",
}


# ── Helpers ────────────────────────────────────────────────────────────────

def _resolve_path(image_url: str) -> Path | None:
    """If image_url looks like a local path, resolve it; else return None."""
    # Heuristic: no scheme prefix and not starting with // → treat as local
    if image_url.startswith(("http://", "https://", "ftp://", "data:")):
        return None
    p = Path(image_url).expanduser().resolve()
    return p if p.exists() else None


def _mime_from_path(p: Path) -> str:
    """Guess MIME type from file extension."""
    ext = p.suffix.lower()
    mime = _IMAGE_MIME_TYPES.get(ext) or _VIDEO_MIME_TYPES.get(ext)
    if mime:
        return mime
    guessed = mimetypes.guess_type(str(p))[0]
    return guessed or "application/octet-stream"


def _is_video_mime(mime: str) -> bool:
    return mime.startswith("video/")


def _encode_file_base64(p: Path) -> tuple[str, str]:
    """Read a local file and return (base64_data_uri, mime_type)."""
    size = p.stat().st_size
    mime = _mime_from_path(p)

    # Size validation
    if _is_video_mime(mime):
        if size > MAX_VIDEO_BYTES:
            raise ValueError(
                f"Video file too large: {size} bytes (max {MAX_VIDEO_BYTES})"
            )
    else:
        if size > MAX_IMAGE_BYTES:
            raise ValueError(
                f"Image file too large: {size} bytes (max {MAX_IMAGE_BYTES})"
            )

    raw = p.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    data_uri = f"data:{mime};base64,{b64}"
    return data_uri, mime


def _select_vision_provider() -> str:
    """Pick a configured vision-capable provider using JEBAT config + auth."""
    cfg = load_config()
    preferred = cfg.get("vision.provider", cfg.get("model.provider", "openai"))
    # Try preferred first, then fallback chain
    for candidate in (preferred, "openai", "anthropic", "google"):
        try:
            get_provider_secret(candidate)
            return candidate
        except RuntimeError:
            continue
    raise RuntimeError("No vision-capable provider is configured (openai/anthropic/google)")


# ── Vision Analyze: OpenAI ────────────────────────────────────────────────

async def _analyze_openai(
    image_content: str, mime: str, question: str, model: str,
) -> dict[str, Any]:
    """Call OpenAI chat completions with image content."""
    api_key = get_provider_secret("openai")
    # Build the content block: URL or base64 data URI
    image_block: dict[str, Any]
    if image_content.startswith(("http://", "https://")):
        image_block = {"type": "image_url", "image_url": {"url": image_content}}
    else:
        # base64 data URI
        image_block = {"type": "image_url", "image_url": {"url": image_content}}

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    image_block,
                ],
            },
        ],
        "max_tokens": 1024,
    }

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    text = data["choices"][0]["message"]["content"]
    return {
        "answer": text,
        "provider": "openai",
        "model": model,
        "usage": data.get("usage"),
    }


# ── Vision Analyze: Anthropic ─────────────────────────────────────────────

async def _analyze_anthropic(
    image_content: str, mime: str, question: str, model: str,
) -> dict[str, Any]:
    """Call Anthropic messages API with image content."""
    api_key = get_provider_secret("anthropic")

    # Anthropic requires base64 for local files; URLs are also accepted
    source: dict[str, Any]
    if image_content.startswith(("http://", "https://")):
        source = {"type": "url", "url": image_content}
    else:
        # Extract base64 from data URI
        # data:{mime};base64,{b64data}
        b64_part = image_content.split(",", 1)[1] if "," in image_content else image_content
        source = {
            "type": "base64",
            "media_type": mime,
            "data": b64_part,
        }

    payload = {
        "model": model,
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": source},
                    {"type": "text", "text": question},
                ],
            },
        ],
    }

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    text_blocks = [
        b["text"] for b in data.get("content", []) if b.get("type") == "text"
    ]
    text = "\n".join(text_blocks) if text_blocks else ""
    return {
        "answer": text,
        "provider": "anthropic",
        "model": model,
        "usage": data.get("usage"),
    }


# ── Vision Analyze: Google Gemini ──────────────────────────────────────────

async def _analyze_gemini(
    image_content: str, mime: str, question: str, model: str,
) -> dict[str, Any]:
    """Call Google Gemini generateContent with image content."""
    api_key = get_provider_secret("google")

    # Build inline_data for base64 or URI reference
    parts: list[dict[str, Any]] = [{"text": question}]
    if image_content.startswith(("http://", "https://")):
        # Gemini supports fileUri but for simplicity we fetch + encode
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as dl:
            img_resp = await dl.get(image_content)
            img_resp.raise_for_status()
            img_bytes = img_resp.content
            img_b64 = base64.b64encode(img_bytes).decode("ascii")
            guessed_mime = mimetypes.guess_type(image_content)[0] or mime
            parts.append({
                "inline_data": {"mime_type": guessed_mime, "data": img_b64},
            })
    else:
        b64_part = image_content.split(",", 1)[1] if "," in image_content else image_content
        parts.append({
            "inline_data": {"mime_type": mime, "data": b64_part},
        })

    payload = {"contents": [{"parts": parts}]}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    candidates = data.get("candidates", [])
    text = ""
    if candidates:
        parts_out = candidates[0].get("content", {}).get("parts", [])
        text = "\n".join(p.get("text", "") for p in parts_out if "text" in p)

    return {
        "answer": text,
        "provider": "google",
        "model": model,
        "usageMetadata": data.get("usageMetadata"),
    }


# ── Provider dispatch ──────────────────────────────────────────────────────

_ANALYZE_DISPATCH = {
    "openai":    _analyze_openai,
    "anthropic": _analyze_anthropic,
    "google":    _analyze_gemini,
}


# ── Tool: vision_analyze ──────────────────────────────────────────────────

@register_tool(
    "vision_analyze",
    schema={
        "type": "object",
        "properties": {
            "image_url": {
                "type": "string",
                "description": "Image URL (http/https) or local file path to analyse",
            },
            "question": {
                "type": "string",
                "description": "Question or instruction about the image",
            },
            "provider": {
                "type": "string",
                "enum": ["openai", "anthropic", "google"],
                "description": "Vision provider to use (default: auto-select from config)",
            },
            "model": {
                "type": "string",
                "description": "Specific model name (default: provider's vision model)",
            },
        },
        "required": ["image_url", "question"],
    },
    safety_tier="auto",
    timeout=60,
    max_output=100_000,
    description="Analyse an image (URL or local path) with a vision-capable LLM.",
)
async def vision_analyze(
    image_url: str,
    question: str,
    provider: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Send an image + question to a vision-capable LLM and return the answer.

    Supports OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet, and Google Gemini.
    Local files are base64-encoded before sending.  Automatically selects a
    configured provider if none is specified.
    """
    # ── Resolve image content ──────────────────────────────────────────
    local_path = _resolve_path(image_url)
    image_content: str
    mime: str

    if local_path is not None:
        # Local file → base64 data URI
        try:
            image_content, mime = _encode_file_base64(local_path)
        except ValueError as exc:
            return {"error": str(exc), "image_url": image_url}
    else:
        # Remote URL
        image_content = image_url
        mime = mimetypes.guess_type(image_url)[0] or "image/jpeg"

    # ── Select provider ────────────────────────────────────────────────
    chosen_provider = provider or _select_vision_provider()
    chosen_model = model or VISION_MODEL_MAP.get(chosen_provider, "gpt-4o")

    handler = _ANALYZE_DISPATCH.get(chosen_provider)
    if handler is None:
        return {
            "error": f"Unsupported vision provider: {chosen_provider}",
            "supported": list(_ANALYZE_DISPATCH.keys()),
        }

    # ── Call provider ──────────────────────────────────────────────────
    try:
        result = await handler(image_content, mime, question, chosen_model)
        result["image_url"] = image_url
        result["question"] = question
        return result
    except httpx.TimeoutException:
        return {
            "error": f"Vision request timed out after {HTTP_TIMEOUT}s",
            "provider": chosen_provider,
            "image_url": image_url,
        }
    except httpx.HTTPStatusError as exc:
        return {
            "error": f"Vision API error: {exc.response.status_code} — {exc.response.text[:500]}",
            "provider": chosen_provider,
            "image_url": image_url,
        }
    except RuntimeError as exc:
        return {
            "error": f"Provider auth error: {exc}",
            "provider": chosen_provider,
            "image_url": image_url,
        }
    except Exception as exc:
        return {
            "error": f"Vision analysis failed: {exc}",
            "provider": chosen_provider,
            "image_url": image_url,
        }


# ── Image Generate: OpenAI DALL-E ─────────────────────────────────────────

async def _generate_openai(
    prompt: str, size: str, model: str,
) -> dict[str, Any]:
    """Call OpenAI DALL-E image generation API."""
    api_key = get_provider_secret("openai")

    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": "standard",
        "response_format": "url",
    }

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    images = data.get("data", [])
    if not images:
        return {"error": "No images returned from DALL-E", "provider": "openai"}

    img = images[0]
    return {
        "image_url": img.get("url", ""),
        "revised_prompt": img.get("revised_prompt", prompt),
        "provider": "openai",
        "model": model,
        "size": size,
    }


# ── Image Generate: Gateway fallback ──────────────────────────────────────

async def _generate_gateway(
    prompt: str, size: str,
) -> dict[str, Any]:
    """Call a configurable image-generation gateway endpoint."""
    cfg = load_config()
    gateway_url = cfg.get("vision.generation_gateway_url")
    gateway_key = cfg.get("vision.generation_gateway_key", "")

    if not gateway_url:
        return {
            "error": "No generation gateway URL configured (set vision.generation_gateway_url in config)",
        }

    payload = {"prompt": prompt, "size": size}

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if gateway_key:
        headers["Authorization"] = f"Bearer {gateway_key}"

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.post(gateway_url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # Gateway may return different shapes; normalise
    image_url = data.get("image_url") or data.get("url") or data.get("data", {}).get("url", "")
    return {
        "image_url": image_url,
        "revised_prompt": data.get("revised_prompt", prompt),
        "provider": "gateway",
        "model": data.get("model", ""),
        "size": size,
        "raw": data,
    }


# ── Tool: image_generate ──────────────────────────────────────────────────

@register_tool(
    "image_generate",
    schema={
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Text description of the image to generate",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["landscape", "square", "portrait"],
                "default": "square",
                "description": "Desired aspect ratio of the generated image",
            },
            "provider": {
                "type": "string",
                "enum": ["openai", "gateway"],
                "description": "Generation provider (default: openai, fallback: gateway)",
            },
            "model": {
                "type": "string",
                "description": "Specific model name (default: dall-e-3 for openai)",
            },
        },
        "required": ["prompt"],
    },
    safety_tier="auto",
    timeout=90,
    max_output=50_000,
    description="Generate an image from a text prompt via DALL-E or configurable gateway.",
)
async def image_generate(
    prompt: str,
    aspect_ratio: str = "square",
    provider: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Generate an image from a text prompt.

    Uses OpenAI DALL-E by default, falling back to a configurable gateway
    if the OpenAI API key is not available or the call fails.
    """
    size = ASPECT_SIZE_MAP.get(aspect_ratio, "1024x1024")

    # Determine provider preference
    if provider is None:
        # Try OpenAI first; fall back to gateway if no key
        try:
            get_provider_secret("openai")
            provider = "openai"
        except RuntimeError:
            provider = "gateway"

    chosen_model = model or (DALLE_MODEL if provider == "openai" else "")

    # ── Try primary provider ───────────────────────────────────────────
    try:
        if provider == "openai":
            return await _generate_openai(prompt, size, chosen_model)
        else:
            return await _generate_gateway(prompt, size)
    except httpx.TimeoutException:
        # Try gateway fallback on timeout
        if provider == "openai":
            try:
                return await _generate_gateway(prompt, size)
            except Exception:
                pass
        return {
            "error": f"Image generation timed out after {HTTP_TIMEOUT}s",
            "provider": provider,
            "prompt": prompt,
        }
    except httpx.HTTPStatusError as exc:
        # Try gateway fallback on API error
        if provider == "openai":
            try:
                fallback = await _generate_gateway(prompt, size)
                fallback["fallback_reason"] = f"OpenAI error: {exc.response.status_code}"
                return fallback
            except Exception:
                pass
        return {
            "error": f"Image generation API error: {exc.response.status_code} — {exc.response.text[:500]}",
            "provider": provider,
            "prompt": prompt,
        }
    except RuntimeError as exc:
        return {
            "error": f"Provider auth error: {exc}",
            "provider": provider,
            "prompt": prompt,
        }
    except Exception as exc:
        # Last resort: try gateway if we were using openai
        if provider == "openai":
            try:
                fallback = await _generate_gateway(prompt, size)
                fallback["fallback_reason"] = f"OpenAI failed: {exc}"
                return fallback
            except Exception:
                pass
        return {
            "error": f"Image generation failed: {exc}",
            "provider": provider,
            "prompt": prompt,
        }