"""Security settings API endpoints.

API for changing file system sandbox, data protection, and PII protection
settings from GUI / CLI / TUI.

Initial settings are the most secure:
- Sandbox: STRICT (allowlist only)
- Data transfer: LOCKDOWN (all external transfers blocked)
- PII detection: all categories enabled
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps.services import get_data_protection, get_sandbox, get_workspace_isolation
from app.api.routes.auth import get_current_user
from app.models.user import User
from app.security.data_protection import (
    DataProtectionConfig,
    DataProtectionGuard,
    TransferPolicy,
)
from app.security.pii_guard import detect_and_mask_pii, get_pii_categories
from app.security.redteam import RedTeamService
from app.security.sandbox import (
    AccessType,
    FileSystemSandbox,
    SandboxConfig,
    SandboxLevel,
)
from app.security.workspace_isolation import (
    StorageLocation,
    TaskWorkspaceOverride,
    WorkspaceConfig,
    WorkspaceIsolation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["security"])


# ---------- Schemas ----------


class SandboxConfigRequest(BaseModel):
    """Sandbox configuration request."""

    level: str = Field(default="strict", description="strict | moderate | permissive")
    allowed_paths: list[str] = Field(default_factory=list)
    denied_paths: list[str] | None = None
    max_file_size_mb: int = 50
    allow_symlink_follow: bool = False


class DataProtectionConfigRequest(BaseModel):
    """Data protection configuration request."""

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
    """Add allowed path request."""

    path: str


class AccessCheckRequest(BaseModel):
    """Access check request."""

    path: str
    access_type: str = "read"


class PIICheckRequest(BaseModel):
    """PII check request."""

    text: str


class SecurityOverviewResponse(BaseModel):
    """Security settings overview."""

    sandbox: dict[str, Any]
    data_protection: dict[str, Any]
    pii_protection: dict[str, Any]


# --- Sandbox response models ---


class SandboxConfigResponse(BaseModel):
    """Sandbox configuration response."""

    level: str
    allowed_paths: list[str]
    denied_paths: list[str]
    max_file_size_mb: int
    allow_symlink_follow: bool


class SandboxUpdateResponse(BaseModel):
    """Sandbox update result."""

    status: str
    level: str


class AllowedPathAddResponse(BaseModel):
    """Allowed path add result."""

    status: str
    path: str
    total_allowed: int


class AllowedPathRemoveResponse(BaseModel):
    """Allowed path remove result."""

    status: str
    path: str


class AccessCheckResponse(BaseModel):
    """Access check result."""

    allowed: bool
    path: str
    access_type: str
    reason: str
    sandbox_level: str


# --- Data protection response models ---


class DataProtectionConfigResponse(BaseModel):
    """Data protection configuration response."""

    transfer_policy: str
    upload_enabled: bool
    upload_allowed_destinations: list[str]
    upload_max_size_mb: int
    upload_require_approval: bool
    download_enabled: bool
    download_allowed_sources: list[str]
    download_max_size_mb: int
    download_require_approval: bool
    external_api_enabled: bool
    external_api_allowed_hosts: list[str]
    external_api_require_approval: bool
    pii_auto_detect: bool
    pii_block_upload: bool
    password_upload_blocked: bool


class DataProtectionUpdateResponse(BaseModel):
    """Data protection update result."""

    status: str
    policy: str


# --- PII response models ---


class PIICategoryResponse(BaseModel):
    """Single PII category entry."""

    id: str
    name: str


class PIICheckResponse(BaseModel):
    """PII check result."""

    has_pii: bool
    detected_count: int
    detected_types: list[str]
    masked_text: str


# --- Workspace response models ---


class WorkspaceConfigResponse(BaseModel):
    """Workspace configuration response."""

    local_access_enabled: bool
    cloud_access_enabled: bool
    allowed_local_paths: list[str]
    cloud_providers: list[str]
    storage_location: str
    internal_storage_path: str
    access_scope: str


class WorkspaceUpdateResponse(BaseModel):
    """Workspace update result."""

    status: str
    access_scope: str


class TaskOverrideSetResponse(BaseModel):
    """Task workspace override set result."""

    status: str
    task_id: str
    requires_approval: bool


class TaskOverrideApproveResponse(BaseModel):
    """Task workspace override approval result."""

    status: str
    task_id: str


# --- Red team response models ---


class RedTeamTestResult(BaseModel):
    """Single red team test result."""

    test_id: str
    passed: bool
    vulnerability_found: bool
    details: str


class RedTeamRunResponse(BaseModel):
    """Red team run result."""

    total: int
    passed: int
    failed: int
    critical_findings: int | None = None
    high_findings: int | None = None
    summary: str | None = None
    results: list[RedTeamTestResult]


# ---------- Endpoints ----------


@router.get("/overview", response_model=SecurityOverviewResponse)
async def get_security_overview(
    user: User = Depends(get_current_user),
    sandbox: FileSystemSandbox = Depends(get_sandbox),
    dp_guard: DataProtectionGuard = Depends(get_data_protection),
) -> SecurityOverviewResponse:
    """Return security settings overview."""
    sandbox_config = sandbox.config
    dp_config = dp_guard.config

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


@router.get("/sandbox", response_model=SandboxConfigResponse)
async def get_sandbox_config(
    user: User = Depends(get_current_user),
    sandbox: FileSystemSandbox = Depends(get_sandbox),
) -> SandboxConfigResponse:
    """Get sandbox configuration."""
    config = sandbox.config
    return {
        "level": config.level.value,
        "allowed_paths": config.allowed_paths,
        "denied_paths": config.denied_paths,
        "max_file_size_mb": config.max_file_size_mb,
        "allow_symlink_follow": config.allow_symlink_follow,
    }


@router.put("/sandbox", response_model=SandboxUpdateResponse)
async def update_sandbox_config(
    req: SandboxConfigRequest,
    user: User = Depends(get_current_user),
    sandbox: FileSystemSandbox = Depends(get_sandbox),
) -> SandboxUpdateResponse:
    """Update sandbox configuration."""
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
        denied_paths=req.denied_paths or list(sandbox.config.denied_paths),
        max_file_size_mb=req.max_file_size_mb,
        allow_symlink_follow=req.allow_symlink_follow,
    )
    sandbox.update_config(config)

    return {"status": "updated", "level": level.value}


@router.post("/sandbox/allowed-paths", response_model=AllowedPathAddResponse)
async def add_allowed_path(
    req: AllowedPathRequest,
    user: User = Depends(get_current_user),
    sandbox: FileSystemSandbox = Depends(get_sandbox),
) -> AllowedPathAddResponse:
    """Add an allowed path."""
    sandbox.add_allowed_path(req.path)
    return {
        "status": "added",
        "path": req.path,
        "total_allowed": len(sandbox.get_allowed_paths()),
    }


@router.delete("/sandbox/allowed-paths", response_model=AllowedPathRemoveResponse)
async def remove_allowed_path(
    req: AllowedPathRequest,
    user: User = Depends(get_current_user),
    sandbox: FileSystemSandbox = Depends(get_sandbox),
) -> AllowedPathRemoveResponse:
    """Remove an allowed path."""
    sandbox.remove_allowed_path(req.path)
    return {"status": "removed", "path": req.path}


@router.post("/sandbox/check-access", response_model=AccessCheckResponse)
async def check_access(
    req: AccessCheckRequest,
    user: User = Depends(get_current_user),
    sandbox: FileSystemSandbox = Depends(get_sandbox),
) -> AccessCheckResponse:
    """Check whether access to a path is allowed."""
    try:
        access_type = AccessType(req.access_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid access_type: {req.access_type}. Valid: read, write, execute, list, delete",
        )

    result = sandbox.check_access(req.path, access_type)
    return {
        "allowed": result.allowed,
        "path": result.path,
        "access_type": result.access_type.value,
        "reason": result.reason,
        "sandbox_level": result.sandbox_level.value,
    }


# --- Data Protection ---


@router.get("/data-protection", response_model=DataProtectionConfigResponse)
async def get_data_protection_config(
    user: User = Depends(get_current_user),
    dp_guard: DataProtectionGuard = Depends(get_data_protection),
) -> DataProtectionConfigResponse:
    """Get data protection configuration."""
    config = dp_guard.config
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


@router.put("/data-protection", response_model=DataProtectionUpdateResponse)
async def update_data_protection_config(
    req: DataProtectionConfigRequest,
    user: User = Depends(get_current_user),
    dp_guard: DataProtectionGuard = Depends(get_data_protection),
) -> DataProtectionUpdateResponse:
    """Update data protection configuration."""
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
    dp_guard.update_config(config)

    return {"status": "updated", "policy": policy.value}


# --- PII ---


@router.get("/pii/categories", response_model=list[PIICategoryResponse])
async def get_pii_categories_list(user: User = Depends(get_current_user)) -> list[PIICategoryResponse]:
    """Return PII category list."""
    return get_pii_categories()


@router.post("/pii/check", response_model=PIICheckResponse)
async def check_pii(req: PIICheckRequest, user: User = Depends(get_current_user)) -> PIICheckResponse:
    """Check text for PII."""
    result = detect_and_mask_pii(req.text)
    return {
        "has_pii": result.detected_count > 0,
        "detected_count": result.detected_count,
        "detected_types": result.detected_types,
        "masked_text": result.masked_text,
    }


# --- Workspace ---


class WorkspaceConfigRequest(BaseModel):
    """Workspace configuration request."""

    local_access_enabled: bool = False
    cloud_access_enabled: bool = False
    allowed_local_paths: list[str] = Field(default_factory=list)
    cloud_providers: list[str] = Field(default_factory=list)
    storage_location: str = Field(default="internal", description="internal | local | cloud")


class TaskWorkspaceOverrideRequest(BaseModel):
    """Per-task workspace override request."""

    additional_local_paths: list[str] = Field(default_factory=list)
    additional_cloud_sources: list[str] = Field(default_factory=list)
    storage_location: str | None = None
    output_path: str | None = None


@router.get("/workspace", response_model=WorkspaceConfigResponse)
async def get_workspace_config(
    user: User = Depends(get_current_user),
    ws_isolation: WorkspaceIsolation = Depends(get_workspace_isolation),
) -> WorkspaceConfigResponse:
    """Get workspace configuration."""
    config = ws_isolation.config
    return {
        "local_access_enabled": config.local_access_enabled,
        "cloud_access_enabled": config.cloud_access_enabled,
        "allowed_local_paths": config.allowed_local_paths,
        "cloud_providers": config.cloud_providers,
        "storage_location": config.storage_location.value,
        "internal_storage_path": config.internal_storage_path,
        "access_scope": ws_isolation.get_access_scope().value,
    }


@router.put("/workspace", response_model=WorkspaceUpdateResponse)
async def update_workspace_config(
    req: WorkspaceConfigRequest,
    user: User = Depends(get_current_user),
    ws_isolation: WorkspaceIsolation = Depends(get_workspace_isolation),
) -> WorkspaceUpdateResponse:
    """Update workspace configuration."""
    try:
        storage = StorageLocation(req.storage_location)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid storage_location: {req.storage_location}. "
            "Valid: internal, local, cloud",
        )

    config = WorkspaceConfig(
        local_access_enabled=req.local_access_enabled,
        allowed_local_paths=req.allowed_local_paths,
        cloud_access_enabled=req.cloud_access_enabled,
        cloud_providers=req.cloud_providers,
        storage_location=storage,
    )
    ws_isolation.update_config(config)

    return {
        "status": "updated",
        "access_scope": ws_isolation.get_access_scope().value,
    }


@router.post("/workspace/tasks/{task_id}/override", response_model=TaskOverrideSetResponse)
async def set_task_workspace_override(
    task_id: str,
    req: TaskWorkspaceOverrideRequest,
    user: User = Depends(get_current_user),
    ws_isolation: WorkspaceIsolation = Depends(get_workspace_isolation),
) -> TaskOverrideSetResponse:
    """Set per-task workspace override."""
    storage = None
    if req.storage_location:
        try:
            storage = StorageLocation(req.storage_location)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid storage_location: {req.storage_location}",
            )

    override = TaskWorkspaceOverride(
        task_id=task_id,
        additional_local_paths=req.additional_local_paths,
        additional_cloud_sources=req.additional_cloud_sources,
        storage_location=storage,
        output_path=req.output_path,
        approved_by_user=False,
    )
    ws_isolation.set_task_override(override)

    return {
        "status": "override_set",
        "task_id": task_id,
        "requires_approval": True,
    }


@router.post("/workspace/tasks/{task_id}/approve", response_model=TaskOverrideApproveResponse)
async def approve_task_workspace_override(
    task_id: str,
    user: User = Depends(get_current_user),
    ws_isolation: WorkspaceIsolation = Depends(get_workspace_isolation),
) -> TaskOverrideApproveResponse:
    """Approve per-task workspace override."""
    approved = ws_isolation.approve_task_override(task_id)
    if not approved:
        raise HTTPException(
            status_code=404,
            detail=f"No pending override found for task {task_id}",
        )
    return {"status": "approved", "task_id": task_id}


# --- Red-team ---


class RedTeamRunRequest(BaseModel):
    """Red team test execution request."""

    category: str | None = Field(
        default=None,
        description="Test category (null = run all). "
        "Options: prompt_injection, data_leakage, privilege_escalation, "
        "pii_exposure, unauthorized_access, sandbox_escape, "
        "rate_limit_bypass, auth_bypass",
    )


@router.post("/redteam/run", response_model=RedTeamRunResponse)
async def run_redteam_tests(
    req: RedTeamRunRequest | None = None, user: User = Depends(get_current_user)
) -> RedTeamRunResponse:
    """Run red team security tests."""
    from app.security.redteam import VulnerabilityType

    service = RedTeamService()
    if req and req.category:
        try:
            vtype = VulnerabilityType(req.category)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {req.category}. "
                f"Valid: {', '.join(v.value for v in VulnerabilityType)}",
            )
        results = await service.run_category(vtype)
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "results": [
                {
                    "test_id": r.test_id,
                    "passed": r.passed,
                    "vulnerability_found": r.vulnerability_found,
                    "details": r.details,
                }
                for r in results
            ],
        }
    else:
        report = await service.run_all_tests()
        return {
            "total": report.total_tests,
            "passed": report.passed,
            "failed": report.failed,
            "critical_findings": report.critical_findings,
            "high_findings": report.high_findings,
            "summary": report.summary,
            "results": [
                {
                    "test_id": r.test_id,
                    "passed": r.passed,
                    "vulnerability_found": r.vulnerability_found,
                    "details": r.details,
                }
                for r in report.results
            ],
        }
