"""Ticket endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_tickets(client: AsyncClient):
    """チケットの作成と一覧取得."""
    company = await client.post(
        "/api/v1/companies",
        json={"name": "テスト", "slug": "ticket-test"},
    )
    company_id = company.json()["id"]

    create_resp = await client.post(
        f"/api/v1/companies/{company_id}/tickets",
        json={"title": "テストタスク", "description": "説明文", "priority": "high"},
    )
    assert create_resp.status_code == 200
    ticket = create_resp.json()
    assert ticket["title"] == "テストタスク"
    assert ticket["ticket_no"] == 1
    assert ticket["status"] == "draft"

    list_resp = await client.get(f"/api/v1/companies/{company_id}/tickets")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


@pytest.mark.asyncio
async def test_ticket_lifecycle(client: AsyncClient):
    """チケットのライフサイクル（作成→閉じる→再開）."""
    company = await client.post(
        "/api/v1/companies",
        json={"name": "lifecycle", "slug": "lifecycle-test"},
    )
    company_id = company.json()["id"]

    ticket = await client.post(
        f"/api/v1/companies/{company_id}/tickets",
        json={"title": "ライフサイクルテスト"},
    )
    ticket_id = ticket.json()["id"]

    close_resp = await client.post(f"/api/v1/tickets/{ticket_id}/close")
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "closed"

    reopen_resp = await client.post(f"/api/v1/tickets/{ticket_id}/reopen")
    assert reopen_resp.status_code == 200
    assert reopen_resp.json()["status"] == "reopened"
