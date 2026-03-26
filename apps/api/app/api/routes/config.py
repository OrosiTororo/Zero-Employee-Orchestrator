"""Configuration management API — configure API keys and execution modes from within the app.

Instead of directly editing the .env file, settings can be changed via Web UI or API.
Configuration changes can only be made by authenticated users.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.routes.auth import get_current_user
from app.core.config_manager import (
    CONFIGURABLE_KEYS,
    delete_config_value,
    get_all_config,
    get_config_value,
    get_provider_status,
    set_config_value,
)
from app.models.user import User

router = APIRouter()


class ConfigUpdateRequest(BaseModel):
    key: str
    value: str


class ConfigBatchUpdateRequest(BaseModel):
    values: dict[str, str]


@router.get("/config")
async def list_config(user: User = Depends(get_current_user)):
    """Get all configuration values (sensitive values are masked).

    Returns a dict of all configurable keys with their current values,
    source (environment, config_file, default, unset), and metadata.
    """
    return {
        "config": get_all_config(),
        "execution_mode": get_config_value("DEFAULT_EXECUTION_MODE"),
    }


@router.get("/config/providers")
async def list_providers(user: User = Depends(get_current_user)):
    """Get connection status for each LLM provider."""
    return {
        "providers": get_provider_status(),
        "execution_mode": get_config_value("DEFAULT_EXECUTION_MODE"),
    }


@router.put("/config")
async def update_config(
    req: ConfigUpdateRequest,
    user: User = Depends(get_current_user),
):
    """Update a configuration value.

    Values are saved to ~/.zero-employee/config.json and
    immediately applied to the running application.
    """
    if req.key not in CONFIGURABLE_KEYS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown config key: {req.key}. "
            f"Available keys: {', '.join(sorted(CONFIGURABLE_KEYS))}",
        )
    set_config_value(req.key, req.value)
    return {"updated": True, "key": req.key}


@router.put("/config/batch")
async def update_config_batch(
    req: ConfigBatchUpdateRequest,
    user: User = Depends(get_current_user),
):
    """Batch update multiple configuration values."""
    updated = []
    errors = []
    for key, value in req.values.items():
        if key not in CONFIGURABLE_KEYS:
            errors.append(f"Unknown key: {key}")
            continue
        set_config_value(key, value)
        updated.append(key)

    if errors:
        return {"updated": updated, "errors": errors, "partial": True}
    return {"updated": updated, "errors": [], "partial": False}


@router.delete("/config/{key}")
async def remove_config(key: str, user: User = Depends(get_current_user)):
    """Remove a runtime configuration value (revert to default)."""
    if key not in CONFIGURABLE_KEYS:
        raise HTTPException(status_code=400, detail=f"Unknown config key: {key}")
    removed = delete_config_value(key)
    return {"removed": removed, "key": key}


@router.get("/config/keys")
async def list_configurable_keys(user: User = Depends(get_current_user)):
    """Return the list of configurable keys and their metadata."""
    return {"keys": CONFIGURABLE_KEYS}
