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
