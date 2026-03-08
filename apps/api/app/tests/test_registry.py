"""Registry endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_install_and_list_skills(client: AsyncClient):
    """Skillのインストールと一覧取得."""
    install_resp = await client.post(
        "/api/v1/registry/skills/install",
        json={
            "slug": "test-skill",
            "name": "テストスキル",
            "description": "テスト用スキル",
            "skill_type": "custom",
        },
    )
    assert install_resp.status_code == 200
    skill = install_resp.json()
    assert skill["name"] == "テストスキル"
    assert skill["status"] == "experimental"

    list_resp = await client.get("/api/v1/registry/skills")
    assert list_resp.status_code == 200
    skills = list_resp.json()
    assert len(skills) >= 1
