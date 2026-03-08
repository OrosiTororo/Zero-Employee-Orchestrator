"""Health endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz(client: AsyncClient):
    """ヘルスチェックエンドポイントが正常応答する."""
    response = await client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_readyz(client: AsyncClient):
    """レディネスチェックが正常応答する."""
    response = await client.get("/readyz")
    assert response.status_code == 200
