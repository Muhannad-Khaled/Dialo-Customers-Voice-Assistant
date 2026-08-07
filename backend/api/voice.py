from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from stt.whisper_stt import transcribe_audio
from tts.piper_tts import synthesize_speech
import io

router = APIRouter()


@router.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    """Accept audio file, return transcript."""
    audio_bytes = await audio.read()
    try:
        transcript = await transcribe_audio(audio_bytes)
        return {"transcript": transcript}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts")
async def text_to_speech(body: dict):
    """Accept text, return WAV audio stream."""
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="text field is required")
    try:
        audio_bytes = await synthesize_speech(text)
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/wav",
            headers={"Content-Disposition": "inline; filename=response.wav"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
