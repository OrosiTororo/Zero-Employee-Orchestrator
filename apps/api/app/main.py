"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.api.routes import api_router

# Ensure all models are imported so Base.metadata is populated.
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Create database tables on startup (dev convenience)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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


@app.get("/healthz", tags=["health"])
async def health_check():
    """Liveness / readiness probe."""
    return {"status": "ok"}


@app.get("/readyz", tags=["health"])
async def readiness_check():
    """Readiness probe."""
    return {"status": "ok"}
