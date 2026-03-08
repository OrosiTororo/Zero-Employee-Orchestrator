"""Auth endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_creates_user(client: AsyncClient):
    """ログインで新規ユーザーが作成される."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "auth_provider": "local"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "test"
    assert data["role"] == "owner"
    assert "token" in data


@pytest.mark.asyncio
async def test_login_existing_user(client: AsyncClient):
    """既存ユーザーで再ログインできる."""
    await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "auth_provider": "local"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "auth_provider": "local"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """ログアウトが正常に完了する."""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
