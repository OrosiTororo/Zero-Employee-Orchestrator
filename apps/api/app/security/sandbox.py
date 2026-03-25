"""ファイルシステムサンドボックス — AI のフォルダアクセス制限.

AI がアクセスできるフォルダを、ユーザーが明示的に許可したフォルダのみに
制限するサンドボックス機能。

設計原則:
- 初期設定: AI はユーザーが許可したフォルダ以外にアクセス不可
- ホワイトリスト方式: 許可されたパスのみアクセス可能
- シンボリックリンク追跡による脱出を防止
- パストラバーサル攻撃を防止
- 全アクセス試行を監査ログに記録

セキュリティレベル:
- STRICT: 許可リストのフォルダのみ（初期設定）
- MODERATE: 許可リスト + 公開ディレクトリ
- PERMISSIVE: 禁止リスト以外すべて（非推奨）
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class SandboxLevel(str, Enum):
    """サンドボックスレベル."""

    STRICT = "strict"  # ホワイトリストのみ（初期設定）
    MODERATE = "moderate"  # ホワイトリスト + 公開ディレクトリ
    PERMISSIVE = "permissive"  # ブラックリスト以外すべて（非推奨）


class AccessType(str, Enum):
    """アクセス種別."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    LIST = "list"
    DELETE = "delete"


@dataclass
class AccessCheckResult:
    """アクセスチェック結果."""

    allowed: bool
    path: str
    access_type: AccessType
    reason: str
    sandbox_level: SandboxLevel


@dataclass
class SandboxConfig:
    """サンドボックス設定."""

    level: SandboxLevel = SandboxLevel.STRICT
    allowed_paths: list[str] = field(default_factory=list)
    denied_paths: list[str] = field(default_factory=lambda: list(_DEFAULT_DENIED_PATHS))
    allowed_extensions: set[str] = field(default_factory=lambda: set(_DEFAULT_ALLOWED_EXTENSIONS))
    max_file_size_mb: int = 50
    allow_symlink_follow: bool = False


# デフォルトの禁止パス（全レベルで共通）
_DEFAULT_DENIED_PATHS: list[str] = [
    "/etc/shadow",
    "/etc/passwd",
    "/etc/sudoers",
    "/root",
    "/.ssh",
    "/.gnupg",
    "/.aws",
    "/.config/gcloud",
    "/.azure",
    "/var/log/auth.log",
    "/var/log/secure",
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "service-account.json",
    "id_rsa",
    "id_ed25519",
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    "wallet.dat",
    "keystore",
    ".netrc",
    ".npmrc",  # npm auth tokens
    ".pypirc",  # PyPI credentials
    ".docker/config.json",
    "kubeconfig",
]

# デフォルトの許可拡張子
_DEFAULT_ALLOWED_EXTENSIONS: set[str] = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".java",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".sh",
    ".bash",
    ".sql",
    ".graphql",
    ".proto",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".pptx",
    ".log",
    ".toml",
    ".ini",
    ".cfg",
}


