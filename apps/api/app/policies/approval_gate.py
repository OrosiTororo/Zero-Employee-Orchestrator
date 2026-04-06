"""Approval gate -- Auto-detection of dangerous operations and approval requests.

Inspired by Claude Cowork's tiered approval model:
- Per-app approval (AI asks permission before accessing each application)
- Per-action granularity (navigate vs. click vs. type vs. delete)
- Scope-aware (read-only navigation vs. form filling vs. data extraction)

Covers:
- External sends / posts / publishing
- Deletion / billing
- Git push / release
- Overwriting important files
- Permission changes
- API key-related operations
- Browser automation (tiered: navigate < extract < interact < submit)
- Web AI sessions (per-service approval)
- Creating new Agents / Teams
- Budget limit changes
- Policy Pack changes
- Expanding autonomy boundaries
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ApprovalCategory(str, Enum):
    """Category of operations requiring approval."""

    EXTERNAL_SEND = "external_send"
    PUBLISH = "publish"
    DELETE = "delete"
    BILLING = "billing"
    GIT_PUSH = "git_push"
    FILE_OVERWRITE = "file_overwrite"
    PERMISSION_CHANGE = "permission_change"
    CREDENTIAL_CHANGE = "credential_change"
    AGENT_CREATE = "agent_create"
    BUDGET_CHANGE = "budget_change"
    POLICY_CHANGE = "policy_change"
    AUTONOMY_EXPAND = "autonomy_expand"
    BROWSER_AUTOMATION = "browser_automation"
    WEB_AI_SESSION = "web_ai_session"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalGateResult:
    """Approval gate check result."""

    requires_approval: bool
    category: ApprovalCategory | None = None
    risk_level: RiskLevel = RiskLevel.LOW
    reason: str = ""
    suggested_approver: str | None = None  # user_id or role


# Operation name -> category + risk level mapping
_DANGEROUS_OPERATIONS: dict[str, tuple[ApprovalCategory, RiskLevel]] = {
    # External communications
    "send_email": (ApprovalCategory.EXTERNAL_SEND, RiskLevel.HIGH),
    "post_sns": (ApprovalCategory.PUBLISH, RiskLevel.HIGH),
    "publish_content": (ApprovalCategory.PUBLISH, RiskLevel.HIGH),
    # Deletion
    "delete_file": (ApprovalCategory.DELETE, RiskLevel.MEDIUM),
    "delete_data": (ApprovalCategory.DELETE, RiskLevel.HIGH),
    # Billing
    "charge_payment": (ApprovalCategory.BILLING, RiskLevel.CRITICAL),
    # Git
    "git_push": (ApprovalCategory.GIT_PUSH, RiskLevel.MEDIUM),
    "git_release": (ApprovalCategory.GIT_PUSH, RiskLevel.HIGH),
    # File operations
    "overwrite_config": (ApprovalCategory.FILE_OVERWRITE, RiskLevel.HIGH),
    # Permissions & credentials
    "change_permission": (ApprovalCategory.PERMISSION_CHANGE, RiskLevel.CRITICAL),
    "update_api_key": (ApprovalCategory.CREDENTIAL_CHANGE, RiskLevel.CRITICAL),
    "rotate_secret": (ApprovalCategory.CREDENTIAL_CHANGE, RiskLevel.HIGH),
    # Agent management
    "create_agent": (ApprovalCategory.AGENT_CREATE, RiskLevel.MEDIUM),
    "create_team": (ApprovalCategory.AGENT_CREATE, RiskLevel.MEDIUM),
    # Policy
    "change_budget": (ApprovalCategory.BUDGET_CHANGE, RiskLevel.HIGH),
    "change_policy": (ApprovalCategory.POLICY_CHANGE, RiskLevel.HIGH),
    "expand_autonomy": (ApprovalCategory.AUTONOMY_EXPAND, RiskLevel.CRITICAL),
    # Browser automation — tiered by action scope (Cowork pattern)
    "browser_navigate": (ApprovalCategory.BROWSER_AUTOMATION, RiskLevel.LOW),
    "browser_screenshot": (ApprovalCategory.BROWSER_AUTOMATION, RiskLevel.LOW),
    "browser_extract_data": (ApprovalCategory.BROWSER_AUTOMATION, RiskLevel.MEDIUM),
    "browser_click": (ApprovalCategory.BROWSER_AUTOMATION, RiskLevel.MEDIUM),
    "browser_type": (ApprovalCategory.BROWSER_AUTOMATION, RiskLevel.HIGH),
    "browser_fill_form": (ApprovalCategory.BROWSER_AUTOMATION, RiskLevel.HIGH),
    "browser_submit_form": (ApprovalCategory.BROWSER_AUTOMATION, RiskLevel.HIGH),
    "browser_download": (ApprovalCategory.BROWSER_AUTOMATION, RiskLevel.HIGH),
    "browser_login": (ApprovalCategory.BROWSER_AUTOMATION, RiskLevel.CRITICAL),
    "browser_payment": (ApprovalCategory.BROWSER_AUTOMATION, RiskLevel.CRITICAL),
    # Web AI sessions — per-service (Cowork per-app approval pattern)
    "web_ai_session": (ApprovalCategory.WEB_AI_SESSION, RiskLevel.MEDIUM),
    "web_ai_session_paid": (ApprovalCategory.WEB_AI_SESSION, RiskLevel.HIGH),
}


def check_approval_required(operation: str) -> ApprovalGateResult:
    """Determine whether an operation requires human approval."""
    entry = _DANGEROUS_OPERATIONS.get(operation)
    if entry is None:
        return ApprovalGateResult(requires_approval=False)

    category, risk_level = entry
    return ApprovalGateResult(
        requires_approval=True,
        category=category,
        risk_level=risk_level,
        reason=f"Operation '{operation}' falls under the {category.value} category and requires human approval",
    )


def check_operations_batch(operations: list[str]) -> list[ApprovalGateResult]:
    """Batch check whether multiple operations require approval."""
    return [check_approval_required(op) for op in operations]


def get_highest_risk(results: list[ApprovalGateResult]) -> RiskLevel:
    """Return the highest risk level from multiple check results."""
    risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    max_idx = 0
    for r in results:
        if r.requires_approval:
            idx = risk_order.index(r.risk_level)
            max_idx = max(max_idx, idx)
    return risk_order[max_idx]
