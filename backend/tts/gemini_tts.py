"""
Gemini TTS — the Egyptian-Arabic voice for Dialo (default provider).

Piper (the offline default) has no Egyptian voice, so Arabic calls synthesize via
Gemini's TTS models instead. This reuses the existing GEMINI_API_KEY (no new secret)
and the already-installed google-genai SDK (no new dependency). Azure remains a
config-selectable fallback (see tts/azure_tts.py) in case the preview TTS model is
not callable on a given key.

Like tts/piper_tts.py and tts/azure_tts.py this exposes a single async function that
takes text and returns a complete WAV clip (bytes), which the LiveKit plugin
(livekit_agent/gemini_tts_plugin.py) wraps as a non-streaming TTS.

Gemini TTS returns RAW PCM (24 kHz, 16-bit, mono), so we wrap it in a WAV container
here — that keeps the plugin's "read the WAV header" path identical across engines.
"""

import io
import wave

from google import genai
from google.genai import types

from core.config import settings

# Gemini TTS output is L16 PCM at 24 kHz, mono.
_SAMPLE_RATE = 24000
_SAMPLE_WIDTH = 2  # bytes (16-bit)
_NUM_CHANNELS = 1

# Style prefix that biases the accent toward Egyptian dialect. Gemini infers accent
# from the text + instruction rather than a dedicated ar-EG voice.
_STYLE_PREFIX = "Say the following in a natural, friendly Egyptian Arabic dialect: "


def _pcm_to_wav(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(_NUM_CHANNELS)
        wav_file.setsampwidth(_SAMPLE_WIDTH)
        wav_file.setframerate(_SAMPLE_RATE)
        wav_file.writeframes(pcm)
    return buf.getvalue()


async def synthesize_gemini(text: str, voice: str | None = None) -> bytes:
    """Synthesize `text` with a Gemini TTS voice (Egyptian bias); return WAV bytes."""
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set — cannot use Gemini TTS.")

    voice_name = voice or settings.gemini_tts_voice
    client = genai.Client(api_key=settings.gemini_api_key)

    response = await client.aio.models.generate_content(
        model=settings.gemini_tts_model,
        contents=_STYLE_PREFIX + text,
        config=types.GenerateContentConfig(
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            ),
        ),
    )

    # Audio arrives as raw PCM bytes in the first candidate's inline_data. On an
    # empty/blocked response the content chain can be None — surface a clear error
    # instead of an opaque AttributeError.
    pcm = None
    candidates = response.candidates or []
    if candidates and candidates[0].content and candidates[0].content.parts:
        inline = candidates[0].content.parts[0].inline_data
        pcm = inline.data if inline else None
    if not pcm:
        raise RuntimeError("Gemini TTS returned no audio (empty or blocked response).")
    return _pcm_to_wav(pcm)
