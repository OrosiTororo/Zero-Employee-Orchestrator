"""Artifact Bridge — Artifact management and inter-stage coordination.

Implements the Artifact Bridge defined in Layer 7 (State & Memory) of
Zero-Employee Orchestrator.md. Enables artifact handoff between stages
with version management and reuse.

Phase 2 additions:
- Auto-linking: Automatic DAG output-to-input linking
- Cross-domain transformation: Convert artifact types across domains
- Artifact compatibility matrix: Compatibility mapping
- Artifact search: Search for compatible artifacts
- Pipeline support: Build artifact flow for skill chains
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ArtifactType(str, Enum):
    """Artifact type."""

    DOCUMENT = "document"
    CODE = "code"
    DATA = "data"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    SPEC = "spec"
    PLAN = "plan"
    REPORT = "report"
    CONFIG = "config"
    LOG = "log"
    # Phase 2: Domain skill-specific artifact types
    STRUCTURED_CONTENT = "structured_content"
    TREND_REPORT = "trend_report"
    COMPETITOR_REPORT = "competitor_report"
    PERFORMANCE_REPORT = "performance_report"
    STRATEGY_PLAN = "strategy_plan"
    MARKET_CONTEXT = "market_context"


class StorageType(str, Enum):
    """Storage type."""

    LOCAL = "local"
    DATABASE = "database"
    CLOUD = "cloud"
    INLINE = "inline"  # Embedded in DB JSON column


@dataclass
class ArtifactRef:
    """Reference to an artifact."""

    artifact_id: str
    title: str
    artifact_type: ArtifactType
    version: int = 1
    storage_type: StorageType = StorageType.LOCAL
    path_or_uri: str = ""
    mime_type: str = "application/octet-stream"
    summary: str = ""
    domain: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ArtifactBridgeResult:
    """Artifact Bridge operation result."""

    success: bool
    artifact: ArtifactRef | None = None
    message: str = ""


# ---------------------------------------------------------------------------
# Artifact Compatibility Matrix
# ---------------------------------------------------------------------------
# source_type -> list of target_types it can be auto-converted to.
# This enables cross-domain artifact reuse: e.g. a trend_report from
# TrendAnalysis can serve as market_context input for ContentCreator.
# ---------------------------------------------------------------------------

ARTIFACT_COMPATIBILITY_MATRIX: dict[str, list[str]] = {
    # Domain-specific reports -> generic types
    "trend_report": ["market_context", "report", "document", "data"],
    "competitor_report": ["market_context", "report", "document", "data"],
    "performance_report": ["report", "document", "data"],
    "strategy_plan": ["plan", "report", "document"],
    "structured_content": ["document"],
    "market_context": ["document", "data"],
    # Generic types -> broader types
    "spec": ["document"],
    "plan": ["document"],
    "report": ["document"],
    "data": ["document"],
    # Identity (every type is compatible with itself -- implicit, handled in code)
}


def _are_types_compatible(source_type: str, target_type: str) -> bool:
    """Check if two artifact types are compatible."""
    if source_type == target_type:
        return True
    compatible_targets = ARTIFACT_COMPATIBILITY_MATRIX.get(source_type, [])
    return target_type in compatible_targets


# ---------------------------------------------------------------------------
# DAG node protocol (duck typing)
# ---------------------------------------------------------------------------


@dataclass
class _DagNode:
    """Minimal protocol for DAG nodes (for testing and type hints).

    Actual orchestration DAG nodes can be any object, but if they have
    the following attributes, they can be used with auto_link_outputs_to_inputs.
    """

    task_id: str
    skill_id: str = ""
    depends_on: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Skill registry integration helper
# ---------------------------------------------------------------------------

# Cache to avoid lazy imports
_skill_artifact_cache: dict[str, dict[str, list[str]]] = {}


def _get_skill_artifact_info(skill_id: str) -> dict[str, list[str]]:
    """Get a skill's accepts/produces artifact type information.

    Retrieves from domain_skills if available,
    otherwise returns empty lists.
    """
    if skill_id in _skill_artifact_cache:
        return _skill_artifact_cache[skill_id]

    try:
        from skills.builtin.domain_skills import get_domain_skill_by_id

        cls = get_domain_skill_by_id(skill_id)
        if cls is not None:
            info = {
                "accepts": cls.accepts_artifact_types(),
                "produces": cls.produces_artifact_types(),
            }
            _skill_artifact_cache[skill_id] = info
            return info
    except ImportError:
        pass

    return {"accepts": [], "produces": []}


# ---------------------------------------------------------------------------
# ArtifactBridge
# ---------------------------------------------------------------------------


class ArtifactBridge:
    """Manage artifact handoff between stages.

    - Link task A's output as task B's input
    - Artifact version management
    - Artifact metadata management
    - Auto-linking: Automatically link compatible artifacts within a DAG
    - Cross-domain transformation: Convert artifact types across domains
    - Artifact search: Search for compatible artifacts
    - Pipeline support: Build artifact flow for skill chains
    """

    def __init__(self) -> None:
        self._artifacts: dict[str, ArtifactRef] = {}
        self._task_outputs: dict[str, list[str]] = {}  # task_id -> [artifact_id, ...]
        self._task_inputs: dict[str, list[str]] = {}  # task_id -> [artifact_id, ...]

    # ------------------------------------------------------------------
    # Existing methods (backward compatible)
    # ------------------------------------------------------------------

    def register_output(
        self,
        task_id: str,
        title: str,
        artifact_type: ArtifactType,
        *,
        content_or_path: str = "",
        mime_type: str = "text/plain",
        summary: str = "",
        storage_type: StorageType = StorageType.INLINE,
        domain: str = "",
    ) -> ArtifactRef:
        """Register a task's output artifact."""
        artifact_id = str(uuid.uuid4())
        ref = ArtifactRef(
            artifact_id=artifact_id,
            title=title,
            artifact_type=artifact_type,
            storage_type=storage_type,
            path_or_uri=content_or_path,
            mime_type=mime_type,
            summary=summary,
            domain=domain,
        )
        self._artifacts[artifact_id] = ref

        if task_id not in self._task_outputs:
            self._task_outputs[task_id] = []
        self._task_outputs[task_id].append(artifact_id)

        return ref

    def link_input(self, task_id: str, artifact_id: str) -> bool:
        """Link an artifact as a task's input."""
        if artifact_id not in self._artifacts:
            return False
        if task_id not in self._task_inputs:
            self._task_inputs[task_id] = []
        self._task_inputs[task_id].append(artifact_id)
        return True

    def get_task_inputs(self, task_id: str) -> list[ArtifactRef]:
        """Get a task's input artifacts."""
        ids = self._task_inputs.get(task_id, [])
        return [self._artifacts[aid] for aid in ids if aid in self._artifacts]

    def get_task_outputs(self, task_id: str) -> list[ArtifactRef]:
        """Get a task's output artifacts."""
        ids = self._task_outputs.get(task_id, [])
        return [self._artifacts[aid] for aid in ids if aid in self._artifacts]

    def get_artifact(self, artifact_id: str) -> ArtifactRef | None:
        return self._artifacts.get(artifact_id)

    def list_artifacts(self, artifact_type: ArtifactType | None = None) -> list[ArtifactRef]:
        if artifact_type:
            return [a for a in self._artifacts.values() if a.artifact_type == artifact_type]
        return list(self._artifacts.values())

    # ------------------------------------------------------------------
    # Phase 2: Auto-linking
    # ------------------------------------------------------------------

    def auto_link_outputs_to_inputs(
        self,
        dag: list[Any],
    ) -> list[dict[str, str]]:
        """Traverse the DAG and automatically link compatible outputs to inputs.

        Assumes each DAG node has task_id, skill_id, and depends_on attributes.
        Matches completed tasks' output artifacts with the types accepted by
        downstream tasks, and automatically calls link_input when compatible.

        Args:
            dag: List of DAG nodes (any objects with task_id, skill_id, depends_on)

        Returns:
            List of created links [{"from_task": ..., "to_task": ..., "artifact_id": ..., "type": ...}, ...]
        """
        links_created: list[dict[str, str]] = []

        # Build lookup: task_id -> node
        node_map: dict[str, Any] = {}
        for node in dag:
            tid = getattr(node, "task_id", None)
            if tid is not None:
                node_map[tid] = node

        for node in dag:
            task_id = getattr(node, "task_id", None)
            skill_id = getattr(node, "skill_id", "")
            depends_on = getattr(node, "depends_on", [])

            if not task_id or not depends_on:
                continue

            # What does this task's skill accept?
            skill_info = _get_skill_artifact_info(skill_id)
            accepted_types = skill_info["accepts"]

            if not accepted_types:
                continue

            for dep_task_id in depends_on:
                outputs = self.get_task_outputs(dep_task_id)
                for artifact in outputs:
                    source_type = (
                        artifact.artifact_type.value
                        if isinstance(artifact.artifact_type, ArtifactType)
                        else str(artifact.artifact_type)
                    )

                    for accepted in accepted_types:
                        if _are_types_compatible(source_type, accepted):
                            if self.link_input(task_id, artifact.artifact_id):
                                links_created.append(
                                    {
                                        "from_task": dep_task_id,
                                        "to_task": task_id,
                                        "artifact_id": artifact.artifact_id,
                                        "source_type": source_type,
                                        "matched_as": accepted,
                                    }
                                )
                            break  # one match per artifact is sufficient

        return links_created

    # ------------------------------------------------------------------
    # Phase 2: Cross-domain transformation
    # ------------------------------------------------------------------

    def transform_artifact(
        self,
        artifact_id: str,
        target_type: str,
    ) -> ArtifactBridgeResult:
        """Re-register an artifact as a different type (cross-domain transformation).

        Creates and returns a new ArtifactRef of a compatible type while
        preserving the original artifact. Returns failure if incompatible.

        Args:
            artifact_id: Source artifact ID
            target_type: Target artifact type string

        Returns:
            ArtifactBridgeResult (contains new ArtifactRef on success)
        """
        source = self._artifacts.get(artifact_id)
        if source is None:
            return ArtifactBridgeResult(
                success=False,
                message=f"Artifact not found: {artifact_id}",
            )

        source_type = (
            source.artifact_type.value
            if isinstance(source.artifact_type, ArtifactType)
            else str(source.artifact_type)
        )

        if not _are_types_compatible(source_type, target_type):
            return ArtifactBridgeResult(
                success=False,
                message=(
                    f"Incompatible types: '{source_type}' cannot be converted to '{target_type}'. "
                    f"Compatible targets: {ARTIFACT_COMPATIBILITY_MATRIX.get(source_type, [])}"
                ),
            )

        # Resolve ArtifactType enum for the target
        try:
            new_type = ArtifactType(target_type)
        except ValueError:
            new_type = ArtifactType.DOCUMENT  # fallback for unrecognised enum values

        new_id = str(uuid.uuid4())
        transformed = ArtifactRef(
            artifact_id=new_id,
            title=f"{source.title} (as {target_type})",
            artifact_type=new_type,
            version=source.version,
            storage_type=source.storage_type,
            path_or_uri=source.path_or_uri,
            mime_type=source.mime_type,
            summary=f"Transformed from {source_type}: {source.summary}",
            domain=source.domain,
        )
        self._artifacts[new_id] = transformed

        return ArtifactBridgeResult(
            success=True,
            artifact=transformed,
            message=f"Transformed '{source_type}' -> '{target_type}'",
        )

    # ------------------------------------------------------------------
    # Phase 2: Artifact search
    # ------------------------------------------------------------------

    def find_compatible_artifacts(
        self,
        required_type: str,
        domain: str | None = None,
    ) -> list[ArtifactRef]:
        """Search for artifacts compatible with the specified type.

        Args:
            required_type: Required artifact type
            domain: Domain filter (None for all domains)

        Returns:
            List of compatible ArtifactRef objects
        """
        results: list[ArtifactRef] = []

        for artifact in self._artifacts.values():
            # Domain filter
            if domain is not None and artifact.domain and artifact.domain != domain:
                continue

            source_type = (
                artifact.artifact_type.value
                if isinstance(artifact.artifact_type, ArtifactType)
                else str(artifact.artifact_type)
            )

            if _are_types_compatible(source_type, required_type):
                results.append(artifact)

        return results

    # ------------------------------------------------------------------
    # Phase 2: Pipeline support
    # ------------------------------------------------------------------

    def build_artifact_pipeline(
        self,
        skill_chain: list[str],
    ) -> list[dict[str, Any]]:
        """Calculate the artifact flow through a skill chain.

        Matches each skill's produced types with the next skill's accepted types,
        and returns the expected flow for the entire pipeline.

        Args:
            skill_chain: List of skill IDs (in execution order)

        Returns:
            List of pipeline steps:
            [
                {
                    "step": 0,
                    "skill_id": "trend-analysis",
                    "accepts": [...],
                    "produces": [...],
                    "auto_linked_from_previous": [...],
                },
                ...
            ]
        """
        pipeline: list[dict[str, Any]] = []
        previous_produces: list[str] = []

        for step_idx, skill_id in enumerate(skill_chain):
            info = _get_skill_artifact_info(skill_id)
            accepts = info["accepts"]
            produces = info["produces"]

            # Calculate intersection of previous step's outputs and current step's inputs
            auto_linked: list[dict[str, str]] = []
            for prev_type in previous_produces:
                for acc_type in accepts:
                    if _are_types_compatible(prev_type, acc_type):
                        auto_linked.append(
                            {
                                "source_type": prev_type,
                                "matched_as": acc_type,
                            }
                        )

            pipeline.append(
                {
                    "step": step_idx,
                    "skill_id": skill_id,
                    "accepts": accepts,
                    "produces": produces,
                    "auto_linked_from_previous": auto_linked,
                }
            )

            previous_produces = produces

        return pipeline


# Global instance
artifact_bridge = ArtifactBridge()
