"""Company endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_company(client: AsyncClient):
    """会社を作成できる."""
    response = await client.post(
        "/api/v1/companies",
        json={"name": "テスト株式会社", "slug": "test-corp", "mission": "AIで業務革新"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "テスト株式会社"
    assert data["slug"] == "test-corp"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_list_companies(client: AsyncClient):
    """会社一覧を取得できる."""
    await client.post(
        "/api/v1/companies",
        json={"name": "会社A", "slug": "company-a"},
    )
    response = await client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_dashboard_summary(client: AsyncClient):
    """ダッシュボード要約を取得できる."""
    create_resp = await client.post(
        "/api/v1/companies",
        json={"name": "テスト", "slug": "test"},
    )
    company_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/companies/{company_id}/dashboard-summary")
    assert response.status_code == 200
