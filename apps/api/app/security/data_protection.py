"""Data protection and transfer security settings.

Security settings module that controls downloads, uploads, and external
communications by AI.

Security policies:
- LOCKDOWN: All external transfers are prohibited (default)
- RESTRICTED: Only user-approved destinations
- PERMISSIVE: Everything allowed except blocklist (not recommended)

Configuration methods:
- GUI: Settings > Security > Data Protection
- CLI: zero-employee config set SECURITY_TRANSFER_POLICY lockdown
- TUI: Security Menu > Data Transfer Policy
- API: PUT /api/v1/security/data-protection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TransferPolicy(str, Enum):
    """Data transfer policy."""

    LOCKDOWN = "lockdown"  # All external transfers prohibited (default)
    RESTRICTED = "restricted"  # Approved destinations only
    PERMISSIVE = "permissive"  # Everything allowed except blocklist (not recommended)


class TransferDirection(str, Enum):
    """Transfer direction."""

    UPLOAD = "upload"
    DOWNLOAD = "download"


class TransferType(str, Enum):
    """Transfer type."""

    FILE = "file"
    API_REQUEST = "api_request"
    WEBHOOK = "webhook"
    EMAIL = "email"
    CHAT_MESSAGE = "chat_message"


@dataclass
class TransferCheckResult:
    """Transfer permission check result."""

    allowed: bool
    direction: TransferDirection
    transfer_type: TransferType
    destination: str
    reason: str
    requires_approval: bool = False


@dataclass
class DataProtectionConfig:
    """Data protection configuration.

    Default setting is the most secure LOCKDOWN mode.
    """

    transfer_policy: TransferPolicy = TransferPolicy.LOCKDOWN

    # Upload settings
    upload_enabled: bool = False  # Whether to allow uploads by AI
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
    upload_require_approval: bool = True  # Require approval before upload

    # Download settings
    download_enabled: bool = False  # Whether to allow downloads by AI
    download_allowed_sources: list[str] = field(default_factory=list)
    download_max_size_mb: int = 100
    download_require_approval: bool = True

    # Blocked patterns (content that must not be included in uploads)
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

    # External API communication settings
    external_api_enabled: bool = False
    external_api_allowed_hosts: list[str] = field(default_factory=list)
    external_api_require_approval: bool = True

    # PII protection
    pii_auto_detect: bool = True  # Enable automatic PII detection
    pii_block_upload: bool = True  # Block uploads containing PII
    pii_mask_in_logs: bool = True  # Mask PII in logs

    # Special protection for passwords and credentials
    password_upload_blocked: bool = True  # Always block uploads of passwords and credentials


class DataProtectionGuard:
    """Data protection guard.

    Controls data transfers (uploads/downloads) by AI.
    """

    def __init__(self, config: DataProtectionConfig | None = None) -> None:
        self._config = config or DataProtectionConfig()

    @property
    def config(self) -> DataProtectionConfig:
        return self._config

    def update_config(self, config: DataProtectionConfig) -> None:
        """Update configuration."""
        self._config = config
        logger.info("Data protection config updated: policy=%s", config.transfer_policy.value)

    def check_upload(
        self,
        destination: str,
        file_name: str = "",
        file_size_mb: float = 0,
        content_preview: str = "",
    ) -> TransferCheckResult:
        """Check whether an upload is permitted."""
        # LOCKDOWN mode: reject all
        if self._config.transfer_policy == TransferPolicy.LOCKDOWN:
            return TransferCheckResult(
                allowed=False,
                direction=TransferDirection.UPLOAD,
                transfer_type=TransferType.FILE,
                destination=destination,
                reason="LOCKDOWN mode: all uploads are disabled. "
                "Change policy via settings to enable.",
            )

        # Uploads disabled
        if not self._config.upload_enabled:
            return TransferCheckResult(
                allowed=False,
                direction=TransferDirection.UPLOAD,
                transfer_type=TransferType.FILE,
                destination=destination,
                reason="Uploads are disabled in current configuration.",
            )

        # Password/credential check
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

        # File size check
        if file_size_mb > self._config.upload_max_size_mb:
            return TransferCheckResult(
                allowed=False,
                direction=TransferDirection.UPLOAD,
                transfer_type=TransferType.FILE,
                destination=destination,
                reason=f"File size {file_size_mb:.1f}MB exceeds limit "
                f"{self._config.upload_max_size_mb}MB",
            )

        # File extension check
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

        # RESTRICTED mode: allowlist check
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
        """Check whether a download is permitted."""
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
        """Check whether an external API call is permitted."""
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


# Global instance (default is LOCKDOWN)
data_protection_guard = DataProtectionGuard()
