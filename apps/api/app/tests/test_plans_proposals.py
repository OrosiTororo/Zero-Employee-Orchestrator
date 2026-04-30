"""Tests for the plan-first proposal/diff endpoints (B-P1, B-P3)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _create_company(client: AsyncClient) -> str:
    res = await client.post(
        "/api/v1/companies",
        json={"name": "Plan Co", "slug": "plan-co"},
    )
    assert res.status_code == 200
    return res.json()["id"]


@pytest.mark.asyncio
async def test_propose_plan_persists_proposal(client: AsyncClient):
    company_id = await _create_company(client)

    res = await client.post(
        f"/api/v1/companies/{company_id}/plans",
        json={"goal": "Ship the new onboarding flow", "autonomy": "semi_auto"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["plan_id"]
    assert body["autonomy"] == "semi_auto"
    assert body["plan_md"].startswith("# 実行計画")
    assert len(body["tasks"]) >= 5
    # The default plan_writer template ends with an approval gate.
    assert body["requires_approval"] is True


@pytest.mark.asyncio
async def test_propose_plan_observe_forces_approval(client: AsyncClient):
    company_id = await _create_company(client)

    res = await client.post(
        f"/api/v1/companies/{company_id}/plans",
        json={"goal": "Read-only research", "autonomy": "observe"},
    )
    assert res.status_code == 200
    assert res.json()["requires_approval"] is True


@pytest.mark.asyncio
async def test_propose_plan_rejects_invalid_autonomy(client: AsyncClient):
    company_id = await _create_company(client)

    res = await client.post(
        f"/api/v1/companies/{company_id}/plans",
        json={"goal": "x", "autonomy": "lightspeed"},
    )
    # Invalid autonomy is rejected before pydantic length validation kicks in.
    assert res.status_code in (400, 422)


@pytest.mark.asyncio
async def test_list_plans_returns_proposals(client: AsyncClient):
    company_id = await _create_company(client)
    for i in range(2):
        res = await client.post(
            f"/api/v1/companies/{company_id}/plans",
            json={"goal": f"Goal {i}", "autonomy": "semi_auto"},
        )
        assert res.status_code == 200

    listing = await client.get(f"/api/v1/companies/{company_id}/plans")
    assert listing.status_code == 200
    items = listing.json()
    assert len(items) >= 2
    assert all(item["goal"] is not None for item in items)
    versions = sorted(item["version_no"] for item in items)
    assert versions == [1, 2]


@pytest.mark.asyncio
async def test_plan_diff_against_prior_revision(client: AsyncClient):
    company_id = await _create_company(client)

    p1 = await client.post(
        f"/api/v1/companies/{company_id}/plans",
        json={"goal": "Iterate the onboarding flow", "autonomy": "semi_auto"},
    )
    p2 = await client.post(
        f"/api/v1/companies/{company_id}/plans",
        json={"goal": "Iterate the onboarding flow v2", "autonomy": "semi_auto"},
    )
    base_id = p2.json()["plan_id"]
    against_id = p1.json()["plan_id"]

    diff = await client.get(
        f"/api/v1/companies/{company_id}/plans/{base_id}/diff?against={against_id}"
    )
    assert diff.status_code == 200, diff.text
    body = diff.json()
    assert body["base_plan_id"] == base_id
    assert body["against_plan_id"] == against_id
    # The proposal template is identical for both, so nothing should diff.
    assert body["added_tasks"] == []
    assert body["removed_tasks"] == []
    assert isinstance(body["modified_tasks"], list)


@pytest.mark.asyncio
async def test_plan_tree_contains_root_only_when_no_children(client: AsyncClient):
    company_id = await _create_company(client)
    res = await client.post(
        f"/api/v1/companies/{company_id}/plans",
        json={"goal": "Plan with no sub-orch yet", "autonomy": "semi_auto"},
    )
    plan_id = res.json()["plan_id"]

    tree = await client.get(f"/api/v1/companies/{company_id}/plans/{plan_id}/tree")
    assert tree.status_code == 200
    body = tree.json()
    assert body["id"] == plan_id
    assert body["children"] == []
