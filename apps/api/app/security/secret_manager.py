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

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 環境変数名: 永続化された Fernet キー (Base64 URL-safe, 32 bytes)
# 本番環境では必ずこの変数を設定する。未設定の場合はプロセスごとの一時キーを生成する。
# 生成コマンド: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# ---------------------------------------------------------------------------
_FERNET_KEY_ENV = "FERNET_SECRET_KEY"


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


def _load_or_generate_fernet_key() -> bytes:
    """環境変数から Fernet キーを読み込む。未設定の場合は一時キーを生成する.

    本番環境では ``FERNET_SECRET_KEY`` 環境変数に有効な Fernet キーを設定すること。
    未設定時はプロセスごとに新しいキーが生成され、再起動でシークレットが失われる。
    """
    raw = os.environ.get(_FERNET_KEY_ENV, "")
    if raw:
        try:
            # Fernet キーの形式検証: URL-safe Base64, 32 bytes に解码できること
            decoded = base64.urlsafe_b64decode(raw + "==")
            if len(decoded) != 32:
                raise ValueError(f"Fernet key must be 32 bytes, got {len(decoded)}")
            logger.info(
                "Fernet key loaded from environment variable %s", _FERNET_KEY_ENV
            )
            return raw.encode()
        except Exception as exc:
            logger.error(
                "Invalid %s value (%s); falling back to ephemeral key. "
                "Secrets will be lost on restart.",
                _FERNET_KEY_ENV,
                exc,
            )

    key = Fernet.generate_key()
    logger.warning(
        "%s is not set. Using an ephemeral per-process Fernet key. "
        "All stored secrets will be lost on application restart. "
        "Set %s in your environment for persistence.",
        _FERNET_KEY_ENV,
        _FERNET_KEY_ENV,
    )
    return key


class SecretStore:
    """ローカル暗号化ストアの抽象.

    Fernet 対称暗号化（AES-128-CBC + HMAC-SHA256）でシークレットを保護する。

    **キーの永続化**:
    ``FERNET_SECRET_KEY`` 環境変数に Fernet キーを設定することで、
    アプリケーション再起動後もシークレットを復元できる（DB 永続化と組み合わせる場合）。
    未設定の場合はプロセスごとの一時キーを使用する。

    **本番環境の推奨**:
    本番環境では AWS Secrets Manager / HashiCorp Vault 等の外部 Secret Manager
    への差し替えを推奨。このクラスはその抽象層として機能する。

    **キー生成コマンド**::

        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """

    def __init__(self) -> None:
        self._key = _load_or_generate_fernet_key()
        self._fernet = Fernet(self._key)
        self._store: dict[str, bytes] = {}

    def store(
        self,
        name: str,
        value: str,
        secret_type: SecretType = SecretType.API_KEY,
    ) -> SecretMetadata:
        """シークレットを Fernet 暗号化して保存する.

        Args:
            name: シークレットの識別名
            value: 保存するシークレット値（平文）
            secret_type: シークレットの種別（デフォルト: API_KEY）
        """
        encrypted = self._fernet.encrypt(value.encode())
        self._store[name] = encrypted
        return SecretMetadata(
            name=name,
            secret_type=secret_type,
            provider="local",
            masked_value=mask_secret(value),
            created_at=datetime.now(timezone.utc),
        )

    def retrieve(self, name: str) -> str | None:
        """シークレットを復号して取得する."""
        encrypted = self._store.get(name)
        if encrypted is None:
            return None
        try:
            return self._fernet.decrypt(encrypted).decode()
        except InvalidToken:
            logger.error(
                "Failed to decrypt secret '%s': token is invalid or tampered", name
            )
            return None

    def delete(self, name: str) -> bool:
        """シークレットを削除する."""
        if name in self._store:
            del self._store[name]
            return True
        return False

    def list_secrets(self) -> list[str]:
        """保存済みシークレット名の一覧を返す."""
        return list(self._store.keys())

    def clear(self) -> None:
        """全シークレットを削除する（プロセス終了時やセッション破棄時に呼び出す）."""
        self._store.clear()
        logger.info("SecretStore cleared")


# グローバルインスタンス
secret_store = SecretStore()
