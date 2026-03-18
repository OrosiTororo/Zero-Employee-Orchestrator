"""セキュリティ設定 API エンドポイント.

ファイルシステムサンドボックス、データ保護、PII 保護の
設定を GUI / CLI / TUI から変更するための API。

初期設定は最もセキュアな状態:
- サンドボックス: STRICT（許可リストのみ）
- データ転送: LOCKDOWN（外部転送全面禁止）
- PII 検出: 全カテゴリ有効
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.security.data_protection import (
    DataProtectionConfig,
    TransferPolicy,
    data_protection_guard,
)
from app.security.pii_guard import detect_and_mask_pii, get_pii_categories
from app.security.sandbox import (
    AccessType,
    SandboxConfig,
    SandboxLevel,
    filesystem_sandbox,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["security"])


# ---------- Schemas ----------


class SandboxConfigRequest(BaseModel):
    """サンドボックス設定リクエスト."""

    level: str = Field(default="strict", description="strict | moderate | permissive")
    allowed_paths: list[str] = Field(default_factory=list)
    denied_paths: list[str] | None = None
    max_file_size_mb: int = 50
    allow_symlink_follow: bool = False


class DataProtectionConfigRequest(BaseModel):
    """データ保護設定リクエスト."""

    transfer_policy: str = Field(
        default="lockdown", description="lockdown | restricted | permissive"
    )
    upload_enabled: bool = False
    upload_allowed_destinations: list[str] = Field(default_factory=list)
    upload_max_size_mb: int = 10
    upload_require_approval: bool = True
    download_enabled: bool = False
    download_allowed_sources: list[str] = Field(default_factory=list)
    download_max_size_mb: int = 100
    download_require_approval: bool = True
    external_api_enabled: bool = False
    external_api_allowed_hosts: list[str] = Field(default_factory=list)
    external_api_require_approval: bool = True
    pii_auto_detect: bool = True
    pii_block_upload: bool = True
    password_upload_blocked: bool = True


class AllowedPathRequest(BaseModel):
    """許可パス追加リクエスト."""

    path: str


class AccessCheckRequest(BaseModel):
    """アクセスチェックリクエスト."""

    path: str
    access_type: str = "read"


class PIICheckRequest(BaseModel):
    """PII チェックリクエスト."""

    text: str


class SecurityOverviewResponse(BaseModel):
    """セキュリティ設定概要."""

    sandbox: dict
    data_protection: dict
    pii_protection: dict


# ---------- Endpoints ----------


@router.get("/overview")
async def get_security_overview() -> SecurityOverviewResponse:
    """セキュリティ設定の概要を返す."""
    sandbox_config = filesystem_sandbox.config
    dp_config = data_protection_guard.config

    return SecurityOverviewResponse(
        sandbox={
            "level": sandbox_config.level.value,
            "allowed_paths_count": len(sandbox_config.allowed_paths),
            "denied_paths_count": len(sandbox_config.denied_paths),
            "allowed_paths": sandbox_config.allowed_paths,
            "max_file_size_mb": sandbox_config.max_file_size_mb,
            "allow_symlink_follow": sandbox_config.allow_symlink_follow,
        },
        data_protection={
            "transfer_policy": dp_config.transfer_policy.value,
            "upload_enabled": dp_config.upload_enabled,
            "download_enabled": dp_config.download_enabled,
            "external_api_enabled": dp_config.external_api_enabled,
            "upload_require_approval": dp_config.upload_require_approval,
            "download_require_approval": dp_config.download_require_approval,
            "pii_auto_detect": dp_config.pii_auto_detect,
            "password_upload_blocked": dp_config.password_upload_blocked,
        },
        pii_protection={
            "enabled": dp_config.pii_auto_detect,
            "block_upload": dp_config.pii_block_upload,
            "mask_in_logs": dp_config.pii_mask_in_logs,
            "categories": get_pii_categories(),
        },
    )


# --- Sandbox ---


@router.get("/sandbox")
async def get_sandbox_config() -> dict:
    """サンドボックス設定を取得する."""
    config = filesystem_sandbox.config
    return {
        "level": config.level.value,
        "allowed_paths": config.allowed_paths,
        "denied_paths": config.denied_paths,
        "max_file_size_mb": config.max_file_size_mb,
        "allow_symlink_follow": config.allow_symlink_follow,
    }


@router.put("/sandbox")
async def update_sandbox_config(req: SandboxConfigRequest) -> dict:
    """サンドボックス設定を更新する."""
    try:
        level = SandboxLevel(req.level)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid level: {req.level}. Valid: strict, moderate, permissive",
        )

    config = SandboxConfig(
        level=level,
        allowed_paths=req.allowed_paths,
        denied_paths=req.denied_paths or list(filesystem_sandbox.config.denied_paths),
        max_file_size_mb=req.max_file_size_mb,
        allow_symlink_follow=req.allow_symlink_follow,
    )
    filesystem_sandbox.update_config(config)

    return {"status": "updated", "level": level.value}


@router.post("/sandbox/allowed-paths")
async def add_allowed_path(req: AllowedPathRequest) -> dict:
    """許可パスを追加する."""
    filesystem_sandbox.add_allowed_path(req.path)
    return {
        "status": "added",
        "path": req.path,
        "total_allowed": len(filesystem_sandbox.get_allowed_paths()),
    }


@router.delete("/sandbox/allowed-paths")
async def remove_allowed_path(req: AllowedPathRequest) -> dict:
    """許可パスを削除する."""
    filesystem_sandbox.remove_allowed_path(req.path)
    return {"status": "removed", "path": req.path}


@router.post("/sandbox/check-access")
async def check_access(req: AccessCheckRequest) -> dict:
    """パスへのアクセス可否をチェックする."""
    try:
        access_type = AccessType(req.access_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid access_type: {req.access_type}. Valid: read, write, execute, list, delete",
        )

    result = filesystem_sandbox.check_access(req.path, access_type)
    return {
        "allowed": result.allowed,
        "path": result.path,
        "access_type": result.access_type.value,
        "reason": result.reason,
        "sandbox_level": result.sandbox_level.value,
    }


# --- Data Protection ---


@router.get("/data-protection")
async def get_data_protection_config() -> dict:
    """データ保護設定を取得する."""
    config = data_protection_guard.config
    return {
        "transfer_policy": config.transfer_policy.value,
        "upload_enabled": config.upload_enabled,
        "upload_allowed_destinations": config.upload_allowed_destinations,
        "upload_max_size_mb": config.upload_max_size_mb,
        "upload_require_approval": config.upload_require_approval,
        "download_enabled": config.download_enabled,
        "download_allowed_sources": config.download_allowed_sources,
        "download_max_size_mb": config.download_max_size_mb,
        "download_require_approval": config.download_require_approval,
        "external_api_enabled": config.external_api_enabled,
        "external_api_allowed_hosts": config.external_api_allowed_hosts,
        "external_api_require_approval": config.external_api_require_approval,
        "pii_auto_detect": config.pii_auto_detect,
        "pii_block_upload": config.pii_block_upload,
        "password_upload_blocked": config.password_upload_blocked,
    }


@router.put("/data-protection")
async def update_data_protection_config(req: DataProtectionConfigRequest) -> dict:
    """データ保護設定を更新する."""
    try:
        policy = TransferPolicy(req.transfer_policy)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid policy: {req.transfer_policy}. Valid: lockdown, restricted, permissive",
        )

    config = DataProtectionConfig(
        transfer_policy=policy,
        upload_enabled=req.upload_enabled,
        upload_allowed_destinations=req.upload_allowed_destinations,
        upload_max_size_mb=req.upload_max_size_mb,
        upload_require_approval=req.upload_require_approval,
        download_enabled=req.download_enabled,
        download_allowed_sources=req.download_allowed_sources,
        download_max_size_mb=req.download_max_size_mb,
        download_require_approval=req.download_require_approval,
        external_api_enabled=req.external_api_enabled,
        external_api_allowed_hosts=req.external_api_allowed_hosts,
        external_api_require_approval=req.external_api_require_approval,
        pii_auto_detect=req.pii_auto_detect,
        pii_block_upload=req.pii_block_upload,
        password_upload_blocked=req.password_upload_blocked,
    )
    data_protection_guard.update_config(config)

    return {"status": "updated", "policy": policy.value}


# --- PII ---


@router.get("/pii/categories")
async def get_pii_categories_list() -> list[dict]:
    """PII カテゴリ一覧を返す."""
    return get_pii_categories()


@router.post("/pii/check")
async def check_pii(req: PIICheckRequest) -> dict:
    """テキストの PII をチェックする."""
    result = detect_and_mask_pii(req.text)
    return {
        "has_pii": result.detected_count > 0,
        "detected_count": result.detected_count,
        "detected_types": result.detected_types,
        "masked_text": result.masked_text,
    }
