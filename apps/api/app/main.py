"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.database import Base, engine
from app.api.routes import api_router
from app.api.ws.events import router as ws_router

# Ensure all models are imported so Base.metadata is populated.
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Create database tables on startup and initialize providers."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Register system-protected skills on startup
    try:
        from app.core.database import async_session_factory
        from app.services.skill_service import ensure_system_skills

        async with async_session_factory() as session:
            await ensure_system_skills(session)
            await session.commit()
            logger.info("System skills verified")
    except Exception as exc:
        logger.warning("System skills init failed (non-fatal): %s", exc)

    # Initialize Ollama provider (non-blocking, best-effort)
    try:
        from app.providers.ollama_provider import ollama_provider

        is_up = await ollama_provider.health_check()
        if is_up:
            models = await ollama_provider.list_models()
            logger.info("Ollama available with %d models", len(models))
        else:
            logger.info("Ollama not available (local mode disabled)")
    except Exception as exc:
        logger.debug("Ollama init check failed: %s", exc)

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# WebSocket routes
app.include_router(ws_router)


@app.get("/healthz", tags=["health"])
async def health_check():
    """Liveness / readiness probe."""
    return {"status": "ok"}


@app.get("/readyz", tags=["health"])
async def readiness_check():
    """Readiness probe."""
    return {"status": "ok"}
