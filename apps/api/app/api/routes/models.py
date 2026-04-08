"""Model Registry API routes — dynamic model catalog management.

Provides model listing, health checks, deprecation management, and catalog updates.
Models can be managed via API without editing model_catalog.json.

No authentication required: model catalog is public information for provider selection.
Contains no user-specific data; read-only discovery endpoints.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ModelEntryResponse(BaseModel):
    id: str
    provider: str
    display_name: str
    latest_model_id: str = ""
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_tokens: int
    supports_tools: bool
    supports_vision: bool
    deprecated: bool
    successor: str | None = None
    tags: list[str] = []


class ModelListResponse(BaseModel):
    models: list[ModelEntryResponse]
    total: int
    catalog_version: str
    catalog_path: str


class ModeCatalogResponse(BaseModel):
    quality: list[str]
    speed: list[str]
    cost: list[str]
    free: list[str]
    subscription: list[str]


class ProviderHealthResponse(BaseModel):
    provider: str
    available: bool
    available_models: list[str]
    error: str | None = None


class AllProvidersHealthResponse(BaseModel):
    providers: list[ProviderHealthResponse]


class DeprecateRequest(BaseModel):
    model_id: str = Field(..., description="Model ID to deprecate")
    successor: str | None = Field(None, description="Successor model ID")


class UpdateCostRequest(BaseModel):
    model_id: str
    cost_per_1k_input: float
    cost_per_1k_output: float


class ReloadResponse(BaseModel):
    success: bool
    model_count: int
    catalog_version: str
    message: str


class DeprecatedModelsResponse(BaseModel):
    models: list[ModelEntryResponse]
    total: int


class DeprecateResponse(BaseModel):
    model_id: str
    deprecated: bool
    successor: str | None = None
    message: str


class UpdateCostResponse(BaseModel):
    model_id: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    message: str


class RemoveModelResponse(BaseModel):
    model_id: str
    message: str


class AutoUpdateResponse(BaseModel):
    success: bool
    model_count: int
    catalog_version: str
    auto_discovered_models: list = []
    rss_pipeline: dict = {}
    message: str


class UpdateVersionResponse(BaseModel):
    family_id: str
    new_model_id: str
    message: str


class AddModelRequest(BaseModel):
    """Register a custom model that is not in the default catalog."""

    id: str = Field(
        ...,
        description="Family ID (e.g. 'mistral/mistral-large' or 'custom/my-model')",
    )
    provider: str = Field(..., description="Provider name (e.g. 'openrouter', 'ollama')")
    display_name: str = Field(..., description="Human-readable display name")
    latest_model_id: str = Field(
        "",
        description="Actual model ID for API calls (e.g. 'mistral-large-latest')",
    )
    cost_per_1k_input: float = Field(0.0, description="Cost per 1K input tokens (USD)")
    cost_per_1k_output: float = Field(0.0, description="Cost per 1K output tokens (USD)")
    max_tokens: int = Field(4096, description="Maximum output tokens")
    supports_tools: bool = False
    supports_vision: bool = False
    tags: list[str] = Field(default_factory=list, description="Tags (e.g. ['quality', 'custom'])")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    provider: str | None = None,
    tag: str | None = None,
    include_deprecated: bool = False,
):
    """Get a list of all registered models.

    Filterable by provider and/or tag (e.g. ``tag=legacy`` to list older but
    still operational models).  Set ``include_deprecated=true`` to include
    deprecated models in the response.
    """
    from app.providers.model_registry import get_model_registry

    registry = get_model_registry()
    models = registry.list_models(
        provider=provider,
        include_deprecated=include_deprecated,
        tag=tag,
    )

    return ModelListResponse(
        models=[
            ModelEntryResponse(
                id=m.id,
                provider=m.provider,
                display_name=m.display_name,
                latest_model_id=m.latest_model_id,
                cost_per_1k_input=m.cost_per_1k_input,
                cost_per_1k_output=m.cost_per_1k_output,
                max_tokens=m.max_tokens,
                supports_tools=m.supports_tools,
                supports_vision=m.supports_vision,
                deprecated=m.deprecated,
                successor=m.successor,
                tags=m.tags,
            )
            for m in models
        ],
        total=len(models),
        catalog_version=registry.catalog_version,
        catalog_path=str(registry.catalog_path),
    )


@router.get("/models/modes", response_model=ModeCatalogResponse)
async def get_mode_catalog():
    """Get model catalog by execution mode."""
    from app.providers.model_registry import get_model_registry

    registry = get_model_registry()
    return ModeCatalogResponse(
        quality=registry.get_models_for_mode("quality"),
        speed=registry.get_models_for_mode("speed"),
        cost=registry.get_models_for_mode("cost"),
        free=registry.get_models_for_mode("free"),
        subscription=registry.get_models_for_mode("subscription"),
    )


@router.get("/models/health", response_model=AllProvidersHealthResponse)
async def check_all_providers_health():
    """Batch check availability of all providers."""
    from app.providers.model_registry import get_model_registry

    registry = get_model_registry()
    health = await registry.check_all_providers()

    return AllProvidersHealthResponse(
        providers=[
            ProviderHealthResponse(
                provider=s.provider,
                available=s.available,
                available_models=s.available_models,
                error=s.error,
            )
            for s in health.values()
        ]
    )


@router.get("/models/health/{provider}", response_model=ProviderHealthResponse)
async def check_provider_health(provider: str):
    """Check availability of a specific provider."""
    from app.providers.model_registry import get_model_registry

    registry = get_model_registry()
    status = await registry.check_provider_health(provider)

    return ProviderHealthResponse(
        provider=status.provider,
        available=status.available,
        available_models=status.available_models,
        error=status.error,
    )


@router.get("/models/deprecated", response_model=DeprecatedModelsResponse)
async def list_deprecated_models():
    """List deprecated models."""
    from app.providers.model_registry import get_model_registry

    registry = get_model_registry()
    deprecated = registry.get_deprecated_models()

    return DeprecatedModelsResponse(
        models=[
            ModelEntryResponse(
                id=m.id,
                provider=m.provider,
                display_name=m.display_name,
                latest_model_id=m.latest_model_id,
                cost_per_1k_input=m.cost_per_1k_input,
                cost_per_1k_output=m.cost_per_1k_output,
                max_tokens=m.max_tokens,
                supports_tools=m.supports_tools,
                supports_vision=m.supports_vision,
                deprecated=m.deprecated,
                successor=m.successor,
                tags=m.tags,
            )
            for m in deprecated
        ],
        total=len(deprecated),
    )


@router.post("/models/deprecate", response_model=DeprecateResponse)
async def deprecate_model(req: DeprecateRequest):
    """Mark a model as deprecated (optionally specify successor)."""
    from app.providers.model_registry import get_model_registry

    registry = get_model_registry()
    ok = registry.mark_deprecated(req.model_id, successor=req.successor)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Model not found: {req.model_id}")

    # Persist to catalog file
    registry.save_catalog()

    return {
        "model_id": req.model_id,
        "deprecated": True,
        "successor": req.successor,
        "message": f"Model {req.model_id} marked as deprecated",
    }


@router.post("/models/update-cost", response_model=UpdateCostResponse)
async def update_model_cost(req: UpdateCostRequest):
    """Update model cost information."""
    from app.providers.model_registry import get_model_registry

    registry = get_model_registry()
    ok = registry.update_cost(req.model_id, req.cost_per_1k_input, req.cost_per_1k_output)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Model not found: {req.model_id}")

    registry.save_catalog()

    return {
        "model_id": req.model_id,
        "cost_per_1k_input": req.cost_per_1k_input,
        "cost_per_1k_output": req.cost_per_1k_output,
        "message": "Cost updated",
    }


@router.post("/models/reload", response_model=ReloadResponse)
async def reload_catalog():
    """Reload model_catalog.json and refresh the registry."""
    from app.providers.model_registry import reload_model_registry

    registry = reload_model_registry()

    return ReloadResponse(
        success=True,
        model_count=registry.model_count,
        catalog_version=registry.catalog_version,
        message="Model catalog reloaded successfully",
    )


@router.post("/models/add", response_model=ModelEntryResponse)
async def add_custom_model(req: AddModelRequest):
    """Register a custom LLM model not in the default catalog.

    Use this to add any model accessible via LiteLLM, OpenRouter, or a
    custom OpenAI-compatible endpoint.  The model is persisted to
    ``model_catalog.json`` and available immediately.

    Example: add ``mistral/mistral-large``, ``cohere/command-r-plus``,
    or a self-hosted model reachable through Ollama / vLLM.
    """
    from app.providers.model_registry import ModelEntry, get_model_registry

    registry = get_model_registry()

    if registry.get_model(req.id) is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Model already exists: {req.id}. Use update-cost or update-version instead.",
        )

    entry = ModelEntry(
        id=req.id,
        provider=req.provider,
        display_name=req.display_name,
        latest_model_id=req.latest_model_id or req.id,
        cost_per_1k_input=req.cost_per_1k_input,
        cost_per_1k_output=req.cost_per_1k_output,
        max_tokens=req.max_tokens,
        supports_tools=req.supports_tools,
        supports_vision=req.supports_vision,
        tags=req.tags,
    )
    registry.add_model(entry)
    registry.save_catalog()

    return ModelEntryResponse(
        id=entry.id,
        provider=entry.provider,
        display_name=entry.display_name,
        latest_model_id=entry.latest_model_id,
        cost_per_1k_input=entry.cost_per_1k_input,
        cost_per_1k_output=entry.cost_per_1k_output,
        max_tokens=entry.max_tokens,
        supports_tools=entry.supports_tools,
        supports_vision=entry.supports_vision,
        deprecated=entry.deprecated,
        successor=entry.successor,
        tags=entry.tags,
    )


@router.delete("/models/{model_id}", response_model=RemoveModelResponse)
async def remove_custom_model(model_id: str):
    """Remove a custom model from the catalog.

    Only user-added (custom/legacy) models should be removed.
    Built-in models can be deprecated instead.
    """
    from app.providers.model_registry import get_model_registry

    registry = get_model_registry()
    ok = registry.remove_model(model_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

    registry.save_catalog()

    return {"model_id": model_id, "message": "Model removed from catalog"}


@router.post("/models/auto-update", response_model=AutoUpdateResponse)
async def auto_update_models():
    """Detect model updates from RSS/ToS pipeline and auto-update the catalog.

    Automatically updates AI models without users touching any files.
    Checks provider RSS feeds and detects new models, deprecations, and price changes.
    Also auto-detects Ollama local models and adds them to the catalog.
    """
    from app.integrations.rss_tos_monitor import rss_tos_monitor
    from app.providers.model_registry import get_model_registry

    registry = get_model_registry()

    # 1. Auto-check and update model availability from provider APIs
    refreshed = await registry.refresh_catalog()

    # 2. Detect and auto-apply external changes via RSS/ToS pipeline
    pipeline_result = await rss_tos_monitor.check_and_auto_update()

    return {
        "success": True,
        "model_count": registry.model_count,
        "catalog_version": registry.catalog_version,
        "auto_discovered_models": refreshed,
        "rss_pipeline": pipeline_result,
        "message": "Model catalog auto-updated successfully",
    }


@router.post("/models/update-version", response_model=UpdateVersionResponse)
async def update_model_version(
    family_id: str,
    new_model_id: str,
):
    """Update latest_model_id for a specific model (no file editing needed via API).

    Example: Update latest_model_id of anthropic/claude-opus to claude-opus-4-7
    """
    from app.providers.model_registry import get_model_registry

    registry = get_model_registry()
    ok = registry.update_latest_model_id(family_id, new_model_id)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail=f"Model family not found: {family_id}",
        )

    return {
        "family_id": family_id,
        "new_model_id": new_model_id,
        "message": f"Model {family_id} updated to {new_model_id}",
    }
