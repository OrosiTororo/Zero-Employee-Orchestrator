"""Authentication endpoints - registration, login, session management."""

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
    LoginRequest,
    LoginResponse,
    OAuthLoginRequest,
    RegisterRequest,
    UserRead,
)
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    get_user_by_id,
    register_user,
)

router = APIRouter()


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
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login(request: Request, req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email/password."""
    user = await authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=401, detail="Incorrect email address or password"
        )

    token = create_access_token(str(user.id))
    return LoginResponse(
        access_token=token,
        user_id=str(user.id),
        display_name=user.display_name,
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
    """現在のユーザー情報を取得"""
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
    """トークンの更新"""
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}


@router.post("/anonymous-session")
@limiter.limit("10/minute")
async def create_anonymous_session(request: Request, db: AsyncSession = Depends(get_db)):
    """ログイン不要の匿名セッション.

    ログインしなくても基本機能が使える。
    ログインすると、複数デバイスでの状態共有が可能になる。
    匿名セッションのデータは後からアカウントに紐付け可能。
    """
    anon_id = generate_uuid()
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
        "message": "ログインすると複数デバイスでの状態共有が可能になります",
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
    """匿名セッションを正式アカウントに紐付け.

    ログイン不要で使い始めた後、アカウントを作成して
    既存のデータを引き継ぐ。
    """
    if user.role != "anonymous":
        raise HTTPException(status_code=400, detail="既にアカウントに紐付けられています")

    # メールの重複チェック
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
        "message": "アカウントが作成されました。複数デバイスでの共有が有効です",
    }


async def get_optional_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> User | None:
    """認証は任意 — トークンがあればユーザーを返し、なければNone."""
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    user_id = decode_access_token(token)
    if not user_id:
        return None
    return await get_user_by_id(db, user_id)
