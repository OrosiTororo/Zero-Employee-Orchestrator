"""Autonomy boundary -- Determination of autonomously executable vs approval-required operations.

Defines the scope of AI autonomous execution based on Zero-Employee Orchestrator.md section 25.

Autonomously executable:
- Research, analysis, drafting, information organization

Approval required:
- Publishing, posting, billing, deletion, permission changes, external sends
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AutonomyLevel(str, Enum):
    """Agent autonomy level."""

    OBSERVE = "observe"  # Observation only
    ASSIST = "assist"  # Assistance (suggestions only)
    SEMI_AUTO = "semi_auto"  # Semi-automatic (execute after approval)
    AUTONOMOUS = "autonomous"  # Autonomous (auto-execute within safe boundaries)


# Operation types permitted for autonomous execution
AUTONOMOUS_OPERATIONS: set[str] = {
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
}


@dataclass
class AutonomyCheckResult:
    """Autonomy check result."""

    allowed: bool
    requires_approval: bool
    reason: str
    operation: str
    autonomy_level: AutonomyLevel


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
