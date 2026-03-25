"""共通バリデーションヘルパー."""

from __future__ import annotations

import logging
import uuid

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def parse_uuid(value: str, name: str = "ID") -> uuid.UUID:
    """UUID 文字列を安全にパースする.

    不正な UUID 文字列の場合は 400 Bad Request を返す。
    """
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {name} format: {value}",
        )


def require_iam_permission(required: str):
    """IAM 権限チェックデコレータ（FastAPI Depends 互換）.

    AI エージェントからのリクエストに対して、要求された権限を持っているか検証する。
    人間ユーザーからのリクエストは常に許可する。

    Usage::

        @router.post("/secrets")
        async def create_secret(
            user=Depends(get_current_user),
            _perm=Depends(require_iam_permission("read:secrets")),
        ):
            ...
    """
    from fastapi import Depends, Request

    from app.api.routes.auth import get_current_user

    async def _check(request: Request, user=Depends(get_current_user)):
        # AI エージェントからのリクエストかどうかを判定
        # X-Agent-Token ヘッダーがある場合は AI エージェント
        agent_token = request.headers.get("X-Agent-Token")
        if not agent_token:
            return True  # 人間ユーザーは常に許可

        # IAM チェック
        from app.security.iam import AI_DENIED_PERMISSIONS

        # AI に明示的に禁止されている権限
        denied_values = {d.value for d in AI_DENIED_PERMISSIONS}
        if required in denied_values:
            logger.warning(
                "IAM denied: AI agent attempted forbidden permission %s",
                required,
            )
            raise HTTPException(
                status_code=403,
                detail=f"AI エージェントにはこの操作の権限がありません: {required}",
            )

        return True

    return _check
