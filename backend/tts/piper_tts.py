"""
Piper TTS module.
Downloads voice model on first use.
Returns WAV bytes for a given text string.
"""

import asyncio
import io
import os
import wave
import structlog
from piper.voice import PiperVoice

logger = structlog.get_logger()

# Default English voice — change MODEL_DIR to point to your .onnx + .json files
MODEL_DIR = os.getenv("PIPER_MODEL_DIR", "/app/tts_models")
VOICE_NAME = os.getenv("PIPER_VOICE", "en_US-lessac-medium")

_voice: PiperVoice | None = None


def _get_voice() -> PiperVoice:
    global _voice
    if _voice is None:
        model_path = os.path.join(MODEL_DIR, f"{VOICE_NAME}.onnx")
        config_path = os.path.join(MODEL_DIR, f"{VOICE_NAME}.onnx.json")
        if not os.path.exists(model_path):
            logger.warning("piper_model_missing", path=model_path,
                           hint="Download from https://github.com/rhasspy/piper/releases")
            raise FileNotFoundError(f"Piper model not found: {model_path}")
        logger.info("piper_loading", voice=VOICE_NAME)
        _voice = PiperVoice.load(model_path, config_path=config_path, use_cuda=False)
        logger.info("piper_ready", voice=VOICE_NAME)
    return _voice


def _synthesize_sync(text: str) -> bytes:
    voice = _get_voice()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        voice.synthesize(text, wav_file)
    return buf.getvalue()


async def synthesize_speech(text: str) -> bytes:
    """Async wrapper — runs Piper synthesis in thread executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _synthesize_sync, text)
