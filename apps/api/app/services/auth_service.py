"""Authentication and registration service."""

import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import generate_uuid, hash_sha256, verify_hash
from app.models.user import CompanyMember, User
from app.models.company import Company

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    display_name: str,
) -> User:
    """Register a new user with email/password and create a default company."""
    user = User(
        id=generate_uuid(),
        email=email,
        display_name=display_name,
        role="owner",
        status="active",
        auth_provider="local",
        password_hash=hash_sha256(password),
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
        joined_at=datetime.now(timezone.utc),
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
    if not verify_hash(password, user.password_hash):
        return None
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    return user


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    return result.scalar_one_or_none()
