from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from core.config import settings
from core.logging import setup_logging
from api import health, token, chat, ingest, voice, auth, history, feedback

setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", service="voice-ai-api")
    yield
    logger.info("shutdown", service="voice-ai-api")


app = FastAPI(
    title="Dialo Customer Service API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router,    prefix="/api")
app.include_router(token.router,     prefix="/api",       tags=["livekit"])
app.include_router(chat.router,      prefix="/api",       tags=["chat"])
app.include_router(ingest.router,    prefix="/api",       tags=["rag"])
app.include_router(voice.router,     prefix="/api",       tags=["voice"])
app.include_router(auth.router,      prefix="/api",       tags=["auth"])
app.include_router(history.router,   prefix="/api",       tags=["history"])
app.include_router(feedback.router,  prefix="/api",       tags=["feedback"])
