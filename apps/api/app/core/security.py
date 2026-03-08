"""Simple token / auth utilities."""

import hashlib
import secrets
import uuid


def generate_uuid() -> uuid.UUID:
    """Return a new UUID4."""
    return uuid.uuid4()


def hash_sha256(value: str) -> str:
    """Return a hex-encoded SHA-256 hash of *value*."""
    return hashlib.sha256(value.encode()).hexdigest()


def generate_token(nbytes: int = 32) -> str:
    """Generate a URL-safe random token."""
    return secrets.token_urlsafe(nbytes)


def verify_hash(plain: str, hashed: str) -> bool:
    """Constant-time comparison of a plain value against its SHA-256 hash."""
    return secrets.compare_digest(hash_sha256(plain), hashed)
