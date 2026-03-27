"""Token / auth utilities with secure password hashing."""

import hashlib
import logging
import secrets
import uuid

import bcrypt

logger = logging.getLogger(__name__)


def generate_uuid() -> uuid.UUID:
    """Return a new UUID4."""
    return uuid.uuid4()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash.

    Supports bcrypt (current) and legacy salted SHA-256 for backward
    compatibility with data created before bcrypt was required.

    Plain (unsalted) SHA-256 hashes are **rejected** because they are
    cryptographically unsafe.  Users with such hashes must reset their
    password.
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
    # Legacy unsalted SHA-256 hashes are no longer accepted.
    # Log the attempt so administrators can identify accounts that need
    # password resets.
    logger.warning(
        "Rejected login attempt using unsalted SHA-256 hash. "
        "The account must reset its password to use bcrypt."
    )
    return False


# Backward compatibility aliases
def hash_sha256(value: str) -> str:
    """Deprecated: use hash_password() instead.

    Now delegates to bcrypt so that all new hashes are secure.
    """
    return hash_password(value)


def verify_hash(plain: str, hashed: str) -> bool:
    """Deprecated: use verify_password() instead."""
    return verify_password(plain, hashed)


def generate_token(nbytes: int = 32) -> str:
    """Generate a URL-safe random token."""
    return secrets.token_urlsafe(nbytes)
