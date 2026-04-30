"""Autonomy boundary -- Determination of autonomously executable vs approval-required operations.

Defines the scope of AI autonomous execution based on Zero-Employee Orchestrator.md section 25.

Autonomously executable:
- Research, analysis, drafting, information organization

Approval required:
- Publishing, posting, billing, deletion, permission changes, external sends
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AutonomyLevel(str, Enum):
    """Agent autonomy level."""

    OBSERVE = "observe"  # Observation only
    ASSIST = "assist"  # Assistance (suggestions only)
    SEMI_AUTO = "semi_auto"  # Semi-automatic (execute after approval)
    AUTONOMOUS = "autonomous"  # Autonomous (auto-execute within safe boundaries)


# Operation types permitted for autonomous execution
AUTONOMOUS_OPERATIONS: set[str] = {
    "execute",
    "research",
    "analyze",
    "draft",
    "summarize",
    "organize",
    "translate",
    "calculate",
    "compare",
    "search",
    "read_file",
    "format",
    "classify",
    "extract",
    # Browser read-only operations (Cowork: read < write hierarchy)
    "browser_navigate",
    "browser_screenshot",
}

# Operation types that require approval
APPROVAL_REQUIRED_OPERATIONS: set[str] = {
    "publish",
    "post",
    "send",
    "delete",
    "charge",
    "change_permission",
    "change_credential",
    "git_push",
    "git_release",
    "overwrite_important_file",
    "external_api_write",
    "create_agent",
    "modify_policy",
    # Browser write/interact operations (Cowork: per-action approval)
    "browser_click",
    "browser_type",
    "browser_fill_form",
    "browser_submit_form",
    "browser_download",
    "browser_login",
    "browser_payment",
    "browser_extract_data",
    # Web AI sessions
    "web_ai_session",
}


@dataclass
class AutonomyCheckResult:
    """Autonomy check result."""

    allowed: bool
    requires_approval: bool
    reason: str
    operation: str
    autonomy_level: AutonomyLevel


async def resolve_effective_autonomy(
    db: AsyncSession,
    user_id: uuid.UUID,
    company_default: AutonomyLevel = AutonomyLevel.SEMI_AUTO,
) -> tuple[AutonomyLevel, datetime | None]:
    """Return ``(effective_level, override_expires_at)`` for the given user.

    A non-expired :class:`AutonomySessionOverride` always wins over the
    company-level default. If no override (or only expired ones) exists, the
    company default is returned with ``None`` for the expiry.
    """
    from sqlalchemy import select

    from app.models.autonomy_override import AutonomySessionOverride

    now = datetime.now(UTC).replace(tzinfo=None)
    stmt = (
        select(AutonomySessionOverride)
        .where(AutonomySessionOverride.user_id == user_id)
        .where(AutonomySessionOverride.expires_at > now)
        .order_by(AutonomySessionOverride.created_at.desc())
        .limit(1)
    )
    res = await db.execute(stmt)
    override = res.scalar_one_or_none()
    if override:
        try:
            return AutonomyLevel(override.autonomy_level), override.expires_at
        except ValueError:
            # Stored value is no longer a recognised level — fall through to
            # the company default rather than raising on every request.
            pass
    return company_default, None


def check_autonomy(
    operation: str,
    agent_autonomy_level: AutonomyLevel = AutonomyLevel.SEMI_AUTO,
) -> AutonomyCheckResult:
    """Determine whether an operation can be executed autonomously."""
    if operation in APPROVAL_REQUIRED_OPERATIONS:
        return AutonomyCheckResult(
            allowed=False,
            requires_approval=True,
            reason=f"Operation '{operation}' requires approval",
            operation=operation,
            autonomy_level=agent_autonomy_level,
        )

    if operation in AUTONOMOUS_OPERATIONS:
        if agent_autonomy_level in (AutonomyLevel.AUTONOMOUS, AutonomyLevel.SEMI_AUTO):
            return AutonomyCheckResult(
                allowed=True,
                requires_approval=False,
                reason=f"Operation '{operation}' can be executed autonomously",
                operation=operation,
                autonomy_level=agent_autonomy_level,
            )

    # Default: request approval for semi-auto and above, deny for observe/assist
    if agent_autonomy_level == AutonomyLevel.OBSERVE:
        return AutonomyCheckResult(
            allowed=False,
            requires_approval=False,
            reason="Cannot execute in observation mode",
            operation=operation,
            autonomy_level=agent_autonomy_level,
        )

    return AutonomyCheckResult(
        allowed=False,
        requires_approval=True,
        reason=f"Operation '{operation}' is unknown and requires approval",
        operation=operation,
        autonomy_level=agent_autonomy_level,
    )
