"""Model Registry API routes — モデルカタログの動的管理.

モデルの一覧・ヘルスチェック・廃止管理・カタログ更新を提供する。
model_catalog.json を編集せずに API 経由でモデル管理が可能。

認証不要: モデルカタログはプロバイダー選択のための公開情報。
ユーザー固有データを含まず、読み取り専用の発見用エンドポイント。
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
    model_id: str = Field(..., description="廃止するモデルID")
    successor: str | None = Field(None, description="後継モデルID")


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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    provider: str | None = None,
    include_deprecated: bool = False,
):
    """全登録モデルの一覧を取得.

    provider パラメータで特定プロバイダーのモデルのみにフィルタ可能。
    """
    from app.providers.model_registry import get_model_registry

    registry = get_model_registry()
    models = registry.list_models(provider=provider, include_deprecated=include_deprecated)

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
    """実行モード別のモデルカタログを取得."""
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
    """全プロバイダーの可用性を一括チェック."""
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
    """特定プロバイダーの可用性をチェック."""
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
    """廃止済みモデルの一覧."""
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


@router.post("/models/deprecate")
async def deprecate_model(req: DeprecateRequest):
    """モデルを廃止としてマーク（後継モデルを指定可能）."""
    from app.providers.model_registry import get_model_registry

    registry = get_model_registry()
    ok = registry.mark_deprecated(req.model_id, successor=req.successor)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Model not found: {req.model_id}")

    # カタログファイルに永続化
    registry.save_catalog()

    return {
        "model_id": req.model_id,
        "deprecated": True,
        "successor": req.successor,
        "message": f"Model {req.model_id} marked as deprecated",
    }


@router.post("/models/update-cost")
async def update_model_cost(req: UpdateCostRequest):
    """モデルのコスト情報を更新."""
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
    """model_catalog.json を再読み込みしてレジストリをリフレッシュ."""
    from app.providers.model_registry import reload_model_registry

    registry = reload_model_registry()

    return ReloadResponse(
        success=True,
        model_count=registry.model_count,
        catalog_version=registry.catalog_version,
        message="Model catalog reloaded successfully",
    )


@router.post("/models/auto-update")
async def auto_update_models():
    """RSS/ToS パイプラインからモデル更新を検出し、カタログを自動更新する.

    ユーザーがファイルを一切触ることなく AI モデル更新を自動で行う。
    プロバイダーの RSS フィードをチェックし、新モデル・廃止・価格変更を検出。
    Ollama のローカルモデルも自動検出してカタログに追加する。
    """
    from app.integrations.rss_tos_monitor import rss_tos_monitor
    from app.providers.model_registry import get_model_registry

    registry = get_model_registry()

    # 1. プロバイダー API からモデル可用性を自動チェック・更新
    refreshed = await registry.refresh_catalog()

    # 2. RSS/ToS パイプラインで外部変更を検出・自動適用
    pipeline_result = await rss_tos_monitor.check_and_auto_update()

    return {
        "success": True,
        "model_count": registry.model_count,
        "catalog_version": registry.catalog_version,
        "auto_discovered_models": refreshed,
        "rss_pipeline": pipeline_result,
        "message": "Model catalog auto-updated successfully",
    }


@router.post("/models/update-version")
async def update_model_version(
    family_id: str,
    new_model_id: str,
):
    """特定モデルの latest_model_id を更新する（API 経由でファイル編集不要）.

    例: anthropic/claude-opus の latest_model_id を claude-opus-4-7 に更新
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
