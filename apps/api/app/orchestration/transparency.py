"""Transparency, fact-checking, and disclosure layer.

To prevent AI from becoming a black box:
1. Disclose sources and information referenced by AI to users
2. Present information needed for accurate approval decisions
3. Bidirectional fact-checking between AI and users
4. Facilitate dialogue and alignment during planning

This module attaches transparency metadata to all AI outputs,
ensuring users can reliably obtain the information needed for approval decisions.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class SourceType(str, Enum):
    """Source type of information referenced by AI."""

    WEB_PAGE = "web_page"  # Web page
    DOCUMENTATION = "documentation"  # Official documentation
    API_RESPONSE = "api_response"  # API response
    DATABASE = "database"  # Internal database
    USER_INPUT = "user_input"  # User input
    LLM_KNOWLEDGE = "llm_knowledge"  # LLM internal knowledge (with cutoff date)
    FILE_CONTENT = "file_content"  # Local file
    PLUGIN_MANIFEST = "plugin_manifest"  # Plugin manifest
    COMMUNITY_REGISTRY = "community_registry"  # Community registry


class ConfidenceLevel(str, Enum):
    """Information confidence level."""

    VERIFIED = "verified"  # Fact-checked
    HIGH = "high"  # High confidence
    MEDIUM = "medium"  # Medium
    LOW = "low"  # Low (includes speculation)
    UNVERIFIED = "unverified"  # Unverified


class ApprovalInfoType(str, Enum):
    """Type of information presented to users during approval."""

    COST = "cost"  # Cost / fees
    RISK = "risk"  # Risk
    PERMISSION = "permission"  # Required permissions
    EXTERNAL_ACCESS = "external_access"  # External access
    DATA_FLOW = "data_flow"  # Data flow
    REVERSIBILITY = "reversibility"  # Operation reversibility
    DEPENDENCY = "dependency"  # Dependencies
    SOURCE_REFERENCE = "source_reference"  # Source reference


@dataclass
class SourceReference:
    """Source reference for information referenced by AI."""

    source_type: SourceType
    title: str
    uri: str = ""  # URL or file path
    snippet: str = ""  # Excerpt of referenced section
    accessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    note: str = ""  # Supplementary information


@dataclass
class FactCheckItem:
    """Fact-check item."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    claim: str = ""  # AI claim
    sources: list[SourceReference] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    verified_by_user: bool = False
    user_feedback: str = ""  # Feedback from user
    needs_verification: bool = False  # Needs user verification


@dataclass
class ApprovalInfo:
    """Information needed for approval decisions."""

    info_type: ApprovalInfoType
    title: str
    detail: str
    severity: str = "info"  # info, warning, critical


