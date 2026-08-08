from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode
from typing import Annotated, List


class Settings(BaseSettings):
    # Gemini (LLM + embeddings)
    gemini_api_key: str = ""

    # Groq (Whisper STT — free API)
    groq_api_key: str = ""

    # Arabic TTS engine. English always uses Piper (offline); Arabic needs a
    # non-Piper voice (Piper has no Egyptian voice). Choose the engine here:
    #   "gemini" — reuses GEMINI_API_KEY, no new secret (default)
    #   "azure"  — dedicated ar-EG neural voice (needs azure_speech_* below)
    arabic_tts_provider: str = "gemini"

    # Gemini TTS (default Arabic engine) — reuses gemini_api_key. Note: the preview
    # TTS model may 404 on keys where gemini-2.5-* chat models are unavailable; if so
    # set arabic_tts_provider="azure".
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts"
    gemini_tts_voice: str = "Kore"

    # Azure Speech (fallback Arabic engine) — billed per character, Arabic turns only
    # (free tier 0.5M chars/month). Only needed when arabic_tts_provider="azure".
    azure_speech_key: str = ""
    azure_speech_region: str = ""  # e.g. "eastus"
    azure_tts_voice_ar: str = "ar-EG-SalmaNeural"  # true Egyptian voice

    # Default language when a call carries no explicit choice ("en" | "ar").
    default_language: str = "en"

    # LiveKit
    livekit_url: str = "ws://localhost:7880"
    livekit_api_key: str = "devkey"
    livekit_api_secret: str = "secret"

    # Database — set enable_postgres=false to skip all DB calls (8GB-lite profile).
    # Otherwise every request wastes ~8s on DNS lookups for an absent host.
    database_url: str = "postgresql+asyncpg://dialo:dialo_pass@postgres:5432/dialo_db"
    enable_postgres: bool = True

    # Redis — set enable_redis=false to use the in-process memory fallback instead.
    redis_url: str = "redis://redis:6379/0"
    enable_redis: bool = True

    # ChromaDB — port 8000 is the container's internal port (host maps 8001:8000).
    # For non-Docker dev, override with CHROMA_HOST=localhost CHROMA_PORT=8001.
    chroma_host: str = "chromadb"
    chroma_port: int = 8000

    # Auth
    secret_key: str = "changeme"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # CORS — accept a comma-separated string from the env (NoDecode skips the
    # default JSON parsing so "http://a,http://b" works, not just JSON arrays).
    cors_origins: Annotated[List[str], NoDecode] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # .env carries POSTGRES_*/BACKEND_PORT/etc. not modeled here


settings = Settings()
