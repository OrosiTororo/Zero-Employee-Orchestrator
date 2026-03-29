"""Tests for SecretManager -- Encrypted secret storage and retrieval."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.security.secret_manager import (
    SecretStatus,
    SecretStore,
    SecretType,
    check_expiration,
    get_env_secret,
    mask_secret,
)

# ---------------------------------------------------------------------------
# mask_secret
# ---------------------------------------------------------------------------


class TestMaskSecret:
    def test_normal_secret(self):
        assert mask_secret("sk-1234567890abcdef") == "sk-...cdef"

    def test_short_secret(self):
        assert mask_secret("abc") == "****"

    def test_exact_boundary(self):
        assert mask_secret("abcd") == "****"

    def test_custom_visible_chars(self):
        result = mask_secret("sk-abcdefghij", visible_chars=2)
        assert result == "sk-...ij"


# ---------------------------------------------------------------------------
# check_expiration
# ---------------------------------------------------------------------------


class TestCheckExpiration:
    def test_no_expiry(self):
        assert check_expiration(None) == SecretStatus.ACTIVE

    def test_active_far_future(self):
        future = datetime.now(UTC) + timedelta(days=365)
        assert check_expiration(future) == SecretStatus.ACTIVE

    def test_expiring_soon(self):
        soon = datetime.now(UTC) + timedelta(days=10)
        assert check_expiration(soon, warn_days=30) == SecretStatus.EXPIRING_SOON

    def test_expired(self):
        past = datetime.now(UTC) - timedelta(days=1)
        assert check_expiration(past) == SecretStatus.EXPIRED

    def test_expired_exact_boundary(self):
        # Exactly at expiration time
        now = datetime.now(UTC)
        assert check_expiration(now) == SecretStatus.EXPIRED


# ---------------------------------------------------------------------------
# get_env_secret
# ---------------------------------------------------------------------------


class TestGetEnvSecret:
    def test_existing_env_var(self, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "sk-test-12345678")
        result = get_env_secret("TEST_API_KEY")
        assert result == "sk-test-12345678"

    def test_missing_env_var(self):
        result = get_env_secret("NONEXISTENT_SECRET_KEY_ZEO_TEST")
        assert result is None


# ---------------------------------------------------------------------------
# SecretStore -- Ephemeral mode
# ---------------------------------------------------------------------------


class TestSecretStoreEphemeral:
    @pytest.fixture
    def store(self) -> SecretStore:
        return SecretStore(persist_path=None)

    def test_is_not_persistent(self, store: SecretStore):
        assert store.is_persistent is False

    def test_store_and_retrieve(self, store: SecretStore):
        meta = store.store("my-api-key", "sk-abcdefghijklmnop")
        assert meta.name == "my-api-key"
        assert meta.secret_type == SecretType.API_KEY
        assert meta.masked_value == "sk-...mnop"
        assert meta.created_at is not None

        retrieved = store.retrieve("my-api-key")
        assert retrieved == "sk-abcdefghijklmnop"

    def test_retrieve_nonexistent(self, store: SecretStore):
        assert store.retrieve("nonexistent") is None

    def test_delete_existing(self, store: SecretStore):
        store.store("to-delete", "value123")
        assert store.delete("to-delete") is True
        assert store.retrieve("to-delete") is None

    def test_delete_nonexistent(self, store: SecretStore):
        assert store.delete("nonexistent") is False

    def test_list_secrets(self, store: SecretStore):
        store.store("key-a", "val-a")
        store.store("key-b", "val-b")
        names = store.list_secrets()
        assert "key-a" in names
        assert "key-b" in names

    def test_overwrite_existing_secret(self, store: SecretStore):
        store.store("overwrite-key", "original")
        store.store("overwrite-key", "updated")
        assert store.retrieve("overwrite-key") == "updated"

    def test_multiple_stores_have_independent_keys(self):
        s1 = SecretStore(persist_path=None)
        s2 = SecretStore(persist_path=None)
        s1.store("shared-name", "value1")
        # s2 should not be able to retrieve s1's secret
        assert s2.retrieve("shared-name") is None


# ---------------------------------------------------------------------------
# SecretStore -- Persistent mode
# ---------------------------------------------------------------------------


class TestSecretStorePersistent:
    def test_is_persistent(self, tmp_path: Path):
        store = SecretStore(persist_path=tmp_path / "secrets")
        assert store.is_persistent is True

    def test_store_and_retrieve_persistent(self, tmp_path: Path):
        path = tmp_path / "secrets"
        store = SecretStore(persist_path=path)
        store.store("persistent-key", "persistent-value")

        retrieved = store.retrieve("persistent-key")
        assert retrieved == "persistent-value"

    def test_persist_survives_reload(self, tmp_path: Path):
        path = tmp_path / "secrets"

        # Store in first instance
        store1 = SecretStore(persist_path=path)
        store1.store("survive-key", "survive-value")

        # Reload in second instance
        store2 = SecretStore(persist_path=path)
        retrieved = store2.retrieve("survive-key")
        assert retrieved == "survive-value"

    def test_delete_persists(self, tmp_path: Path):
        path = tmp_path / "secrets"
        store1 = SecretStore(persist_path=path)
        store1.store("del-key", "del-value")
        store1.delete("del-key")

        store2 = SecretStore(persist_path=path)
        assert store2.retrieve("del-key") is None

    def test_secrets_file_permissions(self, tmp_path: Path):
        import os
        import stat

        path = tmp_path / "secrets"
        store = SecretStore(persist_path=path)
        store.store("perm-test", "value")

        secrets_file = path / "secrets.enc"
        assert secrets_file.exists()
        mode = os.stat(str(secrets_file)).st_mode
        # Should be 0o600 (owner read/write only)
        assert mode & stat.S_IRUSR
        assert mode & stat.S_IWUSR
        assert not (mode & stat.S_IRGRP)
        assert not (mode & stat.S_IROTH)

    def test_salt_file_created(self, tmp_path: Path):
        path = tmp_path / "secrets"
        SecretStore(persist_path=path)
        salt_file = path / "secrets.salt"
        assert salt_file.exists()
        assert len(salt_file.read_bytes()) == 16
