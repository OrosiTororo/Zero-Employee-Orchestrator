"""Registry endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_install_and_list_skills(client: AsyncClient):
    """Skillのインストールと一覧取得."""
    # 認証トークンを取得するためにユーザー登録
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "registry_test@example.com",
            "password": "TestPassword123!",
            "display_name": "Registry Tester",
        },
    )
    assert reg_resp.status_code == 200
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    install_resp = await client.post(
        "/api/v1/registry/skills/install",
        json={
            "slug": "test-skill",
            "name": "テストスキル",
            "description": "テスト用スキル",
            "skill_type": "custom",
        },
        headers=headers,
    )
    assert install_resp.status_code == 201
    skill = install_resp.json()
    assert skill["name"] == "テストスキル"
    assert skill["status"] == "experimental"

    list_resp = await client.get("/api/v1/registry/skills")
    assert list_resp.status_code == 200
    skills = list_resp.json()
    assert len(skills) >= 1