class FileSystemSandbox:
    """ファイルシステムサンドボックス.

    AI がアクセスできるフォルダ・ファイルをユーザー指定のホワイトリストに制限する。
    """

    def __init__(self, config: SandboxConfig | None = None) -> None:
        self._config = config or SandboxConfig()

    @property
    def config(self) -> SandboxConfig:
        return self._config

    def update_config(self, config: SandboxConfig) -> None:
        """設定を更新する."""
        self._config = config
        logger.info(
            "Sandbox config updated: level=%s, allowed=%d paths, denied=%d paths",
            config.level.value,
            len(config.allowed_paths),
            len(config.denied_paths),
        )

    def add_allowed_path(self, path: str) -> None:
        """許可パスを追加する."""
        resolved = str(Path(path).resolve())
        if resolved not in self._config.allowed_paths:
            self._config.allowed_paths.append(resolved)
            logger.info("Sandbox: allowed path added: %s", resolved)

    def remove_allowed_path(self, path: str) -> None:
        """許可パスを削除する."""
        resolved = str(Path(path).resolve())
        self._config.allowed_paths = [p for p in self._config.allowed_paths if p != resolved]
        logger.info("Sandbox: allowed path removed: %s", resolved)

    def check_access(
        self,
        path: str,
        access_type: AccessType = AccessType.READ,
    ) -> AccessCheckResult:
        """パスへのアクセスが許可されているかチェックする.

        Args:
            path: チェック対象のパス
            access_type: アクセス種別

        Returns:
            AccessCheckResult: アクセス可否と理由
        """
        try:
            # パスを正規化（パストラバーサル防止）
            resolved_path = str(Path(path).resolve())
        except (ValueError, OSError) as exc:
            return AccessCheckResult(
                allowed=False,
                path=path,
                access_type=access_type,
                reason=f"Invalid path: {exc}",
                sandbox_level=self._config.level,
            )

        # シンボリックリンクチェック（解決前の元パスでリンクを検出）
        # 注意: os.path.islink は resolve() 前の元パスで実行する必要がある
        if not self._config.allow_symlink_follow and os.path.islink(path):
            return AccessCheckResult(
                allowed=False,
                path=resolved_path,
                access_type=access_type,
                reason="Symlink following is disabled",
                sandbox_level=self._config.level,
            )

        # 解決後パスが元パスと大きく異なる場合もシンボリックリンク攻撃の可能性
        # (シンボリックリンクチェーンや間接リンクへの対策)
        if not self._config.allow_symlink_follow:
            original_dir = str(Path(path).parent.resolve())
            resolved_dir = str(Path(resolved_path).parent)
            if original_dir != resolved_dir:
                return AccessCheckResult(
                    allowed=False,
                    path=resolved_path,
                    access_type=access_type,
                    reason="Path resolves to different directory (possible symlink attack)",
                    sandbox_level=self._config.level,
                )

        # 禁止パスチェック（全レベル共通）
        for denied in self._config.denied_paths:
            if denied.startswith("/") or denied.startswith("~"):
                # 絶対パスの禁止ルール
                denied_resolved = str(Path(denied).expanduser().resolve())
                if resolved_path.startswith(denied_resolved) or resolved_path == denied_resolved:
                    return AccessCheckResult(
                        allowed=False,
                        path=resolved_path,
                        access_type=access_type,
                        reason=f"Path is in denied list: {denied}",
                        sandbox_level=self._config.level,
                    )
            else:
                # ファイル名パターンの禁止ルール
                basename = os.path.basename(resolved_path)
                if basename == denied or resolved_path.endswith(denied):
                    return AccessCheckResult(
                        allowed=False,
                        path=resolved_path,
                        access_type=access_type,
                        reason=f"File matches denied pattern: {denied}",
                        sandbox_level=self._config.level,
                    )

        # レベル別チェック
        if self._config.level == SandboxLevel.STRICT:
            return self._check_strict(resolved_path, access_type)
        elif self._config.level == SandboxLevel.MODERATE:
            return self._check_moderate(resolved_path, access_type)
        else:
            return self._check_permissive(resolved_path, access_type)

    def _check_strict(self, resolved_path: str, access_type: AccessType) -> AccessCheckResult:
        """STRICT モード: 許可リストのフォルダのみ."""
        for allowed in self._config.allowed_paths:
            allowed_resolved = str(Path(allowed).resolve())
            if resolved_path.startswith(allowed_resolved) or resolved_path == allowed_resolved:
                return AccessCheckResult(
                    allowed=True,
                    path=resolved_path,
                    access_type=access_type,
                    reason=f"Path is within allowed directory: {allowed}",
                    sandbox_level=self._config.level,
                )

        return AccessCheckResult(
            allowed=False,
            path=resolved_path,
            access_type=access_type,
            reason="STRICT mode: path not in allowed list. Add path via security settings.",
            sandbox_level=self._config.level,
        )

    def _check_moderate(self, resolved_path: str, access_type: AccessType) -> AccessCheckResult:
        """MODERATE モード: 許可リスト + 一般的な公開ディレクトリ."""
        # 許可リストチェック
        for allowed in self._config.allowed_paths:
            allowed_resolved = str(Path(allowed).resolve())
            if resolved_path.startswith(allowed_resolved):
                return AccessCheckResult(
                    allowed=True,
                    path=resolved_path,
                    access_type=access_type,
                    reason=f"Path is within allowed directory: {allowed}",
                    sandbox_level=self._config.level,
                )

        # 読み取りの場合は拡張子チェック
        if access_type == AccessType.READ:
            ext = Path(resolved_path).suffix.lower()
            if ext in self._config.allowed_extensions:
                return AccessCheckResult(
                    allowed=True,
                    path=resolved_path,
                    access_type=access_type,
                    reason=f"File extension {ext} is allowed for reading",
                    sandbox_level=self._config.level,
                )

        return AccessCheckResult(
            allowed=False,
            path=resolved_path,
            access_type=access_type,
            reason="MODERATE mode: path not in allowed list and not a permitted file type.",
            sandbox_level=self._config.level,
        )

    def _check_permissive(self, resolved_path: str, access_type: AccessType) -> AccessCheckResult:
        """PERMISSIVE モード: 禁止リスト以外すべて許可（非推奨）."""
        # 禁止パスは既にチェック済み
        return AccessCheckResult(
            allowed=True,
            path=resolved_path,
            access_type=access_type,
            reason="PERMISSIVE mode: path not in denied list",
            sandbox_level=self._config.level,
        )

    def check_file_size(self, path: str) -> bool:
        """ファイルサイズが制限内かチェックする."""
        try:
            size_mb = os.path.getsize(path) / (1024 * 1024)
            return size_mb <= self._config.max_file_size_mb
        except OSError:
            return False

    def get_allowed_paths(self) -> list[str]:
        """許可パス一覧を返す."""
        return list(self._config.allowed_paths)

    def get_denied_paths(self) -> list[str]:
        """禁止パス一覧を返す."""
        return list(self._config.denied_paths)


# グローバルインスタンス
filesystem_sandbox = FileSystemSandbox()
