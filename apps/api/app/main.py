"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

import app.models  # noqa: F401
import app.orchestration.agent_session  # noqa: F401
import app.orchestration.experience_memory  # noqa: F401
import app.orchestration.knowledge_store  # noqa: F401
import app.security.iam  # noqa: F401
from app.api.routes import api_router
from app.api.ws.browser_assist_ws import router as browser_assist_ws_router
from app.api.ws.events import router as ws_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.security.input_sanitization import InputSanitizationMiddleware
from app.security.security_headers import (
    RequestValidationMiddleware,
    SecurityHeadersMiddleware,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Create database tables on startup and initialize providers."""
    # Apply runtime config from ~/.zero-employee/config.json
    try:
        from app.core.config_manager import apply_runtime_config

        apply_runtime_config()
    except Exception as exc:
        logger.debug("Runtime config apply failed (non-fatal): %s", exc)

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

    # Initialize Sentry (best-effort)
    try:
        from app.integrations.sentry_integration import (
            create_sentry_integration,
        )

        if settings.SENTRY_DSN:
            create_sentry_integration(
                dsn=settings.SENTRY_DSN,
                environment="production" if not settings.DEBUG else "development",
            )
            logger.info("Sentry integration initialized")
    except Exception as exc:
        logger.debug("Sentry init failed (non-fatal): %s", exc)

    # Initialize MCP server
    try:
        from app.integrations.mcp_server import mcp_server

        logger.info("MCP server ready (%d tools)", len(mcp_server._tools))
    except Exception as exc:
        logger.debug("MCP init failed (non-fatal): %s", exc)

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

# Security headers — OWASP 推奨ヘッダーを全レスポンスに付与
app.add_middleware(SecurityHeadersMiddleware)

# Request validation — 不正リクエストの早期拒否
app.add_middleware(RequestValidationMiddleware)

# Input sanitization — プロンプトインジェクション・PII 自動検査
app.add_middleware(InputSanitizationMiddleware)

# CORS — allow_methods / allow_headers を明示的に制限
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)

# API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# WebSocket routes
app.include_router(ws_router)
app.include_router(browser_assist_ws_router)


@app.get("/healthz", tags=["health"])
async def health_check():
    """Liveness / readiness probe."""
    return {"status": "ok"}


@app.get("/readyz", tags=["health"])
async def readiness_check():
    """Readiness probe."""
    return {"status": "ok"}
