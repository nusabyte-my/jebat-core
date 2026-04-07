"""
Voice Integration Module — Whisper STT + ElevenLabs TTS
Q1 2027: Voice commands and text-to-speech responses

Provides voice command processing and speech synthesis for JEBAT.
"""

import os
import json
import base64
from typing import Optional
from dataclasses import dataclass


@dataclass
class VoiceConfig:
    """Configuration for voice services."""
    # Whisper STT
    whisper_api_key: str = ""
    whisper_model: str = "whisper-1"
    whisper_language: str = "en"
    
    # ElevenLabs TTS
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "EXAVITQu4vr4xnSDxMaL"  # Default voice
    elevenlabs_model: str = "eleven_multilingual_v2"
    
    @classmethod
    def from_env(cls):
        return cls(
            whisper_api_key=os.getenv("WHISPER_API_KEY", ""),
            whisper_model=os.getenv("WHISPER_MODEL", "whisper-1"),
            whisper_language=os.getenv("WHISPER_LANGUAGE", "en"),
            elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY", ""),
            elevenlabs_voice_id=os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL"),
            elevenlabs_model=os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
        )


class WhisperSTT:
    """
    Speech-to-Text using OpenAI Whisper API.
    
    Supports audio file uploads and returns transcribed text.
    Falls back to local whisper model if API key not set.
    """
    
    def __init__(self, config: VoiceConfig = None):
        self.config = config or VoiceConfig.from_env()
    
    def transcribe(self, audio_data: bytes, language: str = None) -> dict:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Audio bytes (WAV, MP3, M4A, etc.)
            language: Language code (e.g., 'en', 'ms', 'zh')
            
        Returns:
            dict with 'text', 'language', 'duration', 'segments'
        """
        if self.config.whisper_api_key:
            return self._transcribe_api(audio_data, language)
        return self._transcribe_local(audio_data, language)
    
    def _transcribe_api(self, audio_data: bytes, language: str) -> dict:
        """Transcribe using OpenAI Whisper API."""
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.config.whisper_api_key}",
        }
        
        files = {
            "file": ("audio.wav", audio_data, "audio/wav"),
            "model": (None, self.config.whisper_model),
        }
        
        if language:
            files["language"] = (None, language)
        elif self.config.whisper_language:
            files["language"] = (None, self.config.whisper_language)
        
        with httpx.Client() as client:
            response = client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
            )
            response.raise_for_status()
            data = response.json()
        
        return {
            "text": data.get("text", ""),
            "language": data.get("language", self.config.whisper_language),
            "duration": data.get("duration", 0),
            "segments": data.get("segments", []),
        }
    
    def _transcribe_local(self, audio_data: bytes, language: str) -> dict:
        """Transcribe using local whisper model (fallback)."""
        try:
            import whisper
            model = whisper.load_model("base")
            # Save to temp file for whisper
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            result = model.transcribe(temp_path, language=language or self.config.whisper_language)
            os.unlink(temp_path)
            
            return {
                "text": result.get("text", ""),
                "language": language or self.config.whisper_language,
                "duration": result.get("duration", 0),
                "segments": result.get("segments", []),
            }
        except ImportError:
            return {"text": "", "error": "Whisper not installed", "language": ""}


class ElevenLabsTTS:
    """
    Text-to-Speech using ElevenLabs API.
    
    Converts text responses to natural-sounding speech.
    """
    
    def __init__(self, config: VoiceConfig = None):
        self.config = config or VoiceConfig.from_env()
    
    def synthesize(self, text: str, voice_id: str = None) -> dict:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use (falls back to config)
            
        Returns:
            dict with 'audio_base64', 'content_type', 'duration_estimate'
        """
        if not self.config.elevenlabs_api_key:
            return {"error": "ElevenLabs API key not set"}
        
        import httpx
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.config.elevenlabs_api_key,
        }
        
        data = {
            "text": text,
            "model_id": self.config.elevenlabs_model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            }
        }
        
        voice = voice_id or self.config.elevenlabs_voice_id
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
        
        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=data)
            response.raise_for_status()
            audio_bytes = response.content
        
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        return {
            "audio_base64": audio_base64,
            "content_type": "audio/mpeg",
            "duration_estimate": len(text) * 0.05,  # Rough estimate: ~20 chars/sec
        }
    
    def list_voices(self) -> list[dict]:
        """List available ElevenLabs voices."""
        if not self.config.elevenlabs_api_key:
            return []
        
        import httpx
        
        headers = {
            "xi-api-key": self.config.elevenlabs_api_key,
        }
        
        with httpx.Client() as client:
            response = client.get(
                "https://api.elevenlabs.io/v1/voices",
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        
        return [
            {
                "id": v["voice_id"],
                "name": v["name"],
                "category": v["category"],
                "description": v.get("description", ""),
            }
            for v in data.get("voices", [])
        ]


# ─── FastAPI Integration ───────────────────────────────────────────────────────

def register_voice_routes(app):
    """Register voice endpoints on a FastAPI app."""
    from fastapi import UploadFile, File, HTTPException
    
    stt = WhisperSTT()
    tts = ElevenLabsTTS()
    
    @app.post("/api/v1/voice/transcribe")
    async def transcribe_audio(file: UploadFile = File(...), language: str = None):
        """Transcribe uploaded audio file to text."""
        audio_data = await file.read()
        result = stt.transcribe(audio_data, language)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    
    @app.post("/api/v1/voice/synthesize")
    async def synthesize_speech(text: str, voice_id: str = None):
        """Synthesize text to speech audio."""
        result = tts.synthesize(text, voice_id)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    
    @app.get("/api/v1/voice/voices")
    async def list_voices():
        """List available TTS voices."""
        return {"voices": tts.list_voices()}
