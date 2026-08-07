"""Unit test for the Piper TTS adapter — model loading is lazy, so this
constructs the plugin without touching Piper weights or any service.
(STT now uses the Groq API plugin directly, so there's no local STT adapter.)"""

from livekit_agent.piper_tts_plugin import PiperTTS


def test_piper_capabilities():
    tts = PiperTTS()
    assert tts.sample_rate == 22050
    assert tts.num_channels == 1
    assert tts.capabilities.streaming is False
