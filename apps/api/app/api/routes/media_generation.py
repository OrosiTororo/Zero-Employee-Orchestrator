"""メディア生成 API エンドポイント.

画像・動画・音声・音楽・3D の生成 API。
すべての操作はデータ保護ポリシーと承認ゲートを経由する。
動的プロバイダー登録・削除に対応。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.integrations.media_generation import (
    GenerationRequest,
    MediaProviderEntry,
    MediaType,
    media_generation_service,
    media_provider_registry,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["media-generation"])

# ---------- Valid media types ----------

_VALID_MEDIA_TYPES = {t.value for t in MediaType}


def _validate_media_type(media_type: str) -> str:
    if media_type not in _VALID_MEDIA_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid media_type: {media_type}. Valid: {sorted(_VALID_MEDIA_TYPES)}",
        )
    return media_type


# ---------- Request / Response schemas ----------


class GenerateRequest(BaseModel):
    """メディア生成リクエスト."""

    prompt: str = Field(..., min_length=1, max_length=10000)
    media_type: str = Field(..., description="image | video | audio | music | 3d")
    provider: str = Field(..., description="Provider ID (e.g. openai_dalle, meshy_3d)")
    user_id: str = ""
    negative_prompt: str = ""
    language: str = "ja"
    parameters: dict = Field(default_factory=dict)


class GenerateResponse(BaseModel):
    """メディア生成レスポンス."""

    request_id: str
    status: str
    media_type: str
    provider: str
    output_url: str = ""
    error: str = ""
    cost_usd: float = 0.0


class MediaProviderRegisterRequest(BaseModel):
    """プロバイダー登録リクエスト."""

    id: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9_]+$")
    media_type: str = Field(..., description="image | video | audio | music | 3d")
    api_base: str = Field(..., min_length=1)
    env_key: str = Field(..., min_length=1)
    models: list[str] = Field(default_factory=list)
    default_model: str = ""
    max_prompt_length: int = Field(default=5000, ge=1)
    cost_per_generation: float = Field(default=0.0, ge=0)
    extra_config: dict = Field(default_factory=dict)


class MediaProviderResponse(BaseModel):
    """プロバイダーレスポンス."""

    id: str
    media_type: str
    models: list[str]
    default_model: str
    available: bool
    builtin: bool
    cost_per_generation: float


# ---------- Provider listing ----------


@router.get("/providers")
async def list_providers() -> list[dict]:
    """利用可能なメディア生成プロバイダー一覧（ビルトイン＋ユーザー登録）."""
    return media_provider_registry.get_available()


@router.get("/providers/{media_type}")
async def list_providers_by_type(media_type: str) -> list[dict]:
    """メディアタイプ別のプロバイダー一覧."""
    _validate_media_type(media_type)
    return media_provider_registry.get_available(media_type)


# ---------- Provider registration ----------


@router.post("/providers", status_code=201)
async def register_provider(
    req: MediaProviderRegisterRequest,
    user: User = Depends(get_current_user),
) -> dict:
    """新規メディアプロバイダーを登録する.

    3D ツールや新しい画像生成サービスなど、ビルトインにないプロバイダーを追加可能。
    ビルトインプロバイダーの上書きは不可。
    """
    _validate_media_type(req.media_type)

    entry = MediaProviderEntry(
        id=req.id,
        media_type=req.media_type,
        api_base=req.api_base,
        env_key=req.env_key,
        models=req.models,
        default_model=req.default_model or (req.models[0] if req.models else ""),
        max_prompt_length=req.max_prompt_length,
        cost_per_generation=req.cost_per_generation,
        extra_config=req.extra_config,
        builtin=False,
    )

    try:
        media_provider_registry.register(entry)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    logger.info("Media provider registered via API: %s by user %s", req.id, user.id)
    return {"status": "registered", "provider": entry.to_dict()}


@router.delete("/providers/{provider_id}")
async def unregister_provider(
    provider_id: str,
    user: User = Depends(get_current_user),
) -> dict:
    """ユーザー登録プロバイダーを削除する（ビルトインは削除不可）."""
    try:
        removed = media_provider_registry.unregister(provider_id)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not removed:
        raise HTTPException(status_code=404, detail=f"Provider not found: {provider_id}")

    logger.info("Media provider unregistered via API: %s by user %s", provider_id, user.id)
    return {"status": "unregistered", "provider_id": provider_id}


# ---------- Generation ----------


@router.post("/generate", response_model=GenerateResponse)
async def generate_media(
    req: GenerateRequest, user: User = Depends(get_current_user)
) -> GenerateResponse:
    """メディアを生成する（ビルトイン＋ユーザー登録プロバイダー対応）."""
    _validate_media_type(req.media_type)

    # プロバイダーの存在確認（enum ではなくレジストリから解決）
    if not media_provider_registry.get(req.provider):
        available = [e.id for e in media_provider_registry.list_all()]
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {req.provider}. Available: {available}",
        )

    request = GenerationRequest(
        prompt=req.prompt,
        media_type=req.media_type,
        provider=req.provider,
        user_id=req.user_id,
        parameters=req.parameters,
        negative_prompt=req.negative_prompt,
        language=req.language,
    )

    result = await media_generation_service.generate(request)

    return GenerateResponse(
        request_id=result.request_id,
        status=result.status.value,
        media_type=result.media_type,
        provider=result.provider,
        output_url=result.output_url,
        error=result.error,
        cost_usd=result.cost_usd,
    )


# ---------- Status ----------


@router.get("/status/{request_id}")
async def get_generation_status(request_id: str) -> dict:
    """生成リクエストのステータスを取得する."""
    result = media_generation_service.get_result(request_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return {
        "request_id": result.request_id,
        "status": result.status.value,
        "media_type": result.media_type,
        "provider": result.provider,
        "output_url": result.output_url,
        "error": result.error,
        "cost_usd": result.cost_usd,
    }
