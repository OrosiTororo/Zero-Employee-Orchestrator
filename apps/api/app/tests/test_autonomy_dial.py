"""Tests for the Autonomy Dial endpoints (B-P4)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.policies.autonomy_boundary import AutonomyLevel


async def _create_company(client: AsyncClient) -> str:
    res = await client.post(
        "/api/v1/companies",
        json={"name": "Dial Co", "slug": "dial-co"},
    )
    assert res.status_code == 200
    return res.json()["id"]


@pytest.mark.asyncio
async def test_get_autonomy_returns_default(client: AsyncClient):
    company_id = await _create_company(client)
    res = await client.get(f"/api/v1/companies/{company_id}/autonomy")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["company_default"] in {level.value for level in AutonomyLevel}
    assert body["effective"] == body["company_default"]
    assert body["override_active"] is False
    assert body["override_expires_at"] is None


@pytest.mark.asyncio
async def test_set_autonomy_default_persists(client: AsyncClient):
    company_id = await _create_company(client)
    res = await client.patch(
        f"/api/v1/companies/{company_id}/autonomy",
        json={"level": "assist"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["company_default"] == "assist"

    again = await client.get(f"/api/v1/companies/{company_id}/autonomy")
    assert again.json()["company_default"] == "assist"


@pytest.mark.asyncio
async def test_session_override_wins_over_default(client: AsyncClient):
    company_id = await _create_company(client)
    await client.patch(
        f"/api/v1/companies/{company_id}/autonomy",
        json={"level": "autonomous"},
    )

    override = await client.post(
        f"/api/v1/companies/{company_id}/autonomy/override",
        json={"level": "observe", "ttl_minutes": 30, "reason": "demo"},
    )
    assert override.status_code == 200, override.text
    body = override.json()
    assert body["company_default"] == "autonomous"
    assert body["effective"] == "observe"
    assert body["override_active"] is True
    assert body["override_expires_at"] is not None


@pytest.mark.asyncio
async def test_override_requires_ttl_or_session_end(client: AsyncClient):
    company_id = await _create_company(client)
    res = await client.post(
        f"/api/v1/companies/{company_id}/autonomy/override",
        json={"level": "assist"},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_clear_override(client: AsyncClient):
    company_id = await _create_company(client)
    await client.post(
        f"/api/v1/companies/{company_id}/autonomy/override",
        json={"level": "observe", "until_session_end": True},
    )
    cleared = await client.delete(f"/api/v1/companies/{company_id}/autonomy/override")
    assert cleared.status_code == 200
    body = cleared.json()
    assert body["override_active"] is False
    assert body["effective"] == body["company_default"]
