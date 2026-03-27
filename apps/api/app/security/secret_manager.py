"""Secret management -- Secure storage and retrieval of credentials.

Based on Zero-Employee Orchestrator.md sections 13.3 and 14:
- API keys and credentials are managed with encryption
- Sensitive information is never output in plaintext to logs
- Credential rotation support is provided
- An abstraction layer enables delegation to Secret Managers or OS-native secure storage
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from cryptography.fernet import Fernet, InvalidToken

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
    """Secret metadata (does not contain the actual value)."""

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
    """Mask a secret value."""
    if len(value) <= visible_chars:
        return "****"
    prefix = value[:3]
    suffix = value[-visible_chars:]
    return f"{prefix}...{suffix}"


def check_expiration(
    expires_at: datetime | None,
    warn_days: int = 30,
) -> SecretStatus:
    """Check the expiration of a secret."""
    if expires_at is None:
        return SecretStatus.ACTIVE

    now = datetime.now(UTC)
    if now >= expires_at:
        return SecretStatus.EXPIRED

    days_until_expiry = (expires_at - now).days
    if days_until_expiry <= warn_days:
        return SecretStatus.EXPIRING_SOON

    return SecretStatus.ACTIVE


def get_env_secret(key: str) -> str | None:
    """Get a secret from environment variables (without logging the value)."""
    value = os.environ.get(key)
    if value:
        logger.debug("Secret '%s' loaded (masked: %s)", key, mask_secret(value))
    else:
        logger.debug("Secret '%s' not found in environment", key)
    return value


class SecretStore:
    """Abstraction of a local encrypted store.

    Protects secrets using Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256).
    This is an in-memory store that generates a random key per process,
    so encryption keys and secrets are all lost on application restart.
    Secrets must be re-registered after restart.
    For production environments, replacing with an external Secret Manager such as
    AWS Secrets Manager or HashiCorp Vault is recommended.
    """

    def __init__(self) -> None:
        self._key = Fernet.generate_key()
        self._fernet = Fernet(self._key)
        self._store: dict[str, bytes] = {}
        logger.warning(
            "SecretStore initialized with ephemeral encryption key. "
            "All secrets will be lost on process restart. "
            "For production, use an external secret manager (AWS Secrets Manager, "
            "HashiCorp Vault, etc.)."
        )

    def store(self, name: str, value: str) -> SecretMetadata:
        """Encrypt and store a secret using Fernet."""
        encrypted = self._fernet.encrypt(value.encode())
        self._store[name] = encrypted
        return SecretMetadata(
            name=name,
            secret_type=SecretType.API_KEY,
            provider="local",
            masked_value=mask_secret(value),
            created_at=datetime.now(UTC),
        )

    def retrieve(self, name: str) -> str | None:
        """Decrypt and retrieve a secret."""
        encrypted = self._store.get(name)
        if encrypted is None:
            return None
        try:
            return self._fernet.decrypt(encrypted).decode()
        except InvalidToken:
            logger.error(
                "Failed to decrypt secret '%s': token is invalid or tampered",
                name,
            )
            return None

    def delete(self, name: str) -> bool:
        """Delete a secret."""
        if name in self._store:
            del self._store[name]
            return True
        return False

    def list_secrets(self) -> list[str]:
        """Return a list of stored secret names."""
        return list(self._store.keys())


# Global instance
secret_store = SecretStore()
