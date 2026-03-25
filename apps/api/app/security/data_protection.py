"""データ保護・転送セキュリティ設定.

AI によるダウンロード・アップロード・外部通信を制御する
セキュリティ設定モジュール。

セキュリティポリシー:
- LOCKDOWN: 外部転送を全面禁止（初期設定）
- RESTRICTED: ユーザーが許可した宛先のみ
- PERMISSIVE: 禁止リスト以外すべて許可（非推奨）

設定方法:
- GUI: 設定画面 > セキュリティ > データ保護
- CLI: zero-employee config set SECURITY_TRANSFER_POLICY lockdown
- TUI: セキュリティメニュー > データ転送ポリシー
- API: PUT /api/v1/security/data-protection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TransferPolicy(str, Enum):
    """データ転送ポリシー."""

    LOCKDOWN = "lockdown"  # 外部転送全面禁止（初期設定）
    RESTRICTED = "restricted"  # 許可された宛先のみ
    PERMISSIVE = "permissive"  # 禁止リスト以外許可（非推奨）


class TransferDirection(str, Enum):
    """転送方向."""

    UPLOAD = "upload"
    DOWNLOAD = "download"


class TransferType(str, Enum):
    """転送タイプ."""

    FILE = "file"
    API_REQUEST = "api_request"
    WEBHOOK = "webhook"
    EMAIL = "email"
    CHAT_MESSAGE = "chat_message"


@dataclass
class TransferCheckResult:
    """転送可否チェック結果."""

    allowed: bool
    direction: TransferDirection
    transfer_type: TransferType
    destination: str
    reason: str
    requires_approval: bool = False


@dataclass
class DataProtectionConfig:
    """データ保護設定.

    初期設定は最もセキュアな LOCKDOWN モード。
    """

    transfer_policy: TransferPolicy = TransferPolicy.LOCKDOWN

    # アップロード設定
    upload_enabled: bool = False  # AI によるアップロードを許可するか
    upload_allowed_destinations: list[str] = field(default_factory=list)
    upload_max_size_mb: int = 10
    upload_allowed_types: set[str] = field(
        default_factory=lambda: {
            ".txt",
            ".md",
            ".csv",
            ".json",
            ".xml",
            ".png",
            ".jpg",
            ".jpeg",
            ".pdf",
        }
    )
    upload_require_approval: bool = True  # アップロード前に承認を要求

    # ダウンロード設定
    download_enabled: bool = False  # AI によるダウンロードを許可するか
    download_allowed_sources: list[str] = field(default_factory=list)
    download_max_size_mb: int = 100
    download_require_approval: bool = True

    # 禁止パターン（アップロードに含めてはいけない内容）
    upload_blocked_patterns: list[str] = field(
        default_factory=lambda: [
            "password",
            "secret",
            "token",
            "api_key",
            "apikey",
            "credential",
            "private_key",
            "credit_card",
            "ssn",
            "social_security",
        ]
    )

    # 外部 API 通信設定
    external_api_enabled: bool = False
    external_api_allowed_hosts: list[str] = field(default_factory=list)
    external_api_require_approval: bool = True

    # PII 保護
    pii_auto_detect: bool = True  # PII 自動検出を有効にする
    pii_block_upload: bool = True  # PII を含むアップロードをブロック
    pii_mask_in_logs: bool = True  # ログ中の PII をマスク

    # パスワード類の特別保護
    password_upload_blocked: bool = True  # パスワード類のアップロードは常にブロック


class DataProtectionGuard:
    """データ保護ガード.

    AI によるデータ転送（アップロード・ダウンロード）を制御する。
    """

    def __init__(self, config: DataProtectionConfig | None = None) -> None:
        self._config = config or DataProtectionConfig()

    @property
    def config(self) -> DataProtectionConfig:
        return self._config

    def update_config(self, config: DataProtectionConfig) -> None:
        """設定を更新する."""
        self._config = config
        logger.info("Data protection config updated: policy=%s", config.transfer_policy.value)

    def check_upload(
        self,
        destination: str,
        file_name: str = "",
        file_size_mb: float = 0,
        content_preview: str = "",
    ) -> TransferCheckResult:
        """アップロードの可否をチェックする."""
        # LOCKDOWN モード: すべて拒否
        if self._config.transfer_policy == TransferPolicy.LOCKDOWN:
            return TransferCheckResult(
                allowed=False,
                direction=TransferDirection.UPLOAD,
                transfer_type=TransferType.FILE,
                destination=destination,
                reason="LOCKDOWN mode: all uploads are disabled. "
                "Change policy via settings to enable.",
            )

        # アップロード無効
        if not self._config.upload_enabled:
            return TransferCheckResult(
                allowed=False,
                direction=TransferDirection.UPLOAD,
                transfer_type=TransferType.FILE,
                destination=destination,
                reason="Uploads are disabled in current configuration.",
            )

        # パスワード類チェック
        if self._config.password_upload_blocked and content_preview:
            lower = content_preview.lower()
            for pattern in self._config.upload_blocked_patterns:
                if pattern.lower() in lower:
                    return TransferCheckResult(
                        allowed=False,
                        direction=TransferDirection.UPLOAD,
                        transfer_type=TransferType.FILE,
                        destination=destination,
                        reason=f"Upload blocked: content contains sensitive pattern '{pattern}'",
                    )

        # ファイルサイズチェック
        if file_size_mb > self._config.upload_max_size_mb:
            return TransferCheckResult(
                allowed=False,
                direction=TransferDirection.UPLOAD,
                transfer_type=TransferType.FILE,
                destination=destination,
                reason=f"File size {file_size_mb:.1f}MB exceeds limit "
                f"{self._config.upload_max_size_mb}MB",
            )

        # 拡張子チェック
        if file_name:
            ext = "." + file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
            if ext and ext not in self._config.upload_allowed_types:
                return TransferCheckResult(
                    allowed=False,
                    direction=TransferDirection.UPLOAD,
                    transfer_type=TransferType.FILE,
                    destination=destination,
                    reason=f"File type '{ext}' is not allowed for upload",
                )

        # RESTRICTED モード: 許可リストチェック
        if self._config.transfer_policy == TransferPolicy.RESTRICTED:
            if destination not in self._config.upload_allowed_destinations:
                allowed_any = any(
                    destination.startswith(d) for d in self._config.upload_allowed_destinations
                )
                if not allowed_any:
                    return TransferCheckResult(
                        allowed=False,
                        direction=TransferDirection.UPLOAD,
                        transfer_type=TransferType.FILE,
                        destination=destination,
                        reason="Destination not in allowed list",
                    )

        return TransferCheckResult(
            allowed=True,
            direction=TransferDirection.UPLOAD,
            transfer_type=TransferType.FILE,
            destination=destination,
            reason="Upload allowed",
            requires_approval=self._config.upload_require_approval,
        )

    def check_download(
        self,
        source: str,
        file_size_mb: float = 0,
    ) -> TransferCheckResult:
        """ダウンロードの可否をチェックする."""
        if self._config.transfer_policy == TransferPolicy.LOCKDOWN:
            return TransferCheckResult(
                allowed=False,
                direction=TransferDirection.DOWNLOAD,
                transfer_type=TransferType.FILE,
                destination=source,
                reason="LOCKDOWN mode: all downloads are disabled.",
            )

        if not self._config.download_enabled:
            return TransferCheckResult(
                allowed=False,
                direction=TransferDirection.DOWNLOAD,
                transfer_type=TransferType.FILE,
                destination=source,
                reason="Downloads are disabled in current configuration.",
            )

        if file_size_mb > self._config.download_max_size_mb:
            return TransferCheckResult(
                allowed=False,
                direction=TransferDirection.DOWNLOAD,
                transfer_type=TransferType.FILE,
                destination=source,
                reason=f"File size exceeds limit {self._config.download_max_size_mb}MB",
            )

        if self._config.transfer_policy == TransferPolicy.RESTRICTED:
            if source not in self._config.download_allowed_sources:
                allowed_any = any(
                    source.startswith(s) for s in self._config.download_allowed_sources
                )
                if not allowed_any:
                    return TransferCheckResult(
                        allowed=False,
                        direction=TransferDirection.DOWNLOAD,
                        transfer_type=TransferType.FILE,
                        destination=source,
                        reason="Source not in allowed list",
                    )

        return TransferCheckResult(
            allowed=True,
            direction=TransferDirection.DOWNLOAD,
            transfer_type=TransferType.FILE,
            destination=source,
            reason="Download allowed",
            requires_approval=self._config.download_require_approval,
        )

    def check_external_api(self, host: str) -> TransferCheckResult:
        """外部 API 通信の可否をチェックする."""
        if self._config.transfer_policy == TransferPolicy.LOCKDOWN:
            return TransferCheckResult(
                allowed=False,
                direction=TransferDirection.UPLOAD,
                transfer_type=TransferType.API_REQUEST,
                destination=host,
                reason="LOCKDOWN mode: external API calls are disabled.",
            )

        if not self._config.external_api_enabled:
            return TransferCheckResult(
                allowed=False,
                direction=TransferDirection.UPLOAD,
                transfer_type=TransferType.API_REQUEST,
                destination=host,
                reason="External API calls are disabled.",
            )

        if self._config.transfer_policy == TransferPolicy.RESTRICTED:
            if host not in self._config.external_api_allowed_hosts:
                return TransferCheckResult(
                    allowed=False,
                    direction=TransferDirection.UPLOAD,
                    transfer_type=TransferType.API_REQUEST,
                    destination=host,
                    reason=f"Host '{host}' is not in allowed API hosts list",
                )

        return TransferCheckResult(
            allowed=True,
            direction=TransferDirection.UPLOAD,
            transfer_type=TransferType.API_REQUEST,
            destination=host,
            reason="External API call allowed",
            requires_approval=self._config.external_api_require_approval,
        )


# グローバルインスタンス（初期設定は LOCKDOWN）
data_protection_guard = DataProtectionGuard()
