"""Secret management -- Secure storage and retrieval of credentials.

Based on Zero-Employee Orchestrator.md sections 13.3 and 14:
- API keys and credentials are managed with encryption
- Sensitive information is never output in plaintext to logs
- Credential rotation support is provided
- An abstraction layer enables delegation to Secret Managers or OS-native secure storage

Persistence modes:
- **Ephemeral** (default): In-memory only, secrets lost on restart.
- **File-backed**: Encrypted secrets persisted to ``~/.zero-employee/secrets.enc``.
  The encryption key is derived from ``SECRET_KEY`` via PBKDF2.
- **External**: Delegate to AWS Secrets Manager, HashiCorp Vault, etc. (not yet implemented).
"""

from __future__ import annotations

import base64
import json
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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


def _derive_key_from_secret(secret_key: str, salt: bytes) -> bytes:
    """Derive a Fernet key from an application secret using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))


_DEFAULT_SECRETS_DIR = Path.home() / ".zero-employee"
_SECRETS_FILE = "secrets.enc"
_SALT_FILE = "secrets.salt"


class SecretStore:
    """Local encrypted secret store with optional file-backed persistence.

    Persistence modes:
    - ``persist_path=None`` (default): In-memory only — ephemeral.
    - ``persist_path=Path``: Encrypted secrets written to disk so they
      survive process restarts.  The encryption key is deterministically
      derived from ``SECRET_KEY`` via PBKDF2 so that the same key
      decrypts the file across restarts.

    For production, delegate to an external secret manager.
    """

    def __init__(self, persist_path: Path | None = None) -> None:
        self._persist_path = persist_path
        self._store: dict[str, bytes] = {}

        if persist_path is not None:
            self._fernet = self._init_persistent(persist_path)
            logger.info(
                "SecretStore initialized with file-backed persistence at %s",
                persist_path,
            )
        else:
            self._key = Fernet.generate_key()
            self._fernet = Fernet(self._key)
            logger.warning(
                "SecretStore initialized with ephemeral encryption key. "
                "All secrets will be lost on process restart. "
                "Set SECRETS_PERSIST=true or use an external secret manager "
                "(AWS Secrets Manager, HashiCorp Vault) for production."
            )

    # ------------------------------------------------------------------
    # Persistent key management
    # ------------------------------------------------------------------

    def _init_persistent(self, persist_path: Path) -> Fernet:
        """Derive a stable Fernet key and load any existing secrets."""
        from app.core.config import settings

        persist_path.mkdir(parents=True, exist_ok=True)
        os.chmod(str(persist_path), 0o700)

        salt_file = persist_path / _SALT_FILE
        if salt_file.exists():
            salt = salt_file.read_bytes()
        else:
            salt = os.urandom(16)
            salt_file.write_bytes(salt)
            os.chmod(str(salt_file), 0o600)

        key = _derive_key_from_secret(settings.SECRET_KEY, salt)
        fernet = Fernet(key)

        # Load existing secrets from disk
        secrets_file = persist_path / _SECRETS_FILE
        if secrets_file.exists():
            try:
                raw = fernet.decrypt(secrets_file.read_bytes())
                data = json.loads(raw.decode())
                self._store = {k: v.encode() for k, v in data.items()}
                logger.info("Loaded %d secrets from persistent store", len(self._store))
            except (InvalidToken, json.JSONDecodeError, UnicodeDecodeError) as exc:
                logger.error("Failed to load persistent secrets (key may have changed): %s", exc)
                self._store = {}

        return fernet

    def _save_to_disk(self) -> None:
        """Persist current store to disk (only if file-backed)."""
        if self._persist_path is None:
            return
        secrets_file = self._persist_path / _SECRETS_FILE
        data = {k: v.decode() if isinstance(v, bytes) else v for k, v in self._store.items()}
        encrypted = self._fernet.encrypt(json.dumps(data).encode())
        secrets_file.write_bytes(encrypted)
        os.chmod(str(secrets_file), 0o600)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(self, name: str, value: str) -> SecretMetadata:
        """Encrypt and store a secret using Fernet."""
        encrypted = self._fernet.encrypt(value.encode())
        self._store[name] = encrypted
        self._save_to_disk()
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
            self._save_to_disk()
            return True
        return False

    def list_secrets(self) -> list[str]:
        """Return a list of stored secret names."""
        return list(self._store.keys())

    @property
    def is_persistent(self) -> bool:
        """Whether this store persists secrets to disk."""
        return self._persist_path is not None


def _create_secret_store() -> SecretStore:
    """Factory that creates either an ephemeral or persistent SecretStore."""
    persist = os.environ.get("SECRETS_PERSIST", "").lower() in ("1", "true", "yes")
    if persist:
        path_str = os.environ.get("SECRETS_DIR", str(_DEFAULT_SECRETS_DIR))
        return SecretStore(persist_path=Path(path_str))
    return SecretStore()


# Global instance — ephemeral by default, persistent if SECRETS_PERSIST=true
secret_store = _create_secret_store()
