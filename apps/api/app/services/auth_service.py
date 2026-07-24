"""Authentication and registration service."""

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import generate_uuid, hash_password, verify_password
from app.models.company import Company
from app.models.user import CompanyMember, OAuthIdentity, User

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h
PASSWORD_RESET_EXPIRE_MINUTES = 60  # 1h
GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


class GoogleOAuthError(Exception):
    """Base class for sanitized Google OAuth failures."""


class GoogleOAuthConfigurationError(GoogleOAuthError):
    """Google sign-in is not configured."""


class GoogleOAuthExchangeError(GoogleOAuthError):
    """Google rejected or failed the authorization-code exchange."""


class GoogleOAuthIdentityError(GoogleOAuthError):
    """Google did not return a usable verified identity."""


class OAuthAccountLinkRequired(GoogleOAuthError):
    """An existing local account must explicitly link the OAuth identity."""


@dataclass(frozen=True)
class GoogleUserInfo:
    subject: str
    email: str
    display_name: str


@dataclass(frozen=True)
class OAuthUserResult:
    user: User
    company_id: uuid.UUID
    created: bool


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


def _add_user_with_default_company(
    db: AsyncSession,
    *,
    email: str,
    display_name: str,
    auth_provider: str,
    password_hash: str | None,
) -> tuple[User, Company]:
    """Add a user and their default organization to the current transaction."""
    user = User(
        id=generate_uuid(),
        email=email,
        display_name=display_name,
        role="owner",
        status="active",
        auth_provider=auth_provider,
        password_hash=password_hash,
    )
    company = Company(
        id=generate_uuid(),
        slug=f"company-{str(user.id)[:8]}",
        name=f"{display_name}'s Organization",
        mission="",
        description="",
        status="active",
    )
    member = CompanyMember(
        id=generate_uuid(),
        company_id=company.id,
        user_id=user.id,
        company_role="owner",
        status="active",
        joined_at=datetime.now(UTC),
    )
    db.add_all((user, company, member))
    return user, company


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    display_name: str,
) -> User:
    """Register a new user with email/password and create a default company."""
    async with db.begin_nested():
        user, _ = _add_user_with_default_company(
            db,
            email=email,
            display_name=display_name,
            auth_provider="local",
            password_hash=hash_password(password),
        )

    await db.commit()
    await db.refresh(user)
    return user


