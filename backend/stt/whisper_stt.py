"""
Speech-To-Text via the Groq-hosted Whisper API (OpenAI-compatible endpoint).

Used by the REST fallback endpoint /api/stt. The real-time LiveKit agent uses the
`groq.STT` plugin directly (see agent_worker.py); both hit the same Groq model, so
there's no local model and no PyTorch/ffmpeg needed for transcription.
"""

import httpx
import structlog

from core.config import settings

logger = structlog.get_logger()

GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_STT_MODEL = "whisper-large-v3-turbo"


async def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe raw audio bytes (webm/wav/mp3/…) to text via Groq Whisper."""
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set — cannot transcribe")

    files = {"file": ("audio.webm", audio_bytes, "application/octet-stream")}
    data = {"model": GROQ_STT_MODEL, "response_format": "json", "language": "en"}
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(GROQ_STT_URL, headers=headers, files=files, data=data)
        resp.raise_for_status()
        transcript = resp.json().get("text", "").strip()

    logger.info("stt_done", transcript_len=len(transcript))
    return transcript
