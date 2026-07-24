"""Authentication dependencies shared by API routes."""

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.user import User
from app.services.auth_service import decode_access_token, get_user_by_id


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
