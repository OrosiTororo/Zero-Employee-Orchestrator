"""シークレット管理 — 認証情報の安全な保管と参照.

Zero-Employee Orchestrator.md §13.3, §14 に基づき:
- API キーや認証情報は暗号化して管理する
- 通常ログに平文の機密情報を出力しない
- 認証情報のローテーション支援を提供する
- Secret Manager や OS 標準の安全な保管先に委譲可能な抽象層を持つ
"""

from __future__ import annotations

import base64
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class SecretType(str, Enum):
    API_KEY = "api_key"
    OAUTH_TOKEN = "oauth_token"
    SERVICE_ACCOUNT = "service_account"
    PASSWORD = "password"
    CERTIFICATE = "certificate"


class SecretStatus(str, Enum):
    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ROTATION_PENDING = "rotation_pending"


@dataclass
class SecretMetadata:
    """シークレットのメタデータ（実値は含まない）."""

    name: str
    secret_type: SecretType
    provider: str
    masked_value: str  # e.g. "sk-...xxxx"
    status: SecretStatus = SecretStatus.ACTIVE
    created_at: datetime | None = None
    expires_at: datetime | None = None
    last_rotated_at: datetime | None = None
    last_verified_at: datetime | None = None


def mask_secret(value: str, visible_chars: int = 4) -> str:
    """シークレット値をマスキングする."""
    if len(value) <= visible_chars:
        return "****"
    prefix = value[:3]
    suffix = value[-visible_chars:]
    return f"{prefix}...{suffix}"


def check_expiration(
    expires_at: datetime | None,
    warn_days: int = 30,
) -> SecretStatus:
    """シークレットの有効期限を確認する."""
    if expires_at is None:
        return SecretStatus.ACTIVE

    now = datetime.now(timezone.utc)
    if now >= expires_at:
        return SecretStatus.EXPIRED

    days_until_expiry = (expires_at - now).days
    if days_until_expiry <= warn_days:
        return SecretStatus.EXPIRING_SOON

    return SecretStatus.ACTIVE


def get_env_secret(key: str) -> str | None:
    """環境変数からシークレットを取得する（ログに値を残さない）."""
    value = os.environ.get(key)
    if value:
        logger.debug("Secret '%s' loaded (masked: %s)", key, mask_secret(value))
    else:
        logger.debug("Secret '%s' not found in environment", key)
    return value


class SecretStore:
    """ローカル暗号化ストアの抽象.

    将来的に OS キーチェーン連携、Vault 連携、
    Secret Manager 連携に差し替え可能。
    """

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def store(self, name: str, value: str) -> SecretMetadata:
        """シークレットを保存する.

        WARNING: 現在の実装は base64 エンコーディングのみで暗号化されていません。
        本番環境では cryptography.Fernet 等による暗号化、または
        AWS Secrets Manager / HashiCorp Vault 等の外部 Secret Manager を使用してください。
        """
        encoded = base64.b64encode(value.encode()).decode()
        self._store[name] = encoded
        return SecretMetadata(
            name=name,
            secret_type=SecretType.API_KEY,
            provider="local",
            masked_value=mask_secret(value),
            created_at=datetime.now(timezone.utc),
        )

    def retrieve(self, name: str) -> str | None:
        """シークレットを取得する."""
        encoded = self._store.get(name)
        if encoded is None:
            return None
        return base64.b64decode(encoded.encode()).decode()

    def delete(self, name: str) -> bool:
        """シークレットを削除する."""
        if name in self._store:
            del self._store[name]
            return True
        return False

    def list_secrets(self) -> list[str]:
        """保存済みシークレット名の一覧を返す."""
        return list(self._store.keys())


# グローバルインスタンス
secret_store = SecretStore()
