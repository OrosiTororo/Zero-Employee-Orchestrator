"""Authentication and registration service."""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import generate_uuid, hash_password, verify_password
from app.models.company import Company
from app.models.user import CompanyMember, User

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h
PASSWORD_RESET_EXPIRE_MINUTES = 60  # 1h


def create_access_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_password_reset_token(email: str) -> str:
    """Create a short-lived token for password reset."""
    expire = datetime.now(UTC) + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    payload = {"sub": email, "purpose": "password_reset", "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


def decode_password_reset_token(token: str) -> str | None:
    """Decode a password reset token and return the email, or None if invalid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "password_reset":
            return None
        return payload.get("sub")
    except Exception:
        return None


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    display_name: str,
) -> User:
    """Register a new user with email/password and create a default company.

    All three inserts (user, company, membership) are wrapped in an
    explicit transaction so that a failure in any step rolls back cleanly.
    """
    async with db.begin_nested():
        user = User(
            id=generate_uuid(),
            email=email,
            display_name=display_name,
            role="owner",
            status="active",
            auth_provider="local",
            password_hash=hash_password(password),
        )
        db.add(user)

        # Create default company for new user
        company = Company(
            id=generate_uuid(),
            slug=f"company-{str(user.id)[:8]}",
            name=f"{display_name}'s Organization",
            mission="",
            description="",
            status="active",
        )
        db.add(company)

        member = CompanyMember(
            id=generate_uuid(),
            company_id=company.id,
            user_id=user.id,
            company_role="owner",
            status="active",
            joined_at=datetime.now(UTC),
        )
        db.add(member)

    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """Verify email/password and return user or None."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    if not hasattr(user, "password_hash") or user.password_hash is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_at = datetime.now(UTC)
    await db.commit()
    return user


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def request_password_reset(db: AsyncSession, email: str) -> str | None:
    """Generate a password reset token if the email exists.

    Returns the reset token, or None if the email is not found.
    The caller should send this token via email in production.
    """
    user = await get_user_by_email(db, email)
    if user is None:
        return None
    token = create_password_reset_token(email)
    logger.info("Password reset token generated for %s", email)
    return token


async def confirm_password_reset(db: AsyncSession, token: str, new_password: str) -> bool:
    """Validate a reset token and update the user's password.

    Returns True on success, False if the token is invalid or the user is not found.
    """
    email = decode_password_reset_token(token)
    if email is None:
        return False
    user = await get_user_by_email(db, email)
    if user is None:
        return False
    user.password_hash = hash_password(new_password)
    await db.commit()
    logger.info("Password reset completed for %s", email)
    return True


async def change_password(
    db: AsyncSession, user: User, current_password: str, new_password: str
) -> bool:
    """Change password for authenticated user after verifying the current one."""
    if not user.password_hash:
        return False
    if not verify_password(current_password, user.password_hash):
        return False
    user.password_hash = hash_password(new_password)
    await db.commit()
    return True
