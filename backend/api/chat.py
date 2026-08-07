from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agent.graph import run_agent
import structlog

router = APIRouter()
logger = structlog.get_logger()


class ChatRequest(BaseModel):
    query: str
    session_id: str


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[str] = []


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        result = await run_agent(query=req.query, session_id=req.session_id)
        return ChatResponse(
            answer=result["answer"],
            session_id=req.session_id,
            sources=result.get("sources", []),
        )
    except Exception as e:
        logger.error("chat_error", error=str(e))
        raise HTTPException(status_code=500, detail="Agent error: " + str(e))
