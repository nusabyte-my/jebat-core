"""JEBAT Image Generation — DALL-E and Stable Diffusion support.

Provides image generation capability through multiple backends:
- OpenAI DALL-E 3 (API key required)
- Stable Diffusion via Stability AI (API key required)
- Local ComfyUI (optional, self-hosted)

Usage:
    from jebat.features.image_gen.image_gen import generate_image, list_backends

    result = await generate_image(
        prompt="A warrior standing on a mountain",
        backend="dalle",
        size="1024x1024",
        quality="hd",
    )
    # result = {"image_url": "...", "backend": "dalle", "revised_prompt": "..."}
"""

import asyncio
import base64
import json
import logging
import os
import struct
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ─── Data Models ────────────────────────────────────────────────────────

class ImageBackend(Enum):
    DALLE = "dalle"
    STABILITY = "stability"
    COMFYUI = "comfyui"


@dataclass
class ImageGenConfig:
    backend: ImageBackend = ImageBackend.DALLE
    dalle_api_key: str | None = None
    dalle_model: str = "dall-e-3"
    stability_api_key: str | None = None
    stability_model: str = "stable-diffusion-xl-1.0"
    comfyui_host: str = "http://127.0.0.1:8188"
    output_dir: str = ""
    default_size: str = "1024x1024"
    default_quality: str = "standard"


@dataclass
class ImageGenResult:
    success: bool
    image_url: str | None = None
    image_path: str | None = None
    image_base64: str | None = None
    backend: str = ""
    revised_prompt: str | None = None
    model_used: str = ""
    size: str = ""
    error: str | None = None
    metadata: dict = field(default_factory=dict)


# ─── DALL-E Backend ────────────────────────────────────────────────────

