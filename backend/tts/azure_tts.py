"""
Azure Speech TTS — the Egyptian-Arabic voice for Dialo.

Piper (the offline default) has no Egyptian voice, so Arabic calls synthesize via
Azure's Cognitive Services REST endpoint instead. This mirrors tts/piper_tts.py:
a single async function that takes text and returns a complete WAV clip (bytes),
which the LiveKit plugin (livekit_agent/azure_tts_plugin.py) wraps as a
non-streaming TTS.

Uses the existing httpx dependency and key-based auth (Ocp-Apim-Subscription-Key) —
no Azure Speech SDK required.
"""

from xml.sax.saxutils import escape

import httpx

from core.config import settings

# 24 kHz mono 16-bit PCM in a RIFF/WAV container — the plugin reads the real rate
# back from the WAV header, so this only has to be a format Azure supports.
_OUTPUT_FORMAT = "riff-24khz-16bit-mono-pcm"


async def synthesize_azure(text: str, voice: str | None = None) -> bytes:
    """Synthesize `text` with an Azure Egyptian-Arabic voice; return WAV bytes."""
    if not settings.azure_speech_key or not settings.azure_speech_region:
        raise RuntimeError(
            "Azure Speech not configured — set AZURE_SPEECH_KEY and "
            "AZURE_SPEECH_REGION in .env to enable Arabic TTS."
        )

    voice_name = voice or settings.azure_tts_voice_ar
    url = (
        f"https://{settings.azure_speech_region}.tts.speech.microsoft.com"
        "/cognitiveservices/v1"
    )
    ssml = (
        '<speak version="1.0" xml:lang="ar-EG">'
        f'<voice name="{voice_name}">{escape(text)}</voice>'
        "</speak>"
    )
    headers = {
        "Ocp-Apim-Subscription-Key": settings.azure_speech_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": _OUTPUT_FORMAT,
        "User-Agent": "dialo",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, content=ssml.encode("utf-8"))
        resp.raise_for_status()
        return resp.content
