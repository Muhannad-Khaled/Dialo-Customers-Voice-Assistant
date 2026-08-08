"""
LiveKit Agents TTS adapter around Azure Speech (Egyptian-Arabic voice).

Azure's REST endpoint returns a complete WAV per utterance, so this is a
non-streaming ``ChunkedStream`` — the same shape as piper_tts_plugin.py:
synthesize the whole clip, strip the WAV header, and push the raw PCM to the
framework's AudioEmitter at the voice's native sample rate.

Verified against livekit-agents==1.6.7.
"""

import io
import wave

from livekit.agents import utils, APIConnectOptions, DEFAULT_API_CONNECT_OPTIONS
from livekit.agents.tts import TTS, TTSCapabilities, ChunkedStream, AudioEmitter

from tts.azure_tts import synthesize_azure  # async fn: text -> WAV bytes

# Azure is requested as 24 kHz mono PCM (see azure_tts._OUTPUT_FORMAT). The stream
# below reads the real rate back from the WAV header, so this is only the declared
# capability rate.
AZURE_SAMPLE_RATE = 24000
NUM_CHANNELS = 1


class AzureTTS(TTS):
    """Azure Speech as a LiveKit TTS plugin (non-streaming, one clip per utterance)."""

    def __init__(self, voice: str | None = None) -> None:
        super().__init__(
            capabilities=TTSCapabilities(streaming=False),
            sample_rate=AZURE_SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
        )
        self._voice = voice

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "AzureChunkedStream":
        return AzureChunkedStream(
            tts=self, input_text=text, conn_options=conn_options, voice=self._voice
        )


class AzureChunkedStream(ChunkedStream):
    def __init__(self, *, voice: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._voice = voice

    async def _run(self, output_emitter: AudioEmitter) -> None:
        wav_bytes = await synthesize_azure(self.input_text, voice=self._voice)
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