@dataclass
class TransparencyReport:
    """Transparency report attached to AI outputs.

    Attached to all AI outputs (plans, proposals, operation results, etc.)
    to allow users to verify the basis for AI decisions.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Information sources referenced by AI
    sources: list[SourceReference] = field(default_factory=list)

    # Fact-check items
    fact_checks: list[FactCheckItem] = field(default_factory=list)

    # Information needed for approval
    approval_info: list[ApprovalInfo] = field(default_factory=list)

    # AI reasoning process summary
    reasoning_summary: str = ""

    # Points where AI is uncertain
    uncertainties: list[str] = field(default_factory=list)

    # Questions / confirmations for the user
    questions_for_user: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Transparency builder — helper for modules to build reports
# ---------------------------------------------------------------------------


class TransparencyBuilder:
    """Builder for incrementally constructing transparency reports.

    Each service / orchestration module uses this builder to record
    the basis for AI decisions, ultimately presented to users.
    """

    def __init__(self) -> None:
        self._report = TransparencyReport()

    def add_source(
        self,
        source_type: SourceType,
        title: str,
        uri: str = "",
        snippet: str = "",
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        note: str = "",
    ) -> TransparencyBuilder:
        """Add a source reference."""
        self._report.sources.append(
            SourceReference(
                source_type=source_type,
                title=title,
                uri=uri,
                snippet=snippet,
                confidence=confidence,
                note=note,
            )
        )
        return self

    def add_fact_check(
        self,
        claim: str,
        sources: list[SourceReference] | None = None,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        needs_verification: bool = False,
    ) -> TransparencyBuilder:
        """Add a fact-check item."""
        self._report.fact_checks.append(
            FactCheckItem(
                claim=claim,
                sources=sources or [],
                confidence=confidence,
                needs_verification=needs_verification,
            )
        )
        return self

    def add_approval_info(
        self,
        info_type: ApprovalInfoType | str,
        title: str,
        detail: str,
        severity: str = "info",
    ) -> TransparencyBuilder:
        """Add information needed for approval decisions."""
        if isinstance(info_type, str):
            info_type = ApprovalInfoType(info_type)
        self._report.approval_info.append(
            ApprovalInfo(
                info_type=info_type,
                title=title,
                detail=detail,
                severity=severity,
            )
        )
        return self

    def set_reasoning(self, summary: str) -> TransparencyBuilder:
        """Set the AI reasoning summary."""
        self._report.reasoning_summary = summary
        return self

    def add_uncertainty(self, uncertainty: str) -> TransparencyBuilder:
        """Add a point where AI is uncertain."""
        self._report.uncertainties.append(uncertainty)
        return self

    def add_question(self, question: str) -> TransparencyBuilder:
        """Add a confirmation item for the user."""
        self._report.questions_for_user.append(question)
        return self

    def build(self) -> TransparencyReport:
        """Generate the report."""
        return self._report

    def to_dict(self) -> dict:
        """Convert report to dict (for API responses)."""
        report = self._report
        return {
            "id": report.id,
            "created_at": report.created_at.isoformat(),
            "sources": [
                {
                    "type": s.source_type.value,
                    "title": s.title,
                    "uri": s.uri,
                    "snippet": s.snippet,
                    "confidence": s.confidence.value,
                    "note": s.note,
                }
                for s in report.sources
            ],
            "fact_checks": [
                {
                    "id": fc.id,
                    "claim": fc.claim,
                    "confidence": fc.confidence.value,
                    "needs_verification": fc.needs_verification,
                    "verified_by_user": fc.verified_by_user,
                    "sources": [
                        {"type": s.source_type.value, "title": s.title, "uri": s.uri}
                        for s in fc.sources
                    ],
                }
                for fc in report.fact_checks
            ],
            "approval_info": [
                {
                    "type": ai.info_type.value,
                    "title": ai.title,
                    "detail": ai.detail,
                    "severity": ai.severity,
                }
                for ai in report.approval_info
            ],
            "reasoning_summary": report.reasoning_summary,
            "uncertainties": report.uncertainties,
            "questions_for_user": report.questions_for_user,
        }


# ---------------------------------------------------------------------------
# Transparency report generation for plugin installation
# ---------------------------------------------------------------------------


def build_plugin_install_transparency(
    template: dict,
    env_report_dict: dict,
) -> dict:
    """Generate a transparency report for plugin installation.

    Before users install a plugin, clearly present:
    - What this plugin does
    - What external access is required
    - What costs are involved
    - What is safe and what is risky

    Args:
        template: Plugin template
        env_report_dict: Environment check results

    Returns:
        Transparency report dict
    """
    builder = TransparencyBuilder()

    # Source information
    source_uri = template.get("source_uri", "")
    if source_uri:
        builder.add_source(
            source_type=SourceType.WEB_PAGE,
            title=f"{template['name']} official repository",
            uri=source_uri,
            confidence=ConfidenceLevel.VERIFIED,
            note="Official source for plugin information",
        )

    pypi = template.get("pypi_package")
    if pypi:
        builder.add_source(
            source_type=SourceType.COMMUNITY_REGISTRY,
            title=f"PyPI: {pypi}",
            uri=f"https://pypi.org/project/{pypi}/",
            confidence=ConfidenceLevel.VERIFIED,
            note="Package public information",
        )

    builder.add_source(
        source_type=SourceType.PLUGIN_MANIFEST,
        title="ZEO Plugin Catalog",
        uri="",
        confidence=ConfidenceLevel.HIGH,
        note="Retrieved from ZEO internal plugin catalog",
    )

    # Fact-check items
    builder.add_fact_check(
        claim=f"{template['name']} is open source, license: {template.get('license', 'unknown')}",
        sources=[
            SourceReference(
                source_type=SourceType.WEB_PAGE,
                title="LICENSE",
                uri=source_uri,
                confidence=ConfidenceLevel.HIGH if source_uri else ConfidenceLevel.LOW,
            )
        ],
        confidence=ConfidenceLevel.HIGH if source_uri else ConfidenceLevel.LOW,
        needs_verification=not source_uri,
    )

    # Information needed for approval
    # Cost
    requirements = template.get("requirements", [])
    has_paid_api = any(
        r.get("type") == "api_key"
        and r.get("required", True)
        and "free" not in r.get("install_hint", "").lower()
        for r in requirements
    )
    if has_paid_api:
        builder.add_approval_info(
            info_type=ApprovalInfoType.COST,
            title="Potential API usage fees",
            detail=(
                "This plugin requires an external API key. "
                "API fees may apply depending on usage. "
                "If free tiers or alternatives exist, please review that information as well."
            ),
            severity="warning",
        )
    else:
        builder.add_approval_info(
            info_type=ApprovalInfoType.COST,
            title="No additional cost",
            detail="This plugin is free to use (local execution or free API).",
            severity="info",
        )

    # External access
    safety = template.get("safety", {})
    dangerous_ops = safety.get("dangerous_operations", [])
    if dangerous_ops:
        builder.add_approval_info(
            info_type=ApprovalInfoType.EXTERNAL_ACCESS,
            title="Operations that perform external access",
            detail=f"The following operations require approval: {', '.join(dangerous_ops)}",
            severity="warning",
        )

    # Data flow
    has_internet = any(
        r.get("type") in ("api_key", "env_var")
        or r.get("name", "") in ("SUNO_COOKIE", "SLACK_BOT_TOKEN")
        for r in requirements
    )
    if has_internet:
        builder.add_approval_info(
            info_type=ApprovalInfoType.DATA_FLOW,
            title="Communication with external services",
            detail="This plugin sends data to external services. Sent content is recorded in audit logs.",
            severity="warning",
        )

    # Permissions
    required_perms = template.get("required_permissions", [])
    if required_perms:
        builder.add_approval_info(
            info_type=ApprovalInfoType.PERMISSION,
            title="Required permissions",
            detail=f"Required permissions: {', '.join(required_perms)}",
            severity="info",
        )

    # Reversibility
    builder.add_approval_info(
        info_type=ApprovalInfoType.REVERSIBILITY,
        title="Can be uninstalled",
        detail="This plugin can be uninstalled at any time. The pip package will remain, but registration from ZEO will be removed.",
        severity="info",
    )

    # Reasoning summary
    builder.set_reasoning(
        f"Proposed installation of plugin '{template['name']}'."
        f"Category: {template.get('category', 'unknown')}. "
        f"Source: {source_uri or 'internal catalog'}."
    )

    # Uncertainties
    if not source_uri:
        builder.add_uncertainty("Plugin source URI is unknown. Safety verification is difficult.")

    if template.get("adapter", {}).get("class") is None:
        builder.add_uncertainty(
            "This plugin's adapter is not yet implemented. "
            "Either wait for community contributions or implement it manually."
        )

    # Questions for the user
    setup_instructions = env_report_dict.get("setup_instructions", [])
    if setup_instructions:
        builder.add_question(
            "Please review the following setup instructions:\n"
            + "\n".join(f"  - {s}" for s in setup_instructions)
        )

    return builder.to_dict()
