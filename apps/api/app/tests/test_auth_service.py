"""Tests for auth_service (token signing + register/login DB flows)."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import auth_service


class TestTokens:
    def test_access_token_roundtrip(self):
        token = auth_service.create_access_token("user-42")
        assert auth_service.decode_access_token(token) == "user-42"

    def test_access_token_with_bad_signature_returns_none(self):
        assert auth_service.decode_access_token("not.a.token") is None

    def test_password_reset_token_carries_purpose(self):
        token = auth_service.create_password_reset_token("user@example.com")
        assert auth_service.decode_password_reset_token(token) == "user@example.com"

    def test_password_reset_rejects_plain_access_token(self):
        # An access token (no ``purpose`` field) must not be accepted by the
        # password-reset decoder even if the signature is valid.
        access = auth_service.create_access_token("user@example.com")
        assert auth_service.decode_password_reset_token(access) is None


@pytest.mark.asyncio
async def test_register_user_creates_company_and_membership(db_session: AsyncSession):
    user = await auth_service.register_user(
        db=db_session,
        email="new@example.com",
        password="hunter2hunter",
        display_name="New User",
    )
    assert user.email == "new@example.com"
    assert user.role == "owner"
    assert user.auth_provider == "local"
    assert user.password_hash is not None
    assert user.password_hash != "hunter2hunter"


@pytest.mark.asyncio
async def test_authenticate_user_happy_path(db_session: AsyncSession):
    await auth_service.register_user(
        db=db_session,
        email="login@example.com",
        password="correct-horse",
        display_name="Login",
    )
    user = await auth_service.authenticate_user(
        db=db_session,
        email="login@example.com",
        password="correct-horse",
    )
    assert user is not None
    assert user.email == "login@example.com"


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password_returns_none(db_session: AsyncSession):
    await auth_service.register_user(
        db=db_session,
        email="wrong@example.com",
        password="right-pw",
        display_name="Wrong",
    )
    result = await auth_service.authenticate_user(
        db=db_session,
        email="wrong@example.com",
        password="nope",
    )
    assert result is None


@pytest.mark.asyncio
async def test_authenticate_user_missing_email_returns_none(db_session: AsyncSession):
    assert (
        await auth_service.authenticate_user(
            db=db_session,
            email="nobody@example.com",
            password="whatever",
        )
        is None
    )


@pytest.mark.asyncio
async def test_request_password_reset_signs_token_for_existing_email(
    db_session: AsyncSession,
):
    await auth_service.register_user(
        db=db_session,
        email="reset@example.com",
        password="pw",
        display_name="Reset",
    )
    token = await auth_service.request_password_reset(db=db_session, email="reset@example.com")
    assert token is not None
    assert auth_service.decode_password_reset_token(token) == "reset@example.com"


@pytest.mark.asyncio
async def test_request_password_reset_returns_none_for_unknown_email(
    db_session: AsyncSession,
):
    assert (
        await auth_service.request_password_reset(db=db_session, email="ghost@example.com") is None
    )
