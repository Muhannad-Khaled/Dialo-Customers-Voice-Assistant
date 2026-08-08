"""
LangGraph Agent — orchestrates Retrieve → Generate → Respond workflow.
State holds query, retrieved context, conversation history, and the final answer.
"""

from typing import TypedDict, Annotated
import operator
import json
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.messages import messages_from_dict, messages_to_dict
from rag.retriever import retrieve
from agent.prompts import build_system_prompt
from core.config import settings
from db.crud import get_messages, persist_turn
from db.session import AsyncSessionLocal
import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger()


def _extract_text(content) -> str:
    """LangChain 1.x may return message content as a list of content blocks
    (e.g. [{'type': 'text', 'text': '...'}]) instead of a plain string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)

# ─── State ────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    query: str
    session_id: str
    language: str  # "en" | "ar" — drives the reply-language directive in the prompt
    history: Annotated[list, operator.add]  # accumulated messages
    context: str
    sources: list[str]
    answer: str


# ─── Nodes ────────────────────────────────────────────────────────────────────

async def node_retrieve(state: AgentState) -> dict:
    chunks = await retrieve(state["query"], top_k=5)
    context = "\n\n---\n".join(c["text"] for c in chunks)
    sources = list({c["source"] for c in chunks})
    logger.info("retrieve", session=state["session_id"], chunks=len(chunks))
    return {"context": context, "sources": sources}


async def node_generate(state: AgentState) -> dict:
    llm = ChatGoogleGenerativeAI(
        # Pinned to an explicit model (NOT a `-latest` alias): the alias resolved
        # to preview gemini-3.6-flash, capped at only 20 free requests/day, which
        # exhausted immediately. On this key the gemini-2.5-* models return 404
        # ("not available to new users") and 2.0-flash is also over quota; the
        # gemini-3.5-flash-lite model is callable with a larger free daily quota
        # (lite variant). Bump to "gemini-3.5-flash" for higher quality if quota
        # allows, or enable billing on the API key to lift the free-tier caps.
        model="gemini-3.5-flash-lite",
        google_api_key=settings.gemini_api_key,
        temperature=0.3,
    )
    system = build_system_prompt(state["context"], state.get("language", "en"))
    messages = [SystemMessage(content=system)] + state["history"] + [HumanMessage(content=state["query"])]
    response = await llm.ainvoke(messages)
    answer = _extract_text(response.content)
    logger.info("generate", session=state["session_id"], answer_len=len(answer))
    return {
        "answer": answer,
        "history": [HumanMessage(content=state["query"]), response],
    }


# ─── Graph ────────────────────────────────────────────────────────────────────

def _build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("retrieve", node_retrieve)
    graph.add_node("generate", node_generate)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


_agent = _build_graph()

# ─── Session memory (Redis, shared by API + agent worker) ─────────────────────
# Short-term conversation history lives in Redis so it survives restarts and is
# shared across the FastAPI process and the LiveKit agent worker (both call
# run_agent). If Redis is unavailable we degrade to a per-process dict.
_HISTORY_TTL_SECONDS = 3600
_MAX_MESSAGES = 20  # last 10 turns

_redis: aioredis.Redis | None = None
_fallback_histories: dict[str, list] = {}


def _get_redis() -> aioredis.Redis | None:
    global _redis
    if not settings.enable_redis:
        return None  # use in-process fallback; don't attempt a doomed connection
    if _redis is None:
        try:
            _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        except Exception as e:  # noqa: BLE001
            logger.warning("redis_init_failed", error=str(e))
            return None
    return _redis


async def _load_history_from_db(session_id: str) -> list:
    """Rehydrate conversation memory from the durable Postgres transcript.

    Redis is short-term (1h TTL, 20-msg cap); Postgres keeps every turn forever.
    Reading it back here is what lets the agent recall a conversation after the
    Redis entry has expired or been flushed — i.e. across long gaps and restarts.
    """
    if not settings.enable_postgres:
        return []
    try:
        async with AsyncSessionLocal() as db:
            rows = await get_messages(db, session_id)
    except Exception as e:  # noqa: BLE001 — memory rehydration must never break a call
        logger.warning("db_load_history_failed", session=session_id, error=str(e))
        return []
    messages: list = []
    for m in rows[-_MAX_MESSAGES:]:  # cap context to the most recent turns
        if m.role == "user":
            messages.append(HumanMessage(content=m.content))
        else:
            messages.append(AIMessage(content=m.content))
    return messages


async def _load_history(session_id: str) -> list:
    key = f"session:{session_id}"
    client = _get_redis()
    if client is not None:
        try:
            raw = await client.get(key)
            if raw:
                return messages_from_dict(json.loads(raw))
        except Exception as e:  # noqa: BLE001
            logger.warning("redis_load_failed", session=session_id, error=str(e))

    # Redis is empty or unavailable for this session — fall back to the durable
    # Postgres transcript so memory survives the 1h Redis TTL and container
    # restarts. Warm Redis on a hit so the next turn is a fast cache read.
    history = await _load_history_from_db(session_id)
    if history:
        if client is not None:
            await _save_history(session_id, history)
        return history

    return _fallback_histories.get(session_id, [])


async def _save_history(session_id: str, messages: list) -> None:
    trimmed = messages[-_MAX_MESSAGES:]  # keep the LAST N messages (most recent turns)
    key = f"session:{session_id}"
    client = _get_redis()
    if client is not None:
        try:
            await client.set(key, json.dumps(messages_to_dict(trimmed)), ex=_HISTORY_TTL_SECONDS)
            return
        except Exception as e:  # noqa: BLE001
            logger.warning("redis_save_failed", session=session_id, error=str(e))
    _fallback_histories[session_id] = trimmed


# Spoken fallbacks when a turn fails — kept in the reply language so an Arabic call
# never suddenly answers in English.
_QUOTA_FALLBACK = {
    "en": ("I'm getting a lot of requests right now and hit my rate limit. "
           "Please try again in a minute."),
    "ar": "فيه ضغط كبير دلوقتي ووصلت للحد المسموح. جرّب تاني بعد دقيقة لو سمحت.",
}
_ERROR_FALLBACK = {
    "en": "Sorry, I ran into a problem answering that. Could you try again?",
    "ar": "معلش، حصلت مشكلة وأنا برد. ممكن تجرّب تاني؟",
}


async def run_agent(query: str, session_id: str, language: str = "en") -> dict:
    lang = language if language in ("en", "ar") else "en"
    history = await _load_history(session_id)
    initial_state: AgentState = {
        "query": query,
        "session_id": session_id,
        "language": lang,
        "history": history,
        "context": "",
        "sources": [],
        "answer": "",
    }
    try:
        result = await _agent.ainvoke(initial_state)
    except Exception as e:  # noqa: BLE001 — the agent must always speak, never go silent
        msg = str(e)
        if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
            logger.warning("llm_quota_exceeded", session=session_id)
            answer = _QUOTA_FALLBACK[lang]
        else:
            logger.error("run_agent_failed", session=session_id, error=msg)
            answer = _ERROR_FALLBACK[lang]
        # Speak a graceful message instead of failing the turn silently. We skip
        # history/persistence here since no real assistant turn was produced.
        return {"answer": answer, "sources": []}
    await _save_history(session_id, result["history"])
    # Durable history for /api/history (best-effort; never breaks the call).
    if settings.enable_postgres:
        await persist_turn(session_id, query, result["answer"], result.get("sources"))
    return {"answer": result["answer"], "sources": result["sources"]}
