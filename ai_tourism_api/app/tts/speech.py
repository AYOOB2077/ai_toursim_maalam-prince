"""
LAYER 5 — TEXT-TO-SPEECH
=========================
Converts the LLM-generated story into an MP3 file. Provider-agnostic:
set TTS_PROVIDER=elevenlabs|openai|none in the environment. Audio is cached
on disk keyed by a hash of (text, voice) so we synthesize once per unique
narration. Swap AUDIO_CACHE_DIR for an S3/MinIO-backed path in production.
"""
import hashlib
import os

from app.config import settings


def _cache_path(text: str, voice: str) -> str:
    key = hashlib.sha256(f"{voice}:{text}".encode("utf-8")).hexdigest()
    return os.path.join(settings.AUDIO_CACHE_DIR, f"{key}.mp3")


def _synthesize_elevenlabs(text: str) -> bytes:
    import requests

    voice_id = settings.ELEVENLABS_VOICE_ID or "21m00Tcm4TlvDq8ikWAM"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": settings.ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {"text": text, "model_id": "eleven_multilingual_v2"}
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.content


def _synthesize_openai(text: str) -> bytes:
    from typing import Any, cast
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.audio.speech.create(
        model="tts-1",
        voice=cast(Any, settings.OPENAI_TTS_VOICE),
        input=text,
    )
    return response.content


def _synthesize_gtts(text: str) -> bytes:
    import io
    from gtts import gTTS

    fp = io.BytesIO()
    tts = gTTS(text=text, lang="en")
    tts.write_to_fp(fp)
    return fp.getvalue()


def synthesize(text: str, voice: str = "default") -> str | None:
    """
    Returns a relative URL path to the generated MP3, or None if no TTS
    provider is configured (the API will still return the story text).
    """
    path = _cache_path(text, voice)
    if os.path.exists(path):
        return _url_for(path)

    provider = settings.TTS_PROVIDER.lower()
    try:
        if provider == "gtts":
            audio_bytes = _synthesize_gtts(text)
        elif provider == "elevenlabs" and settings.ELEVENLABS_API_KEY:
            audio_bytes = _synthesize_elevenlabs(text)
        elif provider == "openai" and settings.OPENAI_API_KEY:
            audio_bytes = _synthesize_openai(text)
        else:
            return None
    except Exception:
        return None

    with open(path, "wb") as f:
        f.write(audio_bytes)
    return _url_for(path)


def _url_for(path: str) -> str:
    filename = os.path.basename(path)
    return f"{settings.AUDIO_PUBLIC_BASE_URL}/{filename}"
