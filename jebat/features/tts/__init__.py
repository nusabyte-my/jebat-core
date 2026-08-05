"""JEBAT TTS Module — Suara (The Voice).

Text-to-speech for multi-channel delivery:
  - Edge TTS (free, no API key, 100+ voices)
  - OpenAI TTS (API key, higher quality)
  - Output: MP3/WAV saved to jebat cache directory

Safety: All TTS generation is AUTO tier (local processing).
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

# Edge TTS voices — subset of popular ones by language
EDGE_VOICES: dict[str, str] = {
    "en-US-female": "en-US-AriaNeural",
    "en-US-male": "en-US-GuyNeural",
    "en-US-natural": "en-US-JennyNeural",
    "en-GB-female": "en-GB-SoniaNeural",
    "en-GB-male": "en-GB-RyanNeural",
    "en-AU-female": "en-AU-NatashaNeural",
    "zh-CN-female": "zh-CN-XiaoxiaoNeural",
    "zh-CN-male": "zh-CN-YunxiNeural",
    "ja-JP-female": "ja-JP-NanamiNeural",
    "ja-JP-male": "ja-JP-KeitaNeural",
    "ko-KR-female": "ko-KR-SunHiNeural",
    "ko-KR-male": "ko-KR-InJoonNeural",
    "ms-MY-female": "ms-MY-YasminNeural",  # Bahasa Malaysia
    "ms-MY-male": "ms-MY-OsmanNeural",
    "id-ID-female": "id-ID-GadisNeural",   # Bahasa Indonesia
    "id-ID-male": "id-ID-ArdiNeural",
    "ar-SA-female": "ar-SA-ZariyahNeural",
    "ar-SA-male": "ar-SA-HamedNeural",
    "fr-FR-female": "fr-FR-DeniseNeural",
    "fr-FR-male": "fr-FR-HenriNeural",
    "de-DE-female": "de-DE-KatjaNeural",
    "de-DE-male": "de-DE-ConradNeural",
    "es-ES-female": "es-ES-ElviraNeural",
    "es-ES-male": "es-ES-AlvaroNeural",
    "pt-BR-female": "pt-BR-FranciscaNeural",
    "pt-BR-male": "pt-BR-AntonioNeural",
    "hi-IN-female": "hi-IN-SwaraNeural",
    "hi-IN-male": "hi-IN-MadhurNeural",
}


@dataclass(slots=True)
class TTSResult:
    """Result of a TTS generation."""
    filepath: str
    format: str  # mp3 or wav
    voice: str
    text_length: int
    duration_ms: int = 0
    created_at: str = ""


async def edge_tts(
    text: str,
    voice: str = "en-US-JennyNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    output_dir: str | None = None,
) -> TTSResult:
    """Generate speech using Microsoft Edge TTS (free, no API key).

    Uses edge-tts via subprocess. Falls back to internal HTTP API if edge-tts
    is not installed.

    Args:
        text: Text to convert to speech
        voice: Microsoft voice name (default: en-US-JennyNeural)
        rate: Speaking rate adjustment (e.g., "+10%", "-5%")
        pitch: Pitch adjustment (e.g., "+2Hz", "-3Hz")
        output_dir: Custom output directory (default: ~/.jebat/tts/)

    Returns:
        TTSResult with filepath, format, voice info
    """
    # Determine output path
    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = Path.home() / ".jebat" / "tts"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename from text hash + timestamp
    text_hash = hashlib.sha256(text.encode()[:128]).hexdigest()[:12]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = out_dir / f"tts_{voice}_{text_hash}_{timestamp}.mp3"

    # Try edge-tts CLI first (best quality)
    try:
        proc = await asyncio.create_subprocess_exec(
            "edge-tts",
            "--voice", voice,
            "--rate", rate,
            "--pitch", pitch,
            "--text", text,
            "--write-media", str(output_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        if proc.returncode == 0 and output_path.exists():
            return TTSResult(
                filepath=str(output_path),
                format="mp3",
                voice=voice,
                text_length=len(text),
                created_at=datetime.now().isoformat(),
            )
        # edge-tts CLI failed — try the Python library or HTTP fallback
    except (FileNotFoundError, asyncio.TimeoutError):
        pass

    # Fallback: try edge-tts Python library
    try:
        import edge_tts as et
        communicate = et.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(str(output_path))
        return TTSResult(
            filepath=str(output_path),
            format="mp3",
            voice=voice,
            text_length=len(text),
            created_at=datetime.now().isoformat(),
        )
    except ImportError:
        pass

    # Last resort: HTTP API (edge-tts unofficial endpoint)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Use the unofficial edge-tts HTTP API
            url = "https://api.edge-tts.com/v1/tts"
            payload = {
                "text": text,
                "voice": voice,
                "rate": rate,
                "pitch": pitch,
            }
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                output_path.write_bytes(response.content)
                return TTSResult(
                    filepath=str(output_path),
                    format="mp3",
                    voice=voice,
                    text_length=len(text),
                    created_at=datetime.now().isoformat(),
                )
    except Exception:
        pass

    raise RuntimeError(
        "Edge TTS not available. Install it:\n"
        "  pip install edge-tts\n"
        "Or use: jebat tts openai \"text\" --model tts-1"
    )


async def openai_tts(
    text: str,
    api_key: str | None = None,
    model: str = "tts-1",
    voice: str = "alloy",
    speed: float = 1.0,
    response_format: str = "mp3",
    output_dir: str | None = None,
) -> TTSResult:
    """Generate speech using OpenAI TTS API.

    Requires OPENAI_API_KEY env var or explicit api_key parameter.

    Voices: alloy, echo, fable, onyx, nova, shimmer
    Models: tts-1 (faster), tts-1-hd (higher quality)

    Args:
        text: Text to convert to speech
        api_key: OpenAI API key (default: OPENAI_API_KEY env)
        model: tts-1 or tts-1-hd
        voice: alloy, echo, fable, onyx, nova, shimmer
        speed: 0.25 to 4.0
        response_format: mp3, opus, aac, flac, wav, pcm
        output_dir: Custom output directory

    Returns:
        TTSResult with filepath
    """
    key = api_key or os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise ValueError("OPENAI_API_KEY not set")

    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = Path.home() / ".jebat" / "tts"
    out_dir.mkdir(parents=True, exist_ok=True)

    text_hash = hashlib.sha256(text.encode()[:128]).hexdigest()[:12]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = "wav" if response_format == "wav" else "mp3"
    output_path = out_dir / f"tts_{voice}_{text_hash}_{timestamp}.{ext}"

    url = "https://api.openai.com/v1/audio/speech"
    payload = {
        "model": model,
        "voice": voice,
        "input": text,
        "speed": speed,
        "response_format": response_format,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {key}"},
        )
        response.raise_for_status()
        output_path.write_bytes(response.content)

    return TTSResult(
        filepath=str(output_path),
        format=response_format,
        voice=f"openai:{voice}",
        text_length=len(text),
        created_at=datetime.now().isoformat(),
    )


def list_tts_voices(language: str | None = None) -> dict[str, str]:
    """List available Edge TTS voices, optionally filtered by language prefix.

    Args:
        language: Optional language filter (e.g., 'en', 'ms', 'zh')

    Returns:
        Dict mapping shorthand to full voice name
    """
    if language:
        return {
            k: v for k, v in EDGE_VOICES.items()
            if k.startswith(language)
        }
    return EDGE_VOICES.copy()


# ── Agent Tool Registration ───────────────────────────────────────────────

from jebat.tools import register_tool

register_tool(
    "tts_edge",
    handler=edge_tts,
    schema={
        "description": (
            "Convert text to speech using Microsoft Edge TTS (free, no API key). "
            "100+ neural voices in 50+ languages. Saves MP3 to ~/.jebat/tts/."
        ),
        "parameters": {
            "text": {"type": "string", "description": "Text to speak"},
            "voice": {
                "type": "string",
                "description": f"Voice name. Shortcuts: {', '.join(list(EDGE_VOICES.keys())[:8])}... or full Microsoft voice name",
                "default": "en-US-JennyNeural",
            },
            "rate": {"type": "string", "description": "Speed adjustment (e.g., '+10%', '-5%')", "default": "+0%"},
            "pitch": {"type": "string", "description": "Pitch adjustment (e.g., '+2Hz')", "default": "+0Hz"},
            "output_dir": {"type": "string", "description": "Custom output directory"},
        },
        "required": ["text"],
    },
    safety_tier="auto",
)

register_tool(
    "tts_openai",
    handler=openai_tts,
    schema={
        "description": (
            "Generate speech with OpenAI TTS (requires API key). "
            "High quality voices: alloy, echo, fable, onyx, nova, shimmer."
        ),
        "parameters": {
            "text": {"type": "string", "description": "Text to speak"},
            "voice": {"type": "string", "description": "Voice: alloy, echo, fable, onyx, nova, shimmer", "default": "alloy"},
            "model": {"type": "string", "description": "tts-1 (fast) or tts-1-hd (quality)", "default": "tts-1"},
            "speed": {"type": "number", "description": "Speed 0.25-4.0", "default": 1.0},
            "response_format": {"type": "string", "description": "mp3, opus, aac, flac, wav, pcm", "default": "mp3"},
            "output_dir": {"type": "string", "description": "Custom output directory"},
        },
        "required": ["text"],
    },
    safety_tier="auto",
)

register_tool(
    "tts_voices",
    handler=lambda language=None: list_tts_voices(language),
    schema={
        "description": "List available TTS voices, optionally filtered by language",
        "parameters": {
            "language": {"type": "string", "description": "Language prefix filter (e.g., 'en', 'ms', 'zh', 'ja')"},
        },
    },
    safety_tier="auto",
)