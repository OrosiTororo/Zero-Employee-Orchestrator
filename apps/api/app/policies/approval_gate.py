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
    EXTERNAL_AGENT = "external_agent"
    PLUGIN_INSTALL = "plugin_install"


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
    # External agent frameworks (CrewAI, AutoGen, LangChain, Dify, n8n, …)
    "external_agent_execution": (ApprovalCategory.EXTERNAL_AGENT, RiskLevel.HIGH),
    # Plugin install (pip install of third-party packages requested by a plugin manifest)
    "plugin_install": (ApprovalCategory.PLUGIN_INSTALL, RiskLevel.HIGH),
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
        reason=f"Operation '{operation}' falls under the {category.value} category and requires human approval",  # noqa: E501
    )


def generate_action_preview(operation: str, payload: dict | None = None) -> str:
    """Generate a human-readable preview of what an operation will do.

    Inspired by Copilot Cowork's approval checkpoints: show the user
    exactly what will happen before they approve.
    """
    payload = payload or {}

    # Operation-specific preview templates
    _PREVIEW_TEMPLATES: dict[str, str] = {
        "send_email": "Will send email to {recipient_count} recipient(s)",
        "post_sns": "Will post to {platform}",
        "publish_content": "Will publish content to {destination}",
        "delete_file": "Will delete {file_count} file(s): {files}",
        "delete_data": "Will permanently delete {record_count} record(s) from {source}",
        "charge_payment": "Will charge {amount} {currency} to {account}",
        "git_push": "Will push {branch} to {remote}",
        "git_release": "Will create release {version} on {remote}",
        "overwrite_config": "Will overwrite configuration: {config_path}",
        "change_permission": "Will change permissions for {subject} on {resource}",
        "update_api_key": "Will update API key for {service}",
        "rotate_secret": "Will rotate secret for {service}",
        "create_agent": "Will create new agent: {agent_name}",
        "create_team": "Will create new team: {team_name}",
        "change_budget": "Will change budget limit to {new_limit} {currency}",
        "change_policy": "Will modify policy: {policy_name}",
        "expand_autonomy": "Will expand autonomy boundary: {boundary}",
        "browser_navigate": "Will navigate to {url}",
        "browser_screenshot": "Will take screenshot of {url}",
        "browser_extract_data": "Will extract data from {url}",
        "browser_click": "Will click element on {url}",
        "browser_type": "Will type into form on {url}",
        "browser_fill_form": "Will fill form on {url}",
        "browser_submit_form": "Will submit form on {url}",
        "browser_download": "Will download file from {url}",
        "browser_login": "Will log in to {service}",
        "browser_payment": "Will make payment on {service}",
        "web_ai_session": "Will start AI session with {service}",
        "web_ai_session_paid": "Will start paid AI session with {service}",
        "external_agent_execution": "Will delegate task to external agent framework: {framework}",
    }

    template = _PREVIEW_TEMPLATES.get(operation)
    if not template:
        entry = _DANGEROUS_OPERATIONS.get(operation)
        if entry:
            category, _ = entry
            return f"Will perform {category.value} operation: {operation}"
        return f"Will execute: {operation}"

    # Fill template with payload data, using safe defaults
    try:
        return template.format_map(_PreviewDefaults(payload))
    except (KeyError, ValueError):
        return template


class _PreviewDefaults(dict):
    """Dict subclass that returns placeholder text for missing keys."""

    _DEFAULTS: dict[str, str] = {
        "recipient_count": "N",
        "platform": "social media",
        "destination": "target",
        "file_count": "N",
        "files": "(details pending)",
        "record_count": "N",
        "source": "database",
        "amount": "N/A",
        "currency": "",
        "account": "default account",
        "branch": "current branch",
        "remote": "origin",
        "version": "N/A",
        "config_path": "(path pending)",
        "subject": "user/role",
        "resource": "resource",
        "service": "service",
        "agent_name": "(unnamed)",
        "team_name": "(unnamed)",
        "new_limit": "N/A",
        "policy_name": "(unnamed)",
        "boundary": "(details pending)",
        "url": "(URL pending)",
    }

    def __missing__(self, key: str) -> str:
        return self._DEFAULTS.get(key, f"<{key}>")


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
