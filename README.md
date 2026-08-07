# Dialo — Customer Service Assistant

> Dialo is a real-time voice AI customer service assistant powered by **Gemini 2.5 Flash**, **LiveKit**, **LangGraph**, and **LlamaIndex** — built entirely with a free/open-source stack.

## Architecture

Real-time voice runs through a server-side **LiveKit Agents worker** (`backend/agent_worker.py`)
that joins each room, listens to the caller, and speaks back:

```
Browser ⇄ LiveKit room ⇄ Agent worker
                             ├─ Silero VAD → Faster-Whisper (STT)
                             ├─ LangGraph + RAG (LlamaIndex/Chroma + Gemini)
                             └─ Piper (TTS) → published back into the room
```

The REST endpoints (`/api/stt`, `/api/chat`, `/api/tts`) wrap the same components and
remain available as a development fallback (set `NEXT_PUBLIC_VOICE_MODE=rest`).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router) |
| Voice Transport | LiveKit |
| Backend | FastAPI |
| Agent | LangGraph |
| LLM | Gemini 2.5 Flash (free API) |
| RAG | LlamaIndex + ChromaDB |
| Embeddings | BAAI/bge-m3 |
| STT | Faster-Whisper |
| TTS | Piper |
| Database | PostgreSQL |
| Cache | Redis |
| Deployment | Docker Compose |

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY
```

### 2. Start all services

```bash
docker compose up -d
```

On startup the **backend** container automatically downloads the Piper voice model and
runs `alembic upgrade head`; the **agent** container downloads the Piper voice + Silero VAD
weights and starts the LiveKit worker. First boot is slower while models download
(cached in the `tts_models` volume afterwards).

Services started: `backend`, `agent` (LiveKit worker), `frontend`, `postgres`, `redis`,
`chromadb`, `livekit`.

### 3. Ingest the sample knowledge base

```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "file=@data/sample_faq.txt"
```

### 4. Open the app

Go to **http://localhost:3000**, enter your name, and click **Start Voice Session**.
Just start speaking — the agent listens continuously, answers from the knowledge base,
and speaks back. The transcript updates live.

---

## Development (without Docker)

**Backend API:**
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
# Start external services (postgres, redis, chromadb, livekit) separately,
# then apply migrations and run the API:
alembic upgrade head
uvicorn main:app --reload
```

**LiveKit agent worker** (separate process — the real-time voice pipeline):
```bash
cd backend
python scripts/download_piper_model.py   # once
python agent_worker.py download-files    # once (Silero VAD weights)
python agent_worker.py dev                # hot-reload against a --dev LiveKit server
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Service health check |
| POST | `/api/token` | Get LiveKit room token |
| POST | `/api/stt` | Audio → transcript |
| POST | `/api/tts` | Text → WAV audio |
| POST | `/api/chat` | RAG-grounded chat |
| POST | `/api/ingest` | Upload knowledge base doc |
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login → JWT |
| GET | `/api/history/{session_id}` | Conversation history |
| POST | `/api/feedback` | Thumbs up/down on a message |

---

## Load Testing

```bash
pip install locust
locust -f tests/locustfile.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 60s
```

---

## Environment Variables

See [`.env.example`](.env.example) for all required variables.

Key variables:
- `GEMINI_API_KEY` — your Gemini API key (required)
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` — LiveKit credentials
- `DATABASE_URL` — async Postgres DSN (`postgresql+asyncpg://…`)
- `REDIS_URL` — Redis DSN for short-term conversation memory
- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` — JWT auth
- `PIPER_VOICE` — TTS voice model name (default: `en_US-lessac-medium`)
- `WHISPER_MODEL` — STT model size: `tiny`, `base`, `small`, `medium` (default: `base`)
- `NEXT_PUBLIC_VOICE_MODE` — `agent` (real-time LiveKit, default) or `rest` (fallback loop)
- `CHROMA_PORT` — Chroma's **in-container** port `8000` (host is mapped to `8001`)

## Future Enhancements

- Human handoff escalation
- CRM integration (Salesforce, HubSpot)
- WhatsApp / Twilio / SIP support
- Multi-language models
- Analytics dashboard
