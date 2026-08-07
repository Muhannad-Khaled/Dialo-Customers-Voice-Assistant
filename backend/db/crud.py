"""
Small persistence helpers shared by the API routers and the agent.

`persist_turn` is called from run_agent (agent/graph.py), which both the REST
/api/chat path and the LiveKit agent worker funnel through — so conversation
history is captured for both pipelines. It opens its own session and never
raises into the caller (a DB hiccup must not break a live voice call).
"""

import json

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Message, Session
from db.session import AsyncSessionLocal

logger = structlog.get_logger()


async def _ensure_session(db: AsyncSession, session_id: str) -> None:
    # Idempotent upsert so message inserts never fail on a missing FK.
    stmt = pg_insert(Session).values(id=session_id).on_conflict_do_nothing(index_elements=["id"])
    await db.execute(stmt)


async def get_messages(db: AsyncSession, session_id: str) -> list[Message]:
    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at, Message.id)
    )
    return list(result.scalars().all())


async def persist_turn(
    session_id: str,
    user_text: str,
    assistant_text: str,
    sources: list[str] | None = None,
) -> None:
    """Best-effort write of one user+assistant turn. Swallows all DB errors."""
    try:
        async with AsyncSessionLocal() as db:
            await _ensure_session(db, session_id)
            db.add(Message(session_id=session_id, role="user", content=user_text))
            db.add(
                Message(
                    session_id=session_id,
                    role="assistant",
                    content=assistant_text,
                    sources=json.dumps(sources) if sources else None,
                )
            )
            await db.commit()
    except Exception as e:  # noqa: BLE001 — persistence must never break the call
        logger.warning("persist_turn_failed", session=session_id, error=str(e))