async def _generate_dalle(
    prompt: str,
    config: ImageGenConfig,
    size: str | None = None,
    quality: str | None = None,
    n: int = 1,
    style: str | None = None,
) -> ImageGenResult:
    """Generate image via OpenAI DALL-E API."""
    api_key = config.dalle_api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return ImageGenResult(success=False, backend="dalle", error="OPENAI_API_KEY not set")

    import urllib.request
    import urllib.error

    url = "https://api.openai.com/v1/images/generations"
    payload = {
        "model": config.dalle_model,
        "prompt": prompt,
        "n": n,
        "size": size or config.default_size,
        "quality": quality or config.default_quality,
    }
    if style:
        payload["style"] = style  # "natural" or "vivid"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        def _sync_call():
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))

        result_data = await asyncio.to_thread(_sync_call)

        images = result_data.get("data", [])
        if not images:
            return ImageGenResult(success=False, backend="dalle", error="No images returned")

        img = images[0]
        image_url = img.get("url")
        revised_prompt = img.get("revised_prompt")

        # Optionally download and save locally
        image_path = None
        if config.output_dir:
            out_dir = Path(config.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            # Download image
            def _download():
                dl_req = urllib.request.Request(image_url)
                with urllib.request.urlopen(dl_req, timeout=30) as dl_resp:
                    img_bytes = dl_resp.read()
                fname = f"jebat_dalle_{asyncio.get_event_loop().time():.0f}.png"
                fpath = out_dir / fname
                fpath.write_bytes(img_bytes)
                return str(fpath)

            image_path = await asyncio.to_thread(_download)

        return ImageGenResult(
            success=True,
            image_url=image_url,
            image_path=image_path,
            backend="dalle",
            revised_prompt=revised_prompt,
            model_used=config.dalle_model,
            size=payload["size"],
        )

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return ImageGenResult(success=False, backend="dalle", error=f"HTTP {e.code}: {body[:200]}")
    except Exception as e:
        return ImageGenResult(success=False, backend="dalle", error=str(e))


# ─── Stability AI Backend ──────────────────────────────────────────────

async def _generate_stability(
    prompt: str,
    config: ImageGenConfig,
    size: str | None = None,
    steps: int = 30,
    cfg_scale: float = 7.0,
    seed: int | None = None,
) -> ImageGenResult:
    """Generate image via Stability AI API."""
    api_key = config.stability_api_key or os.environ.get("STABILITY_API_KEY")
    if not api_key:
        return ImageGenResult(success=False, backend="stability", error="STABILITY_API_KEY not set")

    import urllib.request
    import urllib.error

    # Stability AI uses multipart form data
    url = f"https://api.stability.ai/v2beta/stable-image/generate/sd3"

    # Map size to width/height
    size_map = {
        "1024x1024": (1024, 1024),
        "1024x768": (1024, 768),
        "768x1024": (768, 1024),
        "512x512": (512, 512),
    }
    w, h = size_map.get(size or config.default_size, (1024, 1024))

    # Build multipart form
    boundary = "JEBATBoundary7MA4YWxkTrZu0gW"
    body_parts = []
    body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"prompt\"\r\n\r\n{prompt}")
    body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"output_format\"\r\n\r\npng")
    body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"width\"\r\n\r\n{w}")
    body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"height\"\r\n\r\n{h}")
    body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"steps\"\r\n\r\n{steps}")
    body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"cfg_scale\"\r\n\r\n{cfg_scale}")
    if seed:
        body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"seed\"\r\n\r\n{seed}")
    body_parts.append(f"--{boundary}--\r\n")
    body = "\r\n".join(body_parts).encode("utf-8")

    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Authorization": f"Bearer {api_key}",
        "Accept": "image/*",
    }

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")

        def _sync_call():
            with urllib.request.urlopen(req, timeout=120) as resp:
                img_bytes = resp.read()
            return img_bytes

        img_bytes = await asyncio.to_thread(_sync_call)

        # Save image
        image_path = None
        image_b64 = None
        if config.output_dir:
            out_dir = Path(config.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            fname = f"jebat_stability_{seed or 'auto'}.png"
            fpath = out_dir / fname
            fpath.write_bytes(img_bytes)
            image_path = str(fpath)
        else:
            image_b64 = base64.b64encode(img_bytes).decode("ascii")

        return ImageGenResult(
            success=True,
            image_path=image_path,
            image_base64=image_b64,
            backend="stability",
            model_used=config.stability_model,
            size=f"{w}x{h}",
        )

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return ImageGenResult(success=False, backend="stability", error=f"HTTP {e.code}: {body[:200]}")
    except Exception as e:
        return ImageGenResult(success=False, backend="stability", error=str(e))


# ─── ComfyUI Backend (Local) ──────────────────────────────────────────

async def _generate_comfyui(
    prompt: str,
    config: ImageGenConfig,
    negative_prompt: str = "",
    width: int = 1024,
    height: int = 1024,
    steps: int = 20,
    cfg_scale: float = 7.0,
    seed: int | None = None,
) -> ImageGenResult:
    """Generate image via local ComfyUI instance."""
    import urllib.request

    host = config.comfyui_host.rstrip("/")
    actual_seed = seed or struct.unpack("!I", os.urandom(4))[0] % 2**31

    # Build ComfyUI workflow JSON (basic txt2img)
    workflow = {
        "3": {  # KSampler
            "class_type": "KSampler",
            "inputs": {
                "seed": actual_seed,
                "steps": steps,
                "cfg": cfg_scale,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "4": {  # CheckpointLoaderSimple
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": config.stability_model.replace("stable-diffusion-", "sd").replace("-1.0", ".safetensors")},
        },
        "5": {  # EmptyLatentImage
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "6": {  # CLIPTextEncode (positive)
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["4", 1]},
        },
        "7": {  # CLIPTextEncode (negative)
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative_prompt, "clip": ["4", 1]},
        },
        "8": {  # VAEDecode
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
        },
        "9": {  # SaveImage
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "JEBAT", "images": ["8", 0]},
        },
    }

    try:
        # Queue the prompt
        payload = json.dumps({"prompt": workflow}).encode("utf-8")
        req = urllib.request.Request(
            f"{host}/prompt",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        def _queue():
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))

        queue_result = await asyncio.to_thread(_queue)
        prompt_id = queue_result.get("prompt_id")

        if not prompt_id:
            return ImageGenResult(success=False, backend="comfyui", error="ComfyUI didn't return prompt_id")

        # Poll for completion
        for _ in range(60):
            await asyncio.sleep(2)

            def _check():
                check_req = urllib.request.Request(f"{host}/history/{prompt_id}")
                with urllib.request.urlopen(check_req, timeout=5) as resp:
                    return json.loads(resp.read().decode("utf-8"))

            history = await asyncio.to_thread(_check)
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                if "9" in outputs:
                    images = outputs["9"].get("images", [])
                    if images:
                        img_info = images[0]
                        filename = img_info["filename"]
                        subfolder = img_info.get("subfolder", "")

                        # Fetch the actual image
                        img_url = f"{host}/view?filename={filename}&subfolder={subfolder}&type=output"
                        return ImageGenResult(
                            success=True,
                            image_url=img_url,
                            backend="comfyui",
                            model_used="comfyui-local",
                            size=f"{width}x{height}",
                            metadata={"seed": actual_seed, "prompt_id": prompt_id},
                        )

        return ImageGenResult(success=False, backend="comfyui", error="ComfyUI generation timed out")

    except Exception as e:
        return ImageGenResult(success=False, backend="comfyui", error=str(e))


