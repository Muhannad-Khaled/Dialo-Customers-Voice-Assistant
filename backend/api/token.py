from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from livekit.api import AccessToken, VideoGrants
from core.config import settings

router = APIRouter()


class TokenRequest(BaseModel):
    room: str
    identity: str


class TokenResponse(BaseModel):
    token: str
    url: str


@router.post("/token", response_model=TokenResponse)
async def get_livekit_token(req: TokenRequest):
    try:
        token = (
            AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
            .with_identity(req.identity)
            .with_name(req.identity)
            .with_grants(VideoGrants(room_join=True, room=req.room))
            .to_jwt()
        )
        return TokenResponse(token=token, url=settings.livekit_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
