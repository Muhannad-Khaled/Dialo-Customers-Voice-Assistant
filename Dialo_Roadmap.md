# Dialo — Customer Service Assistant Roadmap

## Goal

Build Dialo, a real-time voice AI customer service assistant using RAG with an
entirely free/open-source stack except the Gemini free API.

## Tech Stack

-   Frontend: Next.js
-   Voice Transport: LiveKit
-   Backend: FastAPI
-   Agent: LangGraph
-   LLM: Gemini 2.5 Flash (Free API)
-   RAG: LlamaIndex
-   Embeddings: BAAI/bge-m3
-   Vector DB: ChromaDB
-   STT: Faster-Whisper
-   TTS: Piper
-   Database: PostgreSQL
-   Cache: Redis
-   Deployment: Docker Compose

## Architecture

1.  User speaks through browser/mobile.
2.  LiveKit streams audio.
3.  Faster-Whisper transcribes speech.
4.  LangGraph orchestrates the workflow.
5.  LlamaIndex retrieves relevant chunks from ChromaDB.
6.  Retrieved context + user query are sent to Gemini.
7.  Gemini generates the answer.
8.  Piper converts text to speech.
9.  LiveKit streams audio back.

## Milestones

### Phase 1

-   [x] Create repository
-   [x] Configure Docker Compose
-   [x] Setup FastAPI
-   [x] Setup Next.js

### Phase 2

-   [x] Integrate LiveKit (server-side Agents worker)
-   [x] Audio streaming (real-time, agent subscribes to room audio)
-   [x] Session management (room-scoped, Redis-backed memory)

### Phase 3

-   [x] Document ingestion
-   [x] Chunking
-   [x] Embeddings (bge-m3, cached singleton)
-   [x] ChromaDB indexing

### Phase 4

-   [x] LangGraph workflow
-   [x] Gemini integration
-   [x] RAG prompt template
-   [x] Conversation memory (Redis + Postgres history)

### Phase 5

-   [x] Faster-Whisper (LiveKit STT adapter)
-   [x] Piper TTS (LiveKit TTS adapter)
-   [x] Streaming responses (agent output streams to the room)

### Phase 6

-   [x] Authentication (JWT + bcrypt)
-   [x] PostgreSQL
-   [x] Redis
-   [x] Conversation history (`/api/history`)
-   [x] Feedback (`/api/feedback`)

### Phase 7

-   [x] Docker deployment
-   [x] Logging (structlog)
-   [ ] Monitoring
-   [x] Load testing (Locust)

## Future Enhancements

-   Human handoff
-   CRM integration
-   WhatsApp
-   Twilio/SIP
-   Multi-language support
-   Analytics dashboard
