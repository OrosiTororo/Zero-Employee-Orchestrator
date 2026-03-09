"""Application configuration using pydantic-settings."""

import logging
import warnings

from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULT_KEYS = frozenset(
    {
        "change-me-in-production",
        "change-this-to-a-random-secret-key",
    }
)

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Project
    PROJECT_NAME: str = "Zero-Employee Orchestrator"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "CHANGE-ME-in-production"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./zero_employee_orchestrator.db"

    # LLM Providers (all optional — configure at least one to enable AI execution)
    OPENROUTER_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # g4f (subscription/no-API-key mode)
    # When true, g4f is loaded at startup enabling free AI access without API keys.
    USE_G4F: bool = True

    # Default execution mode: quality | speed | cost | free | subscription
    DEFAULT_EXECUTION_MODE: str = "quality"


settings = Settings()

# ---------------------------------------------------------------------------
# Startup safety check: reject insecure defaults in production (DEBUG=false)
# ---------------------------------------------------------------------------
if settings.SECRET_KEY.lower() in _INSECURE_DEFAULT_KEYS:
    if settings.DEBUG:
        warnings.warn(
            "SECRET_KEY is set to an insecure default. "
            "Set a strong random value before deploying to production.",
            UserWarning,
            stacklevel=1,
        )
    else:
        raise RuntimeError(
            "SECRET_KEY is still set to an insecure default value. "
            "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\" "
            "and set it in your .env file or environment variables. "
            "If this is intentional for local development, set DEBUG=true."
        )
