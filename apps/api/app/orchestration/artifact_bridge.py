"""Artifact Bridge — 成果物の管理と工程間連携.

Zero-Employee Orchestrator.md の Layer 7 (State & Memory) で定義される
Artifact Bridge を実装する。工程間で成果物を受け渡し、バージョン管理
と再利用を可能にする。

Phase 2 で以下の機能を追加:
- Auto-linking: DAG の出力→入力を自動連携
- Cross-domain transformation: ドメイン間でアーティファクトタイプを変換
- Artifact compatibility matrix: 互換性マッピング
- Artifact search: 互換アーティファクトの検索
- Pipeline support: スキルチェーンのアーティファクトフロー構築
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ArtifactType(str, Enum):
    """成果物のタイプ."""

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
    # Phase 2: ドメインスキル固有のアーティファクトタイプ
    STRUCTURED_CONTENT = "structured_content"
    TREND_REPORT = "trend_report"
    COMPETITOR_REPORT = "competitor_report"
    PERFORMANCE_REPORT = "performance_report"
    STRATEGY_PLAN = "strategy_plan"
    MARKET_CONTEXT = "market_context"


class StorageType(str, Enum):
    """保存先のタイプ."""

    LOCAL = "local"
    DATABASE = "database"
    CLOUD = "cloud"
    INLINE = "inline"  # DB の JSON カラムに埋め込み


@dataclass
class ArtifactRef:
    """成果物への参照."""

    artifact_id: str
    title: str
    artifact_type: ArtifactType
    version: int = 1
    storage_type: StorageType = StorageType.LOCAL
    path_or_uri: str = ""
    mime_type: str = "application/octet-stream"
    summary: str = ""
    domain: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ArtifactBridgeResult:
    """Artifact Bridge の操作結果."""

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
    """2 つのアーティファクトタイプに互換性があるかチェックする."""
    if source_type == target_type:
        return True
    compatible_targets = ARTIFACT_COMPATIBILITY_MATRIX.get(source_type, [])
    return target_type in compatible_targets


# ---------------------------------------------------------------------------
# DAG node protocol (duck typing)
# ---------------------------------------------------------------------------


@dataclass
class _DagNode:
    """DAG ノードの最小プロトコル（テスト・型ヒント用）.

    実際のオーケストレーション DAG ノードは任意のオブジェクトで良いが、
    以下の属性を持っていれば auto_link_outputs_to_inputs で使える。
    """

    task_id: str
    skill_id: str = ""
    depends_on: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Skill registry integration helper
# ---------------------------------------------------------------------------

# Lazy import を避けるためのキャッシュ
_skill_artifact_cache: dict[str, dict[str, list[str]]] = {}


def _get_skill_artifact_info(skill_id: str) -> dict[str, list[str]]:
    """スキルの accepts / produces 情報を取得する.

    domain_skills が利用可能ならそちらから取得し、
    そうでなければ空のリストを返す。
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
    """工程間の成果物受け渡しを管理する.

    - タスク A の出力をタスク B の入力として連携
    - 成果物のバージョン管理
    - 成果物のメタデータ管理
    - Auto-linking: DAG 内の互換アーティファクトを自動連携
    - Cross-domain transformation: ドメイン間でアーティファクトタイプを変換
    - Artifact search: 互換アーティファクトの検索
    - Pipeline support: スキルチェーンのアーティファクトフロー構築
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
        """タスクの出力成果物を登録する."""
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
        """成果物をタスクの入力として紐づける."""
        if artifact_id not in self._artifacts:
            return False
        if task_id not in self._task_inputs:
            self._task_inputs[task_id] = []
        self._task_inputs[task_id].append(artifact_id)
        return True

    def get_task_inputs(self, task_id: str) -> list[ArtifactRef]:
        """タスクの入力成果物を取得する."""
        ids = self._task_inputs.get(task_id, [])
        return [self._artifacts[aid] for aid in ids if aid in self._artifacts]

    def get_task_outputs(self, task_id: str) -> list[ArtifactRef]:
        """タスクの出力成果物を取得する."""
        ids = self._task_outputs.get(task_id, [])
        return [self._artifacts[aid] for aid in ids if aid in self._artifacts]

    def get_artifact(self, artifact_id: str) -> ArtifactRef | None:
        return self._artifacts.get(artifact_id)

    def list_artifacts(
        self, artifact_type: ArtifactType | None = None
    ) -> list[ArtifactRef]:
        if artifact_type:
            return [
                a for a in self._artifacts.values() if a.artifact_type == artifact_type
            ]
        return list(self._artifacts.values())

    # ------------------------------------------------------------------
    # Phase 2: Auto-linking
    # ------------------------------------------------------------------

    def auto_link_outputs_to_inputs(
        self,
        dag: list[Any],
    ) -> list[dict[str, str]]:
        """DAG を走査し、互換性のある出力→入力を自動リンクする.

        各 DAG ノードは task_id, skill_id, depends_on 属性を持つことを前提とする。
        完了済みタスクの出力アーティファクトと、後続タスクが受け入れるタイプを
        マッチングし、互換性があれば自動的に link_input する。

        Args:
            dag: DAG ノードのリスト（task_id, skill_id, depends_on を持つ任意のオブジェクト）

        Returns:
            作成されたリンクのリスト [{"from_task": ..., "to_task": ..., "artifact_id": ..., "type": ...}, ...]
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
        """アーティファクトを別タイプとして再登録する（クロスドメイン変換）.

        元のアーティファクトを維持したまま、互換タイプの新しい ArtifactRef を
        作成して返す。互換性がなければ失敗を返す。

        Args:
            artifact_id: 変換元のアーティファクト ID
            target_type: 変換先のアーティファクトタイプ文字列

        Returns:
            ArtifactBridgeResult (成功時は新しい ArtifactRef を含む)
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
        """指定タイプに互換性のあるアーティファクトを検索する.

        Args:
            required_type: 必要なアーティファクトタイプ
            domain: 絞り込み用ドメイン（None なら全ドメイン）

        Returns:
            互換性のある ArtifactRef のリスト
        """
        results: list[ArtifactRef] = []

        for artifact in self._artifacts.values():
            # ドメインフィルタ
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
        """スキルチェーンを通じた成果物フローを計算する.

        各スキルが produces するタイプと次のスキルが accepts するタイプを
        マッチングし、パイプライン全体の期待フローを返す。

        Args:
            skill_chain: スキル ID のリスト（実行順）

        Returns:
            パイプラインステップのリスト:
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

            # 前のステップの出力と今のステップの入力の交差を計算
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


# グローバルインスタンス
artifact_bridge = ArtifactBridge()
