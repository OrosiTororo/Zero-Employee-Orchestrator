"""ワークスペース隔離 — AI エージェントの環境分離.

初期状態では AI エージェントは完全に隔離されたワークスペース内でのみ動作し、
ローカルファイルシステムやクラウドストレージには一切アクセスできない。

ユーザーは設定やチャットでの指示により、以下を段階的に許可できる:
- ローカルフォルダへのアクセス（許可したフォルダのみ）
- クラウドストレージへの接続（許可したプロバイダー・フォルダのみ）
- 成果物の保存先の変更

業務ごとにチャットで異なる環境・権限を指示された場合、
AI は計画段階でユーザーに許可を求める。

セキュリティ原則:
- デフォルト拒否: 明示的に許可されていないアクセスはすべて拒否
- 最小権限: 必要最小限のアクセスのみ許可
- 監査可能: すべてのアクセス許可変更を記録
- ユーザー主権: AI が勝手にアクセス範囲を拡大しない
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

# 内部ストレージのデフォルトパス
_DEFAULT_INTERNAL_STORAGE = os.path.join(
    os.path.expanduser("~"), ".zero_employee", "workspace"
)


class StorageLocation(str, Enum):
    """成果物の保存先."""

    INTERNAL = "internal"  # 隔離ワークスペース内（初期設定）
    LOCAL = "local"  # ローカルファイルシステム
    CLOUD = "cloud"  # クラウドストレージ


class CloudProvider(str, Enum):
    """対応クラウドストレージプロバイダー."""

    GOOGLE_DRIVE = "google_drive"
    ONEDRIVE = "onedrive"
    DROPBOX = "dropbox"
    ICLOUD = "icloud"


class AccessScope(str, Enum):
    """アクセス範囲."""

    INTERNAL_ONLY = "internal_only"  # 隔離環境のみ（初期設定）
    LOCAL_ALLOWED = "local_allowed"  # ローカルフォルダも許可
    CLOUD_ALLOWED = "cloud_allowed"  # クラウドも許可
    FULL = "full"  # ローカル + クラウド許可


@dataclass
class WorkspaceConfig:
    """ワークスペース隔離設定.

    初期設定では完全隔離状態。ユーザーが明示的に許可した場合のみ
    ローカル・クラウドへのアクセスが可能になる。
    """

    # 内部ストレージパス
    internal_storage_path: str = field(default_factory=lambda: _DEFAULT_INTERNAL_STORAGE)

    # ローカルアクセス設定
    local_access_enabled: bool = False  # 初期: 無効
    allowed_local_paths: list[str] = field(default_factory=list)

    # クラウドアクセス設定
    cloud_access_enabled: bool = False  # 初期: 無効
    cloud_providers: list[str] = field(default_factory=list)
    allowed_cloud_paths: list[str] = field(default_factory=list)

    # 成果物の保存先
    storage_location: StorageLocation = StorageLocation.INTERNAL

    # チャット指示によるオーバーライド時に承認を要求
    require_approval_for_override: bool = True


@dataclass
class TaskWorkspaceOverride:
    """業務（タスク）単位のワークスペースオーバーライド.

    チャットでの指示やAPI経由で、特定のタスクに対して
    システム設定とは異なるアクセス範囲を一時的に許可する。
    """

    task_id: str
    additional_local_paths: list[str] = field(default_factory=list)
    additional_cloud_sources: list[str] = field(default_factory=list)
    storage_location: StorageLocation | None = None
    output_path: str | None = None
    approved_by_user: bool = False
    reason: str = ""


@dataclass
class WorkspaceAccessResult:
    """ワークスペースアクセスチェック結果."""

    allowed: bool
    path: str
    reason: str
    requires_user_approval: bool = False
    suggested_message: str = ""


class WorkspaceIsolation:
    """ワークスペース隔離マネージャー.

    AI エージェントのファイル・ナレッジアクセスを制御する。
    初期状態では隔離ワークスペース内のみアクセス可能。
    """

    def __init__(self, config: WorkspaceConfig | None = None) -> None:
        self._config = config or WorkspaceConfig()
        self._task_overrides: dict[str, TaskWorkspaceOverride] = {}
        self._ensure_internal_storage()

    @property
    def config(self) -> WorkspaceConfig:
        return self._config

    def update_config(self, config: WorkspaceConfig) -> None:
        """設定を更新する."""
        self._config = config
        self._ensure_internal_storage()
        logger.info(
            "Workspace config updated: local=%s, cloud=%s, storage=%s",
            config.local_access_enabled,
            config.cloud_access_enabled,
            config.storage_location.value,
        )

    def _ensure_internal_storage(self) -> None:
        """内部ストレージディレクトリを作成する."""
        base = Path(self._config.internal_storage_path)
        for subdir in ["knowledge", "artifacts", "temp"]:
            (base / subdir).mkdir(parents=True, exist_ok=True)

    def get_internal_storage_path(self) -> str:
        """内部ストレージのベースパスを返す."""
        return self._config.internal_storage_path

    def get_knowledge_path(self) -> str:
        """ナレッジ格納パスを返す."""
        return str(Path(self._config.internal_storage_path) / "knowledge")

    def get_artifacts_path(self) -> str:
        """成果物格納パスを返す."""
        return str(Path(self._config.internal_storage_path) / "artifacts")

    def get_temp_path(self) -> str:
        """一時ファイルパスを返す."""
        return str(Path(self._config.internal_storage_path) / "temp")

    def check_access(
        self,
        path: str,
        *,
        task_id: str | None = None,
    ) -> WorkspaceAccessResult:
        """パスへのアクセスが許可されているかチェックする.

        Args:
            path: チェック対象のパス
            task_id: タスクID（タスク単位のオーバーライドをチェック）

        Returns:
            WorkspaceAccessResult: アクセス可否と理由
        """
        try:
            resolved = str(Path(path).resolve())
        except (ValueError, OSError) as exc:
            return WorkspaceAccessResult(
                allowed=False,
                path=path,
                reason=f"Invalid path: {exc}",
            )

        # 1. 内部ストレージへのアクセスは常に許可
        internal_resolved = str(Path(self._config.internal_storage_path).resolve())
        if resolved.startswith(internal_resolved):
            return WorkspaceAccessResult(
                allowed=True,
                path=resolved,
                reason="Path is within internal workspace storage",
            )

        # 2. タスク単位のオーバーライドをチェック
        if task_id and task_id in self._task_overrides:
            override = self._task_overrides[task_id]
            if override.approved_by_user:
                for allowed in override.additional_local_paths:
                    allowed_resolved = str(Path(allowed).resolve())
                    if resolved.startswith(allowed_resolved):
                        return WorkspaceAccessResult(
                            allowed=True,
                            path=resolved,
                            reason=f"Task override: path allowed for task {task_id}",
                        )

        # 3. ローカルアクセスが有効かチェック
        if not self._config.local_access_enabled:
            return WorkspaceAccessResult(
                allowed=False,
                path=resolved,
                reason="Local filesystem access is disabled. "
                "Only files in the internal workspace are accessible. "
                "Enable local access via settings or upload files to the workspace.",
                requires_user_approval=True,
                suggested_message=(
                    "このパスへのアクセスにはローカルファイルアクセスの許可が必要です。\n"
                    f"対象: {resolved}\n"
                    "設定でローカルアクセスを有効にするか、"
                    "ファイルをワークスペースにアップロードしてください。\n"
                    "[ローカルアクセスを有効にする] [このタスクのみ許可] [キャンセル]"
                ),
            )

        # 4. 許可されたローカルパスに含まれるかチェック
        for allowed in self._config.allowed_local_paths:
            allowed_resolved = str(Path(allowed).resolve())
            if resolved.startswith(allowed_resolved):
                return WorkspaceAccessResult(
                    allowed=True,
                    path=resolved,
                    reason=f"Path is within allowed local directory: {allowed}",
                )

        return WorkspaceAccessResult(
            allowed=False,
            path=resolved,
            reason=f"Path is not in allowed local directories. "
            f"Allowed: {self._config.allowed_local_paths}",
            requires_user_approval=True,
            suggested_message=(
                "このフォルダへのアクセスは現在許可されていません。\n"
                f"対象: {resolved}\n"
                "このフォルダへのアクセスを許可しますか？\n"
                "[このタスクのみ許可] [恒久的に許可] [拒否]"
            ),
        )

    def check_cloud_access(
        self,
        provider: str,
        cloud_path: str = "",
        *,
        task_id: str | None = None,
    ) -> WorkspaceAccessResult:
        """クラウドストレージへのアクセスが許可されているかチェックする."""
        # タスクオーバーライドをチェック
        if task_id and task_id in self._task_overrides:
            override = self._task_overrides[task_id]
            if override.approved_by_user:
                source = f"{provider}://{cloud_path}"
                for allowed in override.additional_cloud_sources:
                    if source.startswith(allowed):
                        return WorkspaceAccessResult(
                            allowed=True,
                            path=source,
                            reason=f"Task override: cloud access allowed for task {task_id}",
                        )

        if not self._config.cloud_access_enabled:
            return WorkspaceAccessResult(
                allowed=False,
                path=f"{provider}://{cloud_path}",
                reason="Cloud storage access is disabled. "
                "Enable cloud access via settings.",
                requires_user_approval=True,
                suggested_message=(
                    "クラウドストレージへのアクセスは現在無効です。\n"
                    f"プロバイダー: {provider}\n"
                    "設定でクラウドアクセスを有効にしますか？\n"
                    "[有効にする] [このタスクのみ許可] [キャンセル]"
                ),
            )

        if provider not in self._config.cloud_providers:
            return WorkspaceAccessResult(
                allowed=False,
                path=f"{provider}://{cloud_path}",
                reason=f"Cloud provider '{provider}' is not configured. "
                f"Configured: {self._config.cloud_providers}",
                requires_user_approval=True,
                suggested_message=(
                    f"クラウドプロバイダー '{provider}' は設定されていません。\n"
                    "接続を追加しますか？\n"
                    "[接続する] [キャンセル]"
                ),
            )

        return WorkspaceAccessResult(
            allowed=True,
            path=f"{provider}://{cloud_path}",
            reason=f"Cloud provider '{provider}' is configured and allowed",
        )

    def get_effective_storage_location(
        self, task_id: str | None = None
    ) -> StorageLocation:
        """有効な保存先を取得する（タスクオーバーライドを考慮）."""
        if task_id and task_id in self._task_overrides:
            override = self._task_overrides[task_id]
            if override.approved_by_user and override.storage_location:
                return override.storage_location
        return self._config.storage_location

    def set_task_override(self, override: TaskWorkspaceOverride) -> None:
        """タスク単位のワークスペースオーバーライドを設定する."""
        self._task_overrides[override.task_id] = override
        logger.info(
            "Task workspace override set: task=%s, approved=%s, "
            "local_paths=%d, cloud_sources=%d",
            override.task_id,
            override.approved_by_user,
            len(override.additional_local_paths),
            len(override.additional_cloud_sources),
        )

    def approve_task_override(self, task_id: str) -> bool:
        """タスクオーバーライドをユーザー承認する."""
        if task_id in self._task_overrides:
            self._task_overrides[task_id].approved_by_user = True
            logger.info("Task workspace override approved: task=%s", task_id)
            return True
        return False

    def remove_task_override(self, task_id: str) -> None:
        """タスクオーバーライドを削除する."""
        self._task_overrides.pop(task_id, None)

    def add_allowed_local_path(self, path: str) -> None:
        """許可ローカルパスを追加する."""
        resolved = str(Path(path).resolve())
        if resolved not in self._config.allowed_local_paths:
            self._config.allowed_local_paths.append(resolved)
            logger.info("Workspace: local path allowed: %s", resolved)

    def remove_allowed_local_path(self, path: str) -> None:
        """許可ローカルパスを削除する."""
        resolved = str(Path(path).resolve())
        self._config.allowed_local_paths = [
            p for p in self._config.allowed_local_paths if p != resolved
        ]
        logger.info("Workspace: local path removed: %s", resolved)

    def add_cloud_provider(self, provider: str) -> None:
        """クラウドプロバイダーを追加する."""
        if provider not in self._config.cloud_providers:
            self._config.cloud_providers.append(provider)
            logger.info("Workspace: cloud provider added: %s", provider)

    def remove_cloud_provider(self, provider: str) -> None:
        """クラウドプロバイダーを削除する."""
        self._config.cloud_providers = [
            p for p in self._config.cloud_providers if p != provider
        ]
        logger.info("Workspace: cloud provider removed: %s", provider)

    def get_access_scope(self) -> AccessScope:
        """現在のアクセス範囲を返す."""
        local = self._config.local_access_enabled
        cloud = self._config.cloud_access_enabled
        if local and cloud:
            return AccessScope.FULL
        if local:
            return AccessScope.LOCAL_ALLOWED
        if cloud:
            return AccessScope.CLOUD_ALLOWED
        return AccessScope.INTERNAL_ONLY

    def should_request_approval(
        self,
        requested_paths: list[str] | None = None,
        requested_cloud: list[str] | None = None,
        requested_storage: StorageLocation | None = None,
    ) -> WorkspaceAccessResult | None:
        """チャット指示がシステム設定と異なる場合、承認が必要かチェックする.

        AI が計画段階で呼び出し、ユーザーに許可を求めるべきかを判定する。

        Returns:
            承認が必要な場合は WorkspaceAccessResult、不要なら None
        """
        issues: list[str] = []

        if requested_paths:
            for p in requested_paths:
                result = self.check_access(p)
                if not result.allowed:
                    issues.append(f"ローカルパス: {p}")

        if requested_cloud:
            for c in requested_cloud:
                parts = c.split("://", 1)
                provider = parts[0] if len(parts) > 1 else c
                path = parts[1] if len(parts) > 1 else ""
                result = self.check_cloud_access(provider, path)
                if not result.allowed:
                    issues.append(f"クラウド: {c}")

        if requested_storage and requested_storage != self._config.storage_location:
            if requested_storage == StorageLocation.LOCAL and not self._config.local_access_enabled:
                issues.append(f"保存先: {requested_storage.value}（ローカルアクセス未許可）")
            elif requested_storage == StorageLocation.CLOUD and not self._config.cloud_access_enabled:
                issues.append(f"保存先: {requested_storage.value}（クラウドアクセス未許可）")

        if not issues:
            return None

        items = "\n".join(f"  - {issue}" for issue in issues)
        return WorkspaceAccessResult(
            allowed=False,
            path="",
            reason="Chat instructions require access beyond current workspace settings",
            requires_user_approval=True,
            suggested_message=(
                "この業務の指示には、現在のワークスペース設定を超えるアクセスが必要です。\n"
                "以下のアクセスを許可しますか？\n"
                f"{items}\n"
                "[このタスクのみ許可] [設定を恒久変更] [拒否]"
            ),
        )


# グローバルインスタンス（初期設定: 完全隔離）
workspace_isolation = WorkspaceIsolation()
