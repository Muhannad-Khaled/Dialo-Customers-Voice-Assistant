import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from livekit.api import AccessToken, VideoGrants
from core.config import settings

router = APIRouter()


class TokenRequest(BaseModel):
    room: str
    identity: str
    language: str = "en"  # "en" | "ar" — the agent reads this from participant attributes


class TokenResponse(BaseModel):
    token: str
    url: str


@router.post("/token", response_model=TokenResponse)
async def get_livekit_token(req: TokenRequest):
    try:
        # Carry the chosen language so the agent worker can pick the STT language +
        # TTS voice + reply language per call. Prefer participant attributes; fall
        # back to metadata on older livekit-api versions without with_attributes.
        builder = (
            AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
            .with_identity(req.identity)
            .with_name(req.identity)
            .with_grants(VideoGrants(room_join=True, room=req.room))
        )
        if hasattr(builder, "with_attributes"):
            builder = builder.with_attributes({"language": req.language})
        else:
            builder = builder.with_metadata(json.dumps({"language": req.language}))
        token = builder.to_jwt()
        return TokenResponse(token=token, url=settings.livekit_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