# ─── Public API ─────────────────────────────────────────────────────────

def _load_config() -> ImageGenConfig:
    """Load image generation config from environment."""
    return ImageGenConfig(
        dalle_api_key=os.environ.get("OPENAI_API_KEY"),
        dalle_model=os.environ.get("JEBAT_DALLE_MODEL", "dall-e-3"),
        stability_api_key=os.environ.get("STABILITY_API_KEY"),
        stability_model=os.environ.get("JEBAT_SD_MODEL", "stable-diffusion-xl-1.0"),
        comfyui_host=os.environ.get("JEBAT_COMFYUI_HOST", "http://127.0.0.1:8188"),
        output_dir=os.environ.get("JEBAT_IMAGE_DIR", ""),
        default_size=os.environ.get("JEBAT_IMAGE_SIZE", "1024x1024"),
    )


async def generate_image(
    prompt: str,
    backend: str | None = None,
    size: str | None = None,
    quality: str | None = None,
    negative_prompt: str = "",
    steps: int = 30,
    cfg_scale: float = 7.0,
    seed: int | None = None,
    n: int = 1,
    style: str | None = None,
    output_dir: str | None = None,
) -> ImageGenResult:
    """Generate an image from a text prompt.

    Args:
        prompt: Text description of desired image
        backend: "dalle", "stability", or "comfyui" (default: dalle)
        size: Image dimensions (e.g. "1024x1024")
        quality: Image quality ("standard" or "hd" for DALL-E)
        negative_prompt: What to avoid (Stability/ComfyUI only)
        steps: Generation steps (Stability/ComfyUI)
        cfg_scale: CFG guidance scale (Stability/ComfyUI)
        seed: Reproducibility seed
        n: Number of images (DALL-E only)
        style: "natural" or "vivid" (DALL-E only)
        output_dir: Directory to save images locally

    Returns:
        ImageGenResult with image_url, image_path, or base64 data
    """
    config = _load_config()
    if output_dir:
        config.output_dir = output_dir

    backend_enum = ImageBackend(backend or config.backend.value)

    if backend_enum == ImageBackend.DALLE:
        return await _generate_dalle(prompt, config, size=size, quality=quality, n=n, style=style)
    elif backend_enum == ImageBackend.STABILITY:
        return await _generate_stability(prompt, config, size=size, steps=steps, cfg_scale=cfg_scale, seed=seed)
    elif backend_enum == ImageBackend.COMFYUI:
        # Parse size into width/height for ComfyUI
        size_map = {"1024x1024": (1024, 1024), "512x512": (512, 512), "1024x768": (1024, 768), "768x1024": (768, 1024)}
        w, h = size_map.get(size or config.default_size, (1024, 1024))
        return await _generate_comfyui(prompt, config, negative_prompt=negative_prompt, width=w, height=h, steps=steps, cfg_scale=cfg_scale, seed=seed)
    else:
        return ImageGenResult(success=False, backend=backend, error=f"Unknown backend: {backend}")


def list_backends() -> list[dict[str, str]]:
    """List available image generation backends and their status."""
    config = _load_config()
    backends = []
    if config.dalle_api_key:
        backends.append({"name": "dalle", "model": config.dalle_model, "status": "ready"})
    else:
        backends.append({"name": "dalle", "model": config.dalle_model, "status": "missing_api_key"})
    if config.stability_api_key:
        backends.append({"name": "stability", "model": config.stability_model, "status": "ready"})
    else:
        backends.append({"name": "stability", "model": config.stability_model, "status": "missing_api_key"})
    backends.append({"name": "comfyui", "model": "local", "status": f"host={config.comfyui_host}"})
    return backends