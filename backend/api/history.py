import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud import get_messages
from db.session import get_db

router = APIRouter()


class HistoryMessage(BaseModel):
    id: int
    role: str
    content: str
    sources: list[str] = []


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[HistoryMessage]


@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    rows = await get_messages(db, session_id)
    messages = [
        HistoryMessage(
            id=m.id,
            role=m.role,
            content=m.content,
            sources=json.loads(m.sources) if m.sources else [],
        )
        for m in rows
    ]
    return HistoryResponse(session_id=session_id, messages=messages)
