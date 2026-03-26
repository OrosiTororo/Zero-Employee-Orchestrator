"""Workspace isolation -- AI agent environment separation.

By default, AI agents operate only within a fully isolated workspace
and cannot access the local file system or cloud storage at all.

Users can gradually grant permissions through settings or chat instructions:
- Local folder access (only permitted folders)
- Cloud storage connections (only permitted providers/folders)
- Changing artifact storage locations

When different environments/permissions are instructed per task via chat,
the AI requests user permission during the planning stage.

Security principles:
- Default deny: All access not explicitly permitted is denied
- Least privilege: Only the minimum necessary access is granted
- Auditable: All access permission changes are recorded
- User sovereignty: AI does not expand access scope on its own
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

# Default path for internal storage
_DEFAULT_INTERNAL_STORAGE = os.path.join(os.path.expanduser("~"), ".zero_employee", "workspace")


class StorageLocation(str, Enum):
    """Artifact storage location."""

    INTERNAL = "internal"  # Within isolated workspace (default)
    LOCAL = "local"  # Local file system
    CLOUD = "cloud"  # Cloud storage


class CloudProvider(str, Enum):
    """Supported cloud storage providers."""

    GOOGLE_DRIVE = "google_drive"
    ONEDRIVE = "onedrive"
    DROPBOX = "dropbox"
    ICLOUD = "icloud"


class AccessScope(str, Enum):
    """Access scope."""

    INTERNAL_ONLY = "internal_only"  # Isolated environment only (default)
    LOCAL_ALLOWED = "local_allowed"  # Local folders also allowed
    CLOUD_ALLOWED = "cloud_allowed"  # Cloud also allowed
    FULL = "full"  # Local + cloud allowed


@dataclass
class WorkspaceConfig:
    """Workspace isolation configuration.

    Default is fully isolated. Local/cloud access becomes available
    only when explicitly permitted by the user.
    """

    # Internal storage path
    internal_storage_path: str = field(default_factory=lambda: _DEFAULT_INTERNAL_STORAGE)

    # Local access settings
    local_access_enabled: bool = False  # Default: disabled
    allowed_local_paths: list[str] = field(default_factory=list)

    # Cloud access settings
    cloud_access_enabled: bool = False  # Default: disabled
    cloud_providers: list[str] = field(default_factory=list)
    allowed_cloud_paths: list[str] = field(default_factory=list)

    # Artifact storage location
    storage_location: StorageLocation = StorageLocation.INTERNAL

    # Require approval when overriding via chat instructions
    require_approval_for_override: bool = True


@dataclass
class TaskWorkspaceOverride:
    """Per-task workspace override.

    Temporarily grants a different access scope for a specific task
    via chat instructions or API, differing from system settings.
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
    """Workspace access check result."""

    allowed: bool
    path: str
    reason: str
    requires_user_approval: bool = False
    suggested_message: str = ""


class WorkspaceIsolation:
    """Workspace isolation manager.

    Controls AI agent file and knowledge access.
    By default, only the isolated workspace is accessible.
    """

    def __init__(self, config: WorkspaceConfig | None = None) -> None:
        self._config = config or WorkspaceConfig()
        self._task_overrides: dict[str, TaskWorkspaceOverride] = {}
        self._ensure_internal_storage()

    @property
    def config(self) -> WorkspaceConfig:
        return self._config

    def update_config(self, config: WorkspaceConfig) -> None:
        """Update configuration."""
        self._config = config
        self._ensure_internal_storage()
        logger.info(
            "Workspace config updated: local=%s, cloud=%s, storage=%s",
            config.local_access_enabled,
            config.cloud_access_enabled,
            config.storage_location.value,
        )

    def _ensure_internal_storage(self) -> None:
        """Create internal storage directories."""
        base = Path(self._config.internal_storage_path)
        for subdir in ["knowledge", "artifacts", "temp"]:
            (base / subdir).mkdir(parents=True, exist_ok=True)

    def get_internal_storage_path(self) -> str:
        """Return the base path of internal storage."""
        return self._config.internal_storage_path

    def get_knowledge_path(self) -> str:
        """Return the knowledge storage path."""
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
                reason="Cloud storage access is disabled. Enable cloud access via settings.",
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

    def get_effective_storage_location(self, task_id: str | None = None) -> StorageLocation:
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
            "Task workspace override set: task=%s, approved=%s, local_paths=%d, cloud_sources=%d",
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
        self._config.cloud_providers = [p for p in self._config.cloud_providers if p != provider]
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
            elif (
                requested_storage == StorageLocation.CLOUD and not self._config.cloud_access_enabled
            ):
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
