"""Auth endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_creates_user(client: AsyncClient):
    """登録で新規ユーザーが作成される."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "display_name": "test",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "test"
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_existing_user(client: AsyncClient):
    """既存ユーザーで再ログインできる."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test2@example.com",
            "password": "testpassword123",
            "display_name": "test2",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test2@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """ログアウトが正常に完了する."""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_password_reset_returns_token_in_debug(client: AsyncClient):
    """DEBUG時のみ開発用にリセットトークンが返る."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "reset-debug@example.com",
            "password": "testpassword123",
            "display_name": "reset-debug",
        },
    )
    response = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "reset-debug@example.com"},
    )
    assert response.status_code == 200
    assert response.json().get("reset_token")


@pytest.mark.asyncio
async def test_password_reset_hides_token_when_not_debug(client: AsyncClient, monkeypatch):
    """本番相当(DEBUG=false)ではリセットトークンがレスポンスに漏れない."""
    from app.core.config import settings

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "reset-prod@example.com",
            "password": "testpassword123",
            "display_name": "reset-prod",
        },
    )
    monkeypatch.setattr(settings, "DEBUG", False)
    response = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "reset-prod@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("reset_token") is None
    assert "sent" in data["message"]


@pytest.mark.asyncio
async def test_password_reset_unknown_email_same_message(client: AsyncClient):
    """未知のメールでも同一メッセージ(メール列挙攻撃の防止)."""
    known = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "reset-debug@example.com"},
    )
    unknown = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "no-such-user@example.com"},
    )
    assert unknown.status_code == 200
    assert unknown.json()["message"] == known.json()["message"]
    assert unknown.json().get("reset_token") is None


@pytest.mark.asyncio
async def test_password_reset_confirm_flow(client: AsyncClient):
    """リセットトークンで新パスワードを設定しログインできる."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "reset-flow@example.com",
            "password": "oldpassword123",
            "display_name": "reset-flow",
        },
    )
    request_resp = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "reset-flow@example.com"},
    )
    token = request_resp.json()["reset_token"]
    confirm_resp = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "newpassword456"},
    )
    assert confirm_resp.status_code == 200
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset-flow@example.com", "password": "newpassword456"},
    )
    assert login_resp.status_code == 200
