from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Feedback, Message
from db.session import get_db

router = APIRouter()


class FeedbackRequest(BaseModel):
    message_id: int
    rating: int = Field(description="+1 for thumbs up, -1 for thumbs down", ge=-1, le=1)
    comment: str | None = None


class FeedbackResponse(BaseModel):
    id: int
    message_id: int
    rating: int


@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(req: FeedbackRequest, db: AsyncSession = Depends(get_db)):
    if req.rating == 0:
        raise HTTPException(status_code=422, detail="rating must be +1 or -1")

    message = await db.get(Message, req.message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    fb = Feedback(message_id=req.message_id, rating=req.rating, comment=req.comment)
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return FeedbackResponse(id=fb.id, message_id=fb.message_id, rating=fb.rating)
