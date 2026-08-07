"""
LiveKit Agents worker — the CORE real-time voice pipeline.

Runs as its own process, registers with the LiveKit server, and is dispatched
into every room the frontend creates via /api/token (automatic dispatch — no
agent_name set). For each call it subscribes to the caller's mic and runs:

    caller audio --(Silero VAD)--> Groq Whisper STT --> LangGraph run_agent (RAG+Gemini)
                --> PiperTTS --> published back into the room

STT/LLM/TTS all reuse the existing backend code via thin adapters, so there is
no duplication with the REST endpoints (/api/stt, /api/chat, /api/tts), which
remain available as a development fallback.

Run:
    python agent_worker.py download-files   # fetch Silero VAD weights
    python agent_worker.py dev              # local hot-reload against `livekit --dev`
    python agent_worker.py start            # production

Reads LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET from the environment.
Verified against livekit-agents==1.6.7.
"""

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    ModelSettings,
    RoomInputOptions,
    RoomOutputOptions,
    cli,
)
from livekit.plugins import silero, groq

from livekit_agent.piper_tts_plugin import PiperTTS
from agent.graph import run_agent

GREETING = "Hi! I'm Dialo, your customer service assistant. How can I help you today?"


class CustomerServiceAgent(Agent):
    """Delegates the LLM step to the existing LangGraph RAG agent via llm_node."""

    def __init__(self, session_id: str) -> None:
        # instructions are unused: run_agent applies its own RAG system prompt.
        super().__init__(instructions="You are a helpful customer service assistant.")
        self._session_id = session_id

    async def llm_node(self, chat_ctx, tools, model_settings: ModelSettings):
        # Most recent user turn from the accumulated chat context.
        query = ""
        for item in reversed(chat_ctx.items):
            if getattr(item, "role", None) == "user":
                query = item.text_content or ""
                break

        result = await run_agent(query=query, session_id=self._session_id)
        # Yielding a plain string routes through transcription_node -> tts_node.
        yield result["answer"]


def prewarm(proc):
    # Load Silero VAD once per worker process (required: Whisper is non-streaming).
    proc.userdata["vad"] = silero.VAD.load()


# num_idle_processes=1: keep a single warm worker (prod default is 8, which would
# load the VAD/Piper/embedding models 8× and exhaust memory on small hosts).
# initialize_process_timeout raised to 60s: the worker subprocess imports the heavy
# llama-index/langchain stack, which can exceed the 10s default on modest hardware.
server = AgentServer(
    setup_fnc=prewarm,
    num_idle_processes=1,
    initialize_process_timeout=60.0,
)


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    await ctx.connect()  # default AutoSubscribe subscribes to the caller's audio

    # Memory is keyed on the caller's IDENTITY (e.g. "Muhannad"), not the room name.
    # This decouples the two concerns: each call can use a fresh, unique room (so the
    # agent is reliably dispatched on room creation — rejoining a lingering room does
    # NOT re-dispatch), while conversation memory (Redis + Postgres) follows the user
    # across calls/reconnects. NOTE: identity is client-supplied, so distinct users
    # sharing a name would share memory — fine for this demo; use an authenticated
    # user id here for production.
    participant = await ctx.wait_for_participant()
    session_id = participant.identity or ctx.room.name

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=groq.STT(model="whisper-large-v3-turbo"),  # reads GROQ_API_KEY from env
        # An llm MUST be set: the session only runs its reply pipeline (the task that
        # invokes Agent.llm_node) when `self.llm` is an llm.LLM instance — see
        # agent_activity.py `if self.llm is None: raise ... elif isinstance(self.llm,
        # llm.LLM): _pipeline_reply_task(...)`. Without it the user turn commits but no
        # reply is ever generated. CustomerServiceAgent.llm_node fully overrides
        # generation (routing to the LangGraph RAG agent), so this Groq LLM is only a
        # lightweight placeholder to enable the pipeline — it is never actually called.
        llm=groq.LLM(model="llama-3.1-8b-instant"),
        tts=PiperTTS(),
        # groq.STT is non-streaming, so LiveKit wraps it in a StreamAdapter that only
        # calls Groq AFTER VAD end-of-speech. turn_detection="stt" commits the turn
        # when the STT FINAL transcript arrives (not on a VAD timer that fires before
        # the slow Groq transcript returns), so the user's words always reach the LLM.
        turn_detection="stt",
        min_endpointing_delay=0.5,
        max_endpointing_delay=10.0,
    )

    await session.start(
        agent=CustomerServiceAgent(session_id=session_id),
        room=ctx.room,
        room_input_options=RoomInputOptions(),
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )

    # Deterministic opening line (bypasses run_agent so it isn't an empty query).
    await session.say(GREETING)


if __name__ == "__main__":
    cli.run_app(server)
