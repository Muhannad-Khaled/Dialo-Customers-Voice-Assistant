"""
LiveKit Agents TTS adapter around the existing Piper implementation.

Piper returns a complete WAV per utterance, so this is a non-streaming
``ChunkedStream``: synthesize the whole clip, strip the WAV header, and push the
raw PCM to the framework's AudioEmitter at the voice's native sample rate.

Verified against livekit-agents==1.6.7.
"""

import io
import os
import wave

from livekit.agents import utils, APIConnectOptions, DEFAULT_API_CONNECT_OPTIONS
from livekit.agents.tts import TTS, TTSCapabilities, ChunkedStream, AudioEmitter

from tts.piper_tts import synthesize_speech  # existing async fn: text -> WAV bytes

# en_US-lessac-medium is 22.05 kHz mono. Override if you change PIPER_VOICE.
PIPER_SAMPLE_RATE = int(os.getenv("PIPER_SAMPLE_RATE", "22050"))
NUM_CHANNELS = 1


class PiperTTS(TTS):
    """Piper as a LiveKit TTS plugin (non-streaming, one clip per utterance)."""

    def __init__(self) -> None:
        super().__init__(
            capabilities=TTSCapabilities(streaming=False),
            sample_rate=PIPER_SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
        )

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "PiperChunkedStream":
        return PiperChunkedStream(tts=self, input_text=text, conn_options=conn_options)


class PiperChunkedStream(ChunkedStream):
    async def _run(self, output_emitter: AudioEmitter) -> None:
        wav_bytes = await synthesize_speech(self.input_text)
        with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            num_channels = wav_file.getnchannels()
            pcm = wav_file.readframes(wav_file.getnframes())  # raw int16 PCM

        output_emitter.initialize(
            request_id=utils.shortuuid(),
            sample_rate=sample_rate,
            num_channels=num_channels,
            mime_type="audio/pcm",
        )
        output_emitter.push(pcm)
        output_emitter.flush()
