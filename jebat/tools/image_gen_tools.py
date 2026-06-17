"""JEBAT Image Generation Tool.

Generate high-quality images from text prompts using the configured image
provider (OpenAI DALL-E by default, configurable via config.yaml).
"""

from __future__ import annotations

import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from jebat.config import load_config
from jebat.tools import register_tool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_OUTPUT_DIR = Path(os.environ.get("JEBAT_IMAGE_DIR", Path.home() / ".jebat" / "images"))


def _ensure_output_dir() -> Path:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return _OUTPUT_DIR


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------

async def image_generate(
    prompt: str,
    aspect_ratio: str = "landscape",
) -> dict[str, Any]:
    """Generate an image from a text prompt.

    Args:
        prompt: Text description of the desired image. Be detailed — include
            subject, style, colors, lighting, composition.
        aspect_ratio: "landscape" (16:9), "square" (1:1), or "portrait" (9:16).

    Returns:
        {"status": "ok"/"error", "path": "absolute path to saved image", "prompt": "..."}
    """
    config = load_config()
    provider = str(config.get("image.provider", "openai")).lower()

    # Map aspect ratio to dimensions
    size_map = {
        "landscape": "1792x1024",
        "square": "1024x1024",
        "portrait": "1024x1792",
    }
    size = size_map.get(aspect_ratio, "1024x1024")

    if provider == "openai":
        result = await _generate_openai(prompt, size, config)
    elif provider == "stability":
        result = await _generate_stability(prompt, aspect_ratio, config)
    elif provider == "local":
        result = await _generate_local_fallback(prompt)
    else:
        return {"status": "error", "error": f"Unsupported image provider: {provider}"}

    return result


async def _generate_openai(prompt: str, size: str, config: dict[str, Any]) -> dict[str, Any]:
    """Generate via OpenAI DALL-E 3."""
    from .auth_deps import _get_image_api_key

    api_key = _get_image_api_key(config, "openai") or os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"status": "error", "error": "No OpenAI API key found"}

    try:
        import openai

        client = openai.AsyncOpenAI(api_key=api_key)
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt[:4000],
            n=1,
            size=size,
            quality="standard",
            response_format="b64_json",
        )
    except ImportError:
        # Fallback to direct HTTP
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "dall-e-3",
                    "prompt": prompt[:4000],
                    "n": 1,
                    "size": size,
                    "response_format": "b64_json",
                },
            )
            resp.raise_for_status()
            response = resp.json()

        b64_data = response["data"][0]["b64_json"]
    else:
        b64_data = response.data[0].b64_json

    # Save to disk
    out_dir = _ensure_output_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"dalle_{timestamp}.png"
    fpath = out_dir / fname
    fpath.write_bytes(base64.b64decode(b64_data))

    return {"status": "ok", "path": str(fpath), "prompt": prompt, "provider": "openai"}


async def _generate_stability(prompt: str, aspect_ratio: str, config: dict[str, Any]) -> dict[str, Any]:
    """Generate via Stability AI."""
    from .auth_deps import _get_image_api_key

    api_key = _get_image_api_key(config, "stability") or os.environ.get("STABILITY_API_KEY", "")
    if not api_key:
        return {"status": "error", "error": "No Stability API key found"}

    ar_map = {"landscape": "16:9", "square": "1:1", "portrait": "9:16"}
    ar = ar_map.get(aspect_ratio, "1:1")

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"none": ""},
            data={"prompt": prompt[:10000], "aspect_ratio": ar, "output_format": "png"},
        )
        resp.raise_for_status()

    out_dir = _ensure_output_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"stability_{timestamp}.png"
    fpath = out_dir / fname
    fpath.write_bytes(resp.content)

    return {"status": "ok", "path": str(fpath), "prompt": prompt, "provider": "stability"}


async def _generate_local_fallback(prompt: str) -> dict[str, Any]:
    """No-op fallback when no real provider is configured."""
    out_dir = _ensure_output_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"placeholder_{timestamp}.txt"
    fpath = out_dir / fname
    fpath.write_text(f"Image prompt (not generated — no provider configured):\n\n{prompt}")
    return {
        "status": "ok",
        "path": str(fpath),
        "prompt": prompt,
        "provider": "local",
        "warning": "No image provider configured — saved prompt as text file",
    }


def _get_image_api_key(config: dict[str, Any], provider: str) -> str:
    """Extract API key from config nested under image.providers.<name>.api_key."""
    provider_cfg = config.get("image", {}).get("providers", {}).get(provider, {})
    key = provider_cfg.get("api_key", "")
    if key:
        return str(key)
    return ""


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

register_tool(
    "image_generate",
    schema={
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": (
                    "Detailed text description of the desired image. Include subject, "
                    "style, colors, lighting, and composition. Max ~4000 chars."
                ),
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["landscape", "square", "portrait"],
                "description": "Aspect ratio: landscape (16:9 wide), square (1:1), portrait (9:16 tall).",
                "default": "landscape",
            },
        },
        "required": ["prompt"],
    },
    safety_tier="auto",
    timeout=120,
    description=(
        "Generate high-quality images from text prompts. Uses the configured "
        "image provider (OpenAI DALL-E 3 by default, or Stability AI). Saves "
        "the generated image to ~/.jebat/images/ and returns the file path."
    ),
)(image_generate)