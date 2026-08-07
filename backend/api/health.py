from fastapi import APIRouter
import chromadb
import redis.asyncio as aioredis
from sqlalchemy import text
from core.config import settings
from db.session import engine
import structlog

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health", tags=["health"])
async def health_check():
    status = {"status": "ok", "services": {}}

    # ChromaDB
    try:
        client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        client.heartbeat()
        status["services"]["chromadb"] = "ok"
    except Exception as e:
        status["services"]["chromadb"] = f"error: {e}"
        status["status"] = "degraded"

    # PostgreSQL (skipped in the lite profile)
    if settings.enable_postgres:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            status["services"]["postgres"] = "ok"
        except Exception as e:
            status["services"]["postgres"] = f"error: {e}"
            status["status"] = "degraded"
    else:
        status["services"]["postgres"] = "disabled"

    # Redis (skipped in the lite profile)
    if settings.enable_redis:
        try:
            r = aioredis.from_url(settings.redis_url)
            await r.ping()
            await r.aclose()
            status["services"]["redis"] = "ok"
        except Exception as e:
            status["services"]["redis"] = f"error: {e}"
            status["status"] = "degraded"
    else:
        status["services"]["redis"] = "disabled"

    return status
