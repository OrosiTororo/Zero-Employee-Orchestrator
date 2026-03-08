"""Authentication endpoints - registration, login, session management."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.user import CompanyMember, User
from app.models.company import Company
from app.core.security import generate_uuid, hash_sha256, verify_hash
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
        raise HTTPException(status_code=401, detail="認証が必要です")
    token = authorization.replace("Bearer ", "")
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="無効なトークンです")
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="ユーザーが見つかりません")
    return user


@router.post("/register", response_model=LoginResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """新規アカウント登録 - メールとパスワードで登録し、デフォルト組織を自動作成"""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="このメールアドレスは既に登録されています")

    user = await register_user(db, req.email, req.password, req.display_name)
    token = create_access_token(str(user.id))

    return LoginResponse(
        access_token=token,
        user_id=str(user.id),
        display_name=user.display_name,
    )


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """メール/パスワードでログイン"""
    user = await authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません")

    token = create_access_token(str(user.id))
    return LoginResponse(
        access_token=token,
        user_id=str(user.id),
        display_name=user.display_name,
    )


@router.post("/oauth/login", response_model=LoginResponse)
async def oauth_login(req: OAuthLoginRequest, db: AsyncSession = Depends(get_db)):
    """OAuth プロバイダー経由のログイン (Google, GitHub等)"""
    # In production, validate the OAuth code with the provider
    # For now, create/find user by provider info
    # This would be expanded with actual OAuth flow
    raise HTTPException(
        status_code=501,
        detail=f"OAuth provider '{req.provider}' は準備中です。メール登録をご利用ください。",
    )


@router.post("/logout")
async def logout():
    """ログアウト"""
    return {"status": "ok", "message": "ログアウトしました"}


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
