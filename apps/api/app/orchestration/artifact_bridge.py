"""Artifact Bridge — 成果物の管理と工程間連携.

Zero-Employee Orchestrator.md の Layer 7 (State & Memory) で定義される
Artifact Bridge を実装する。工程間で成果物を受け渡し、バージョン管理
と再利用を可能にする。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ArtifactBridgeResult:
    """Artifact Bridge の操作結果."""

    success: bool
    artifact: ArtifactRef | None = None
    message: str = ""


class ArtifactBridge:
    """工程間の成果物受け渡しを管理する.

    - タスク A の出力をタスク B の入力として連携
    - 成果物のバージョン管理
    - 成果物のメタデータ管理
    """

    def __init__(self) -> None:
        self._artifacts: dict[str, ArtifactRef] = {}
        self._task_outputs: dict[str, list[str]] = {}  # task_id -> [artifact_id, ...]
        self._task_inputs: dict[str, list[str]] = {}   # task_id -> [artifact_id, ...]

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

    def list_artifacts(self, artifact_type: ArtifactType | None = None) -> list[ArtifactRef]:
        if artifact_type:
            return [a for a in self._artifacts.values() if a.artifact_type == artifact_type]
        return list(self._artifacts.values())


# グローバルインスタンス
artifact_bridge = ArtifactBridge()
