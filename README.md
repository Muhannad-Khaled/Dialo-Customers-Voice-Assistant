# Dialo — Customer Service Assistant

> Dialo is a **bilingual** (English + Egyptian Arabic) real-time voice AI customer service
> assistant powered by **Gemini**, **LiveKit**, **LangGraph**, and **LlamaIndex** — built
> largely on a free-API stack.

## Architecture

Real-time voice runs through a server-side **LiveKit Agents worker** (`backend/agent_worker.py`)
that joins each room, listens to the caller, and speaks back. The pipeline is picked per
call from the caller's chosen language (see [Languages](#languages)):

```
Browser ⇄ LiveKit room ⇄ Agent worker
                             ├─ Silero VAD → Groq Whisper (STT, language en|ar)
                             ├─ LangGraph + RAG (LlamaIndex/Chroma + Gemini)  → reply in the caller's language
                             └─ TTS → published back into the room
                                  ├─ English  → Piper (offline)
                                  └─ Arabic   → Gemini TTS (default) or Azure ar-EG
```

The REST endpoints (`/api/stt`, `/api/chat`, `/api/tts`) wrap the same components and
remain available as a development fallback (set `NEXT_PUBLIC_VOICE_MODE=rest`; English-only).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router) |
| Voice Transport | LiveKit |
| Backend | FastAPI |
| Agent | LangGraph |
| LLM | Gemini (free API) |
| RAG | LlamaIndex + ChromaDB |
| Embeddings | Gemini embeddings (free API) |
| STT | Groq Whisper (`whisper-large-v3-turbo`, per-call `en`/`ar`) |
| TTS (English) | Piper (offline) |
| TTS (Egyptian Arabic) | Gemini TTS (default) · Azure `ar-EG` (fallback) |
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
`chromadb`. Voice transport uses **LiveKit Cloud** (set `LIVEKIT_URL`/keys in `.env`); the
optional local `livekit` container is commented out in `docker-compose.yml`.

### 3. Ingest the sample knowledge base

```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "file=@data/sample_faq.txt"
```

### 4. Open the app

Go to **http://localhost:3000**, enter your name, pick a **Language** (English or
العربية مصري), and click **Start Voice Session**. Just start speaking — the agent listens
continuously, answers from the knowledge base in your language, and speaks back. The
transcript updates live (right-to-left for Arabic).

---

## Languages

Dialo is bilingual: **English** and **Egyptian Arabic**. The caller picks a language on the
join screen; it is carried to the agent as a LiveKit **participant attribute** on the token
and drives the whole pipeline per call:

- **STT** — Groq Whisper is forced to `en` or `ar` so speech isn't mis-detected.
- **LLM** — the RAG system prompt injects a reply-language directive; Arabic replies come
  back in Egyptian dialect (اللهجة المصرية). The knowledge base can stay English — Gemini
  translates facts on the fly.
- **TTS** — English uses **Piper** (offline). Arabic uses a non-Piper voice because Piper
  has no Egyptian voice, selected by `ARABIC_TTS_PROVIDER`:
  - `gemini` (default) — reuses `GEMINI_API_KEY`, no extra secret. **Caveat:** the free-tier
    Gemini TTS model is limited to **~3 requests/minute**, so a sustained conversation can
    hit `429 RESOURCE_EXHAUSTED` and drop a spoken reply. Enable billing to lift it.
  - `azure` — Azure Speech `ar-EG-SalmaNeural`, a dedicated Egyptian neural voice. Needs
    `AZURE_SPEECH_KEY` / `AZURE_SPEECH_REGION` (free tier: 0.5M chars/month, no tight
    per-minute cap). Recommended for smooth Arabic conversation.

Conversation memory is keyed on the caller's name (identity), independent of language, so a
user is remembered across calls in either language.

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
- `GEMINI_API_KEY` — your Gemini API key (required; also powers Gemini TTS by default)
- `GROQ_API_KEY` — Groq API key for Whisper STT (required)
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` — LiveKit credentials
- `DATABASE_URL` — async Postgres DSN (`postgresql+asyncpg://…`)
- `REDIS_URL` — Redis DSN for short-term conversation memory
- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` — JWT auth
- `DEFAULT_LANGUAGE` — reply language when a call sends none: `en` or `ar` (default: `en`)
- `PIPER_VOICE` — English TTS voice model name (default: `en_US-lessac-medium`)
- `ARABIC_TTS_PROVIDER` — Egyptian-Arabic TTS engine: `gemini` (default) or `azure`
- `GEMINI_TTS_MODEL`, `GEMINI_TTS_VOICE` — Gemini TTS model/voice (default `gemini-2.5-flash-preview-tts` / `Kore`)
- `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, `AZURE_TTS_VOICE_AR` — only needed when `ARABIC_TTS_PROVIDER=azure`
- `NEXT_PUBLIC_VOICE_MODE` — `agent` (real-time LiveKit, default) or `rest` (fallback loop, English-only)
- `CHROMA_PORT` — Chroma's **in-container** port `8000` (host is mapped to `8001`)

## Future Enhancements

- Human handoff escalation
- CRM integration (Salesforce, HubSpot)
- WhatsApp / Twilio / SIP support
- More languages (English + Egyptian Arabic today) + a native Arabic knowledge base
- Analytics dashboard
