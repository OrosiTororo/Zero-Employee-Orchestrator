"""Governance and compliance API endpoints.

Provides policy management, compliance auditing, and violation reporting.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.models.user import User
from app.services.governance_service import (
    ComplianceFramework,
    PolicyRule,
    PolicyType,
    ViolationSeverity,
    governance_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/governance", tags=["governance"])


# ---------- Schemas ----------


class AddPolicyRequest(BaseModel):
    """Add policy request."""

    name: str = Field(..., min_length=1, max_length=200)
    policy_type: str = Field(...)
    framework: str = Field(...)
    description: str = Field(default="")
    conditions: dict = Field(default_factory=dict)
    actions: list[str] = Field(default_factory=list)
    severity: str = Field(default="medium")
    is_active: bool = Field(default=True)


# ---------- Endpoints ----------


@router.post("/policies", status_code=201)
async def add_policy(req: AddPolicyRequest, user: User = Depends(get_current_user)) -> dict:
    """Add a policy rule."""
    try:
        policy_type = PolicyType(req.policy_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid policy type: {req.policy_type}. "
            f"Valid values: {[p.value for p in PolicyType]}",
        )

    try:
        framework = ComplianceFramework(req.framework)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid framework: {req.framework}. "
            f"Valid values: {[f.value for f in ComplianceFramework]}",
        )

    try:
        severity = ViolationSeverity(req.severity)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity: {req.severity}. Valid values: {[s.value for s in ViolationSeverity]}",
        )

    rule = PolicyRule(
        id="",
        name=req.name,
        policy_type=policy_type,
        framework=framework,
        description=req.description,
        conditions=req.conditions,
        actions=req.actions,
        severity=severity,
        is_active=req.is_active,
    )
    result = await governance_service.add_policy(rule)
    return _policy_to_dict(result)


@router.get("/policies")
async def list_policies(
    framework: str | None = None,
    policy_type: str | None = None,
    active_only: bool = True,
    user: User = Depends(get_current_user),
) -> list[dict]:
    """List policy rules."""
    fw = None
    if framework:
        try:
            fw = ComplianceFramework(framework)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid framework: {framework}",
            )

    pt = None
    if policy_type:
        try:
            pt = PolicyType(policy_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid policy type: {policy_type}",
            )

    policies = await governance_service.list_policies(
        framework=fw, policy_type=pt, active_only=active_only
    )
    return [_policy_to_dict(p) for p in policies]


@router.post("/check/{framework}")
async def run_compliance_check(
    framework: str,
    resource_id: str = Query(default="", description="Resource ID to check"),
    user: User = Depends(get_current_user),
) -> dict:
    """Run compliance check for the specified framework."""
    try:
        fw = ComplianceFramework(framework)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid framework: {framework}. "
            f"Valid values: {[f.value for f in ComplianceFramework]}",
        )

    results = await governance_service.check_compliance(fw, resource_id)
    passed = sum(1 for r in results if r.status.value == "pass")
    failed = sum(1 for r in results if r.status.value == "fail")

    return {
        "framework": fw.value,
        "total_checks": len(results),
        "passed": passed,
        "failed": failed,
        "results": [
            {
                "id": r.id,
                "rule_id": r.rule_id,
                "status": r.status.value,
                "details": r.details,
                "checked_at": r.checked_at,
                "resource_id": r.resource_id,
            }
            for r in results
        ],
    }


@router.get("/report/{framework}")
async def get_compliance_report(framework: str, user: User = Depends(get_current_user)) -> dict:
    """Get compliance report."""
    try:
        fw = ComplianceFramework(framework)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid framework: {framework}",
        )

    return await governance_service.get_compliance_report(fw)


@router.get("/violations")
async def get_violations(
    severity: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
) -> list[dict]:
    """Get recent policy violations."""
    sev = None
    if severity:
        try:
            sev = ViolationSeverity(severity)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity: {severity}",
            )

    violations = await governance_service.get_policy_violations(severity=sev, limit=limit)
    return [
        {
            "id": v.id,
            "rule_id": v.rule_id,
            "rule_name": v.rule_name,
            "severity": v.severity.value,
            "details": v.details,
            "resource_id": v.resource_id,
            "detected_at": v.detected_at,
        }
        for v in violations
    ]


# ---------- Helpers ----------


def _policy_to_dict(rule: PolicyRule) -> dict:
    """Convert PolicyRule to dict."""
    return {
        "id": rule.id,
        "name": rule.name,
        "policy_type": rule.policy_type.value,
        "framework": rule.framework.value,
        "description": rule.description,
        "conditions": rule.conditions,
        "actions": rule.actions,
        "severity": rule.severity.value,
        "is_active": rule.is_active,
        "created_at": rule.created_at,
    }