def build_google_authorization_url(state: str, code_challenge: str) -> str:
    """Build a Google authorization URL for a server-bound PKCE transaction."""
    if not settings.GOOGLE_LOGIN_CLIENT_ID or not settings.GOOGLE_LOGIN_CLIENT_SECRET:
        raise GoogleOAuthConfigurationError(
            "Google sign-in is not configured. Set GOOGLE_LOGIN_CLIENT_ID and "
            "GOOGLE_LOGIN_CLIENT_SECRET."
        )

    params = urlencode(
        {
            "client_id": settings.GOOGLE_LOGIN_CLIENT_ID,
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": settings.GOOGLE_LOGIN_REDIRECT_URI,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{GOOGLE_AUTHORIZATION_URL}?{params}"


async def _get_company_id_for_user(db: AsyncSession, user_id: uuid.UUID) -> uuid.UUID:
    member_result = await db.execute(
        select(CompanyMember).where(CompanyMember.user_id == user_id).limit(1)
    )
    member = member_result.scalars().first()
    if member is None:
        raise GoogleOAuthIdentityError("The linked Google account has no organization.")
    return member.company_id


async def get_or_create_google_user(
    db: AsyncSession,
    identity: GoogleUserInfo,
) -> OAuthUserResult:
    """Resolve a Google subject or create a user without implicit local linking."""
    identity_result = await db.execute(
        select(OAuthIdentity).where(
            OAuthIdentity.provider == "google",
            OAuthIdentity.subject == identity.subject,
        )
    )
    oauth_identity = identity_result.scalar_one_or_none()

    if oauth_identity is not None:
        user_result = await db.execute(select(User).where(User.id == oauth_identity.user_id))
        user = user_result.scalar_one_or_none()
        if user is None:
            raise GoogleOAuthIdentityError("The linked Google account no longer has a user.")

        if user.email != identity.email:
            email_result = await db.execute(select(User).where(User.email == identity.email))
            if email_result.scalar_one_or_none() is None:
                user.email = identity.email
        oauth_identity.provider_email = identity.email
        user.last_login_at = datetime.now(UTC)
        company_id = await _get_company_id_for_user(db, user.id)
        await db.flush()
        return OAuthUserResult(user=user, company_id=company_id, created=False)

    email_result = await db.execute(select(User).where(User.email == identity.email))
    existing_user = email_result.scalar_one_or_none()
    if existing_user is not None:
        if existing_user.auth_provider == "google" and existing_user.password_hash is None:
            db.add(
                OAuthIdentity(
                    id=generate_uuid(),
                    user_id=existing_user.id,
                    provider="google",
                    subject=identity.subject,
                    provider_email=identity.email,
                )
            )
            existing_user.last_login_at = datetime.now(UTC)
            company_id = await _get_company_id_for_user(db, existing_user.id)
            await db.flush()
            return OAuthUserResult(
                user=existing_user,
                company_id=company_id,
                created=False,
            )
        raise OAuthAccountLinkRequired(
            "An account with this email already exists. Sign in with your password "
            "before linking Google."
        )

    user, company = _add_user_with_default_company(
        db,
        email=identity.email,
        display_name=identity.display_name,
        auth_provider="google",
        password_hash=None,
    )
    user.last_login_at = datetime.now(UTC)
    db.add(
        OAuthIdentity(
            id=generate_uuid(),
            user_id=user.id,
            provider="google",
            subject=identity.subject,
            provider_email=identity.email,
        )
    )

    await db.flush()
    return OAuthUserResult(user=user, company_id=company.id, created=True)


async def exchange_google_code(code: str, code_verifier: str) -> GoogleUserInfo:
    """Exchange an authorization code and return a verified Google identity."""
    if not settings.GOOGLE_LOGIN_CLIENT_ID or not settings.GOOGLE_LOGIN_CLIENT_SECRET:
        raise GoogleOAuthConfigurationError("Google sign-in is not configured.")

    logger.info(
        "audit.external_oauth.started",
        extra={
            "provider": "google",
            "operation": "authorization_code_exchange",
        },
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_LOGIN_CLIENT_ID,
                    "client_secret": settings.GOOGLE_LOGIN_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_LOGIN_REDIRECT_URI,
                    "grant_type": "authorization_code",
                    "code_verifier": code_verifier,
                },
            )
            token_response.raise_for_status()
            token_data: dict[str, Any] = token_response.json()
            access_token = token_data.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                raise GoogleOAuthIdentityError("Google did not return an access token.")

            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo_response.raise_for_status()
            userinfo: dict[str, Any] = userinfo_response.json()
    except GoogleOAuthError:
        logger.warning(
            "audit.external_oauth.failed",
            extra={
                "provider": "google",
                "operation": "authorization_code_exchange",
                "reason": "invalid_provider_response",
            },
        )
        raise
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        logger.warning(
            "audit.external_oauth.failed",
            extra={
                "provider": "google",
                "operation": "authorization_code_exchange",
                "reason": type(exc).__name__,
            },
        )
        raise GoogleOAuthExchangeError("Google OAuth exchange failed.") from exc

    subject = userinfo.get("sub")
    email = userinfo.get("email")
    verified_email = userinfo.get("email_verified")
    display_name = userinfo.get("name") or email

    if (
        not isinstance(subject, str)
        or not subject
        or not isinstance(email, str)
        or not email
        or verified_email is not True
        or not isinstance(display_name, str)
    ):
        logger.warning(
            "audit.external_oauth.failed",
            extra={
                "provider": "google",
                "operation": "authorization_code_exchange",
                "reason": "unverified_identity",
            },
        )
        raise GoogleOAuthIdentityError("Google did not return a verified identity.")

    logger.info(
        "audit.external_oauth.succeeded",
        extra={
            "provider": "google",
            "operation": "authorization_code_exchange",
        },
    )
    return GoogleUserInfo(
        subject=subject,
        email=email,
        display_name=display_name,
    )


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
