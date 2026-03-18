"""ユーザー入力リクエスト API エンドポイント.

AIタスクが実行中にユーザーへ追加情報を要求するための
リクエスト作成・回答・一覧・キャンセル機能を提供する。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.user_input_service import (
    InputRequest,
    InputRequestStatus,
    InputRequestType,
    user_input_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-input", tags=["user-input"])


# ---------------------------------------------------------------------------
# Pydantic スキーマ
# ---------------------------------------------------------------------------
class CreateInputRequestBody(BaseModel):
    """入力リクエスト作成リクエスト."""

    task_id: str = Field(..., description="対象タスクのID")
    request_type: InputRequestType = Field(..., description="入力タイプ")
    prompt_text: str = Field(
        ..., min_length=1, max_length=2000, description="ユーザーに表示するプロンプト"
    )
    options: list[str] | None = Field(default=None, description="CHOICE タイプの場合の選択肢")
    timeout_seconds: int = Field(default=300, ge=10, le=86400, description="タイムアウト秒数")


class AnswerInputBody(BaseModel):
    """入力回答リクエスト."""

    response: str | list[str] | bool = Field(..., description="ユーザーの回答")


class InputRequestResponse(BaseModel):
    """入力リクエストレスポンス."""

    id: str
    task_id: str
    request_type: str
    prompt_text: str
    options: list[str] | None
    timeout_seconds: int
    status: str
    created_at: str
    answered_at: str | None
    response: str | list[str] | bool | None


class PendingRequestsResponse(BaseModel):
    """未回答リクエスト一覧レスポンス."""

    requests: list[InputRequestResponse]
    total: int


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------
def _to_response(req: InputRequest) -> InputRequestResponse:
    """InputRequest を InputRequestResponse に変換する."""
    return InputRequestResponse(
        id=req.id,
        task_id=req.task_id,
        request_type=req.request_type.value,
        prompt_text=req.prompt_text,
        options=req.options,
        timeout_seconds=req.timeout_seconds,
        status=req.status.value,
        created_at=req.created_at.isoformat(),
        answered_at=req.answered_at.isoformat() if req.answered_at else None,
        response=req.response,
    )


# ---------------------------------------------------------------------------
# エンドポイント
# ---------------------------------------------------------------------------
@router.post("/request", response_model=InputRequestResponse)
async def create_input_request(body: CreateInputRequestBody) -> InputRequestResponse:
    """入力リクエストを作成する.

    AIタスクがユーザーに追加情報を要求する際に使用する。
    """
    try:
        request_id = await user_input_service.request_input(
            task_id=body.task_id,
            request_type=body.request_type,
            prompt_text=body.prompt_text,
            options=body.options,
            timeout_seconds=body.timeout_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    req = user_input_service.get_request(request_id)
    if req is None:
        raise HTTPException(status_code=500, detail="リクエストの作成に失敗しました")
    return _to_response(req)


@router.get("/pending", response_model=PendingRequestsResponse)
async def list_all_pending_requests() -> PendingRequestsResponse:
    """全タスクの未回答リクエスト一覧を取得する."""
    # 期限切れチェックを先に実行
    await user_input_service.expire_stale_requests()

    all_pending: list[InputRequest] = [
        r for r in user_input_service._requests.values() if r.status == InputRequestStatus.PENDING
    ]
    return PendingRequestsResponse(
        requests=[_to_response(r) for r in all_pending],
        total=len(all_pending),
    )


@router.get("/pending/{task_id}", response_model=PendingRequestsResponse)
async def list_pending_for_task(task_id: str) -> PendingRequestsResponse:
    """指定タスクの未回答リクエスト一覧を取得する."""
    await user_input_service.expire_stale_requests()
    pending = await user_input_service.get_pending_requests(task_id)
    return PendingRequestsResponse(
        requests=[_to_response(r) for r in pending],
        total=len(pending),
    )


@router.post("/{request_id}/answer", response_model=InputRequestResponse)
async def answer_request(
    request_id: str,
    body: AnswerInputBody,
) -> InputRequestResponse:
    """入力リクエストに回答する."""
    try:
        req = await user_input_service.answer_input(request_id, body.response)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(req)


@router.delete("/{request_id}", response_model=InputRequestResponse)
async def cancel_request(request_id: str) -> InputRequestResponse:
    """入力リクエストをキャンセルする."""
    try:
        req = await user_input_service.cancel_request(request_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(req)
