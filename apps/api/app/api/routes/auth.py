"""Authentication endpoints."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.user import User

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    auth_provider: str = "local"


class LoginResponse(BaseModel):
    user_id: str
    display_name: str
    role: str
    token: str


class UserResponse(BaseModel):
    id: str
    email: str | None
    display_name: str
    role: str
    status: str


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """ログインまたは新規ユーザー作成"""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=req.email,
            display_name=req.email.split("@")[0],
            role="owner",
            status="active",
            auth_provider=req.auth_provider,
            last_login_at=datetime.utcnow(),
        )
        db.add(user)
        await db.flush()
    else:
        user.last_login_at = datetime.utcnow()
    return LoginResponse(
        user_id=str(user.id),
        display_name=user.display_name,
        role=user.role,
        token=str(uuid.uuid4()),
    )


@router.post("/logout")
async def logout():
    """ログアウト"""
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
async def get_me(db: AsyncSession = Depends(get_db)):
    """現在のユーザー情報を取得"""
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        status=user.status,
    )
