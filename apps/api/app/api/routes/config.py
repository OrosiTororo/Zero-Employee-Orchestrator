"""Configuration management API — API キーや実行モードをアプリ内から設定.

.env ファイルを直接編集する代わりに、Web UI や API 経由で設定を変更できる。
設定の変更は認証済みユーザーのみ実行可能。
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
    """全設定値を取得する（機密値はマスク済み）.

    Returns a dict of all configurable keys with their current values,
    source (environment, config_file, default, unset), and metadata.
    """
    return {
        "config": get_all_config(),
        "execution_mode": get_config_value("DEFAULT_EXECUTION_MODE"),
    }


@router.get("/config/providers")
async def list_providers(user: User = Depends(get_current_user)):
    """各 LLM プロバイダーの接続状態を取得する."""
    return {
        "providers": get_provider_status(),
        "execution_mode": get_config_value("DEFAULT_EXECUTION_MODE"),
    }


@router.put("/config")
async def update_config(
    req: ConfigUpdateRequest,
    user: User = Depends(get_current_user),
):
    """設定値を更新する.

    値は ~/.zero-employee/config.json に保存され、
    実行中のアプリケーションにも即座に反映される。
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
    """複数の設定値を一括更新する."""
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
    """ランタイム設定値を削除する（デフォルト値に戻す）."""
    if key not in CONFIGURABLE_KEYS:
        raise HTTPException(status_code=400, detail=f"Unknown config key: {key}")
    removed = delete_config_value(key)
    return {"removed": removed, "key": key}


@router.get("/config/keys")
async def list_configurable_keys(user: User = Depends(get_current_user)):
    """設定可能なキーの一覧とメタデータを返す."""
    return {"keys": CONFIGURABLE_KEYS}
