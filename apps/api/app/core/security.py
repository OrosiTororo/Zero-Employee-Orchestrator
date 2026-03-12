"""Token / auth utilities with secure password hashing."""

import hashlib
import secrets
import uuid

import bcrypt


def generate_uuid() -> uuid.UUID:
    """Return a new UUID4."""
    return uuid.uuid4()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash.

    Supports bcrypt (current) and legacy salted/plain SHA-256 for
    backward compatibility with data created before bcrypt was required.
    """
    if hashed.startswith("$2"):
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    if hashed.startswith("sha256$"):
        parts = hashed.split("$")
        if len(parts) == 3:
            salt = parts[1]
            expected = parts[2]
            actual = hashlib.sha256((salt + plain).encode()).hexdigest()
            return secrets.compare_digest(actual, expected)
    # Legacy: plain SHA-256 (for backward compatibility with existing data)
    legacy_hash = hashlib.sha256(plain.encode()).hexdigest()
    return secrets.compare_digest(legacy_hash, hashed)


# Backward compatibility aliases
def hash_sha256(value: str) -> str:
    """Deprecated: use hash_password() instead."""
    return hash_password(value)


def verify_hash(plain: str, hashed: str) -> bool:
    """Deprecated: use verify_password() instead."""
    return verify_password(plain, hashed)


def generate_token(nbytes: int = 32) -> str:
    """Generate a URL-safe random token."""
    return secrets.token_urlsafe(nbytes)
