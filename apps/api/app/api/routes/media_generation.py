"""メディア生成 API エンドポイント.

画像・動画・音声・音楽の生成 API。
すべての操作はデータ保護ポリシーと承認ゲートを経由する。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.integrations.media_generation import (
    GenerationProvider,
    GenerationRequest,
    MediaType,
    media_generation_service,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["media-generation"])


class GenerateRequest(BaseModel):
    """メディア生成リクエスト."""

    prompt: str = Field(..., min_length=1, max_length=10000)
    media_type: str = Field(..., description="image | video | audio | music")
    provider: str = Field(..., description="Provider ID (e.g. openai_dalle)")
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


# 認証不要: プロバイダー一覧は公開情報
@router.get("/providers")
async def list_providers() -> list[dict]:
    """利用可能なメディア生成プロバイダー一覧."""
    return media_generation_service.get_available_providers()


# 認証不要: プロバイダー一覧は公開情報
@router.get("/providers/{media_type}")
async def list_providers_by_type(media_type: str) -> list[dict]:
    """メディアタイプ別のプロバイダー一覧."""
    try:
        mt = MediaType(media_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid media_type: {media_type}. Valid: image, video, audio, music",
        )
    return media_generation_service.get_providers_by_type(mt)


@router.post("/generate", response_model=GenerateResponse)
async def generate_media(
    req: GenerateRequest, user: User = Depends(get_current_user)
) -> GenerateResponse:
    """メディアを生成する."""
    try:
        mt = MediaType(req.media_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid media_type: {req.media_type}",
        )

    try:
        provider = GenerationProvider(req.provider)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider: {req.provider}. "
            f"Valid: {[p.value for p in GenerationProvider]}",
        )

    request = GenerationRequest(
        prompt=req.prompt,
        media_type=mt,
        provider=provider,
        user_id=req.user_id,
        parameters=req.parameters,
        negative_prompt=req.negative_prompt,
        language=req.language,
    )

    result = await media_generation_service.generate(request)

    return GenerateResponse(
        request_id=result.request_id,
        status=result.status.value,
        media_type=result.media_type.value,
        provider=result.provider.value,
        output_url=result.output_url,
        error=result.error,
        cost_usd=result.cost_usd,
    )


# 認証不要: プロバイダー一覧は公開情報
@router.get("/status/{request_id}")
async def get_generation_status(request_id: str) -> dict:
    """生成リクエストのステータスを取得する."""
    result = media_generation_service.get_result(request_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return {
        "request_id": result.request_id,
        "status": result.status.value,
        "media_type": result.media_type.value,
        "provider": result.provider.value,
        "output_url": result.output_url,
        "error": result.error,
        "cost_usd": result.cost_usd,
    }
