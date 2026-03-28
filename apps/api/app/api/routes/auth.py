"""Authentication endpoints - registration, login, session management."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.core.rate_limit import limiter
from app.core.security import generate_uuid, hash_password
from app.models.company import Company
from app.models.user import CompanyMember, User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    OAuthLoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    UserRead,
)
from app.services.auth_service import (
    authenticate_user,
    change_password,
    confirm_password_reset,
    create_access_token,
    decode_access_token,
    get_user_by_id,
    register_user,
    request_password_reset,
)

router = APIRouter()


async def _get_user_setup_completed(db: AsyncSession, user_id: str) -> bool:
    """Check if the user's company has completed initial setup."""
    result = await db.execute(
        select(Company)
        .join(CompanyMember, CompanyMember.company_id == Company.id)
        .where(CompanyMember.user_id == uuid.UUID(user_id))
        .limit(1)
    )
    company = result.scalar_one_or_none()
    if company is None:
        return False
    return bool(company.setup_completed)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> User:
    """Extract current user from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.replace("Bearer ", "")
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register", response_model=LoginResponse)
@limiter.limit("5/minute")
async def register(request: Request, req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new account - register with email and password, auto-create default organization."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="This email address is already registered")

    user = await register_user(db, req.email, req.password, req.display_name)
    token = create_access_token(str(user.id))

    return LoginResponse(
        access_token=token,
        user_id=str(user.id),
        display_name=user.display_name,
        setup_completed=False,
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login(request: Request, req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email/password."""
    user = await authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email address or password")

    token = create_access_token(str(user.id))
    setup_done = await _get_user_setup_completed(db, str(user.id))
    return LoginResponse(
        access_token=token,
        user_id=str(user.id),
        display_name=user.display_name,
        setup_completed=setup_done,
    )


@router.get("/google/authorize")
async def google_authorize():
    """Get Google OAuth authorization URL (unimplemented stub)."""
    raise HTTPException(
        status_code=501,
        detail="Google OAuth is not yet available. Please use email registration.",
    )


@router.post("/oauth/login", response_model=LoginResponse)
async def oauth_login(req: OAuthLoginRequest, db: AsyncSession = Depends(get_db)):
    """Login via OAuth provider (Google, GitHub, etc.)."""
    # In production, validate the OAuth code with the provider
    # For now, create/find user by provider info
    # This would be expanded with actual OAuth flow
    raise HTTPException(
        status_code=501,
        detail=f"OAuth provider '{req.provider}' is not yet available. Please use email registration.",
    )


@router.post("/logout")
async def logout():
    """Logout."""
    return {"status": "ok", "message": "Logged out successfully"}


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserRead(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        status=user.status,
        auth_provider=user.auth_provider,
        last_login_at=str(user.last_login_at) if user.last_login_at else None,
        created_at=str(user.created_at),
    )


@router.post("/refresh")
async def refresh_token(user: User = Depends(get_current_user)):
    """Refresh token."""
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}


@router.post("/password-reset/request")
@limiter.limit("3/minute")
async def password_reset_request(
    request: Request,
    req: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset.

    Generates a short-lived reset token.  In production this token
    would be sent via email; in the current implementation it is
    returned directly in the response for development convenience.
    """
    token = await request_password_reset(db, req.email)
    # Always return 200 to prevent email enumeration attacks
    if token is None:
        return {"message": "If an account with this email exists, a reset link has been sent."}
    # NOTE: In production, send the token via email instead of returning it.
    return {
        "message": "If an account with this email exists, a reset link has been sent.",
        "reset_token": token,  # Remove in production — send via email instead
    }


@router.post("/password-reset/confirm")
@limiter.limit("5/minute")
async def password_reset_confirm(
    request: Request,
    req: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """Confirm a password reset with the token received via email."""
    success = await confirm_password_reset(db, req.token, req.new_password)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token",
        )
    return {"message": "Password has been reset successfully"}


@router.post("/change-password")
async def change_password_endpoint(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for the current authenticated user."""
    success = await change_password(db, user, req.current_password, req.new_password)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect",
        )
    return {"message": "Password changed successfully"}


@router.post("/anonymous-session")
@limiter.limit("10/minute")
async def create_anonymous_session(request: Request, db: AsyncSession = Depends(get_db)):
    """Create an anonymous session without login.

    Basic features are available without logging in.
    Logging in enables state sharing across multiple devices.
    Anonymous session data can be linked to an account later.
    """
    anon_id = generate_uuid()
    async with db.begin_nested():
        user = User(
            id=anon_id,
            email=None,
            display_name=f"Anonymous-{str(anon_id)[:8]}",
            role="anonymous",
            status="active",
            auth_provider="anonymous",
        )
        db.add(user)

        company = Company(
            id=generate_uuid(),
            slug=f"anon-{str(anon_id)[:8]}",
            name="Anonymous Workspace",
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

    token = create_access_token(str(user.id))
    return {
        "access_token": token,
        "user_id": str(user.id),
        "company_id": str(company.id),
        "display_name": user.display_name,
        "is_anonymous": True,
        "setup_completed": False,
        "message": "Login to enable state sharing across multiple devices",
    }


class LinkAccountRequest(BaseModel):
    email: str
    password: str
    display_name: str


@router.post("/link-account")
async def link_anonymous_to_account(
    req: LinkAccountRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link an anonymous session to a formal account.

    After starting without login, create an account and
    carry over existing data.
    """
    if user.role != "anonymous":
        raise HTTPException(status_code=400, detail="Already linked to an account")

    # Check for duplicate email
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="This email address is already registered")

    user.email = req.email
    user.display_name = req.display_name
    user.role = "user"
    user.auth_provider = "local"
    user.password_hash = hash_password(req.password)

    await db.commit()

    token = create_access_token(str(user.id))
    return {
        "access_token": token,
        "user_id": str(user.id),
        "display_name": req.display_name,
        "linked": True,
        "message": "Account created. Multi-device sharing is now enabled",
    }


@router.get("/setup-status")
async def get_setup_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check whether the current user's organization has completed initial setup."""
    setup_done = await _get_user_setup_completed(db, str(user.id))
    return {"setup_completed": setup_done}


@router.post("/setup-complete")
async def mark_setup_complete(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark the current user's organization setup as completed."""
    result = await db.execute(
        select(Company)
        .join(CompanyMember, CompanyMember.company_id == Company.id)
        .where(CompanyMember.user_id == user.id)
        .limit(1)
    )
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=404, detail="No organization found")
    company.setup_completed = True
    await db.commit()
    return {"setup_completed": True}


async def get_optional_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> User | None:
    """Authentication is optional — returns user if token is present, otherwise None."""
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    user_id = decode_access_token(token)
    if not user_id:
        return None
    return await get_user_by_id(db, user_id)
