"""Tests for team_service."""

from __future__ import annotations

import pytest

from app.services.team_service import TeamRole, TeamService


@pytest.mark.asyncio
async def test_create_team_registers_owner():
    svc = TeamService()
    team = await svc.create_team(name="demo", company_id="co-1", owner_user_id="u-1")
    assert team.id
    assert len(team.members) == 1
    assert team.members[0].role == TeamRole.OWNER


@pytest.mark.asyncio
async def test_list_teams_filters_by_company():
    svc = TeamService()
    await svc.create_team(name="A", company_id="co-1", owner_user_id="u-1")
    await svc.create_team(name="B", company_id="co-2", owner_user_id="u-2")
    teams = await svc.list_teams(company_id="co-1")
    assert [t.name for t in teams] == ["A"]


@pytest.mark.asyncio
async def test_invite_requires_admin_or_owner():
    svc = TeamService()
    team = await svc.create_team(name="demo", company_id="co-1", owner_user_id="u-owner")
    invitation = await svc.invite_member(
        team_id=team.id,
        email="new@example.com",
        role=TeamRole.MEMBER,
        invited_by="u-owner",
    )
    assert invitation.email == "new@example.com"
    assert invitation.role == TeamRole.MEMBER


@pytest.mark.asyncio
async def test_invite_rejects_owner_role():
    svc = TeamService()
    team = await svc.create_team(name="demo", company_id="co-1", owner_user_id="u-owner")
    with pytest.raises(ValueError):
        await svc.invite_member(
            team_id=team.id,
            email="new@example.com",
            role=TeamRole.OWNER,
            invited_by="u-owner",
        )


@pytest.mark.asyncio
async def test_check_permission_owner_has_all():
    svc = TeamService()
    team = await svc.create_team(name="demo", company_id="co-1", owner_user_id="u-owner")
    assert await svc.check_permission(team.id, "u-owner", "security", "manage") is True
    assert await svc.check_permission(team.id, "u-owner", "team", "delete") is True


@pytest.mark.asyncio
async def test_check_permission_nonmember_is_denied():
    svc = TeamService()
    team = await svc.create_team(name="demo", company_id="co-1", owner_user_id="u-owner")
    assert await svc.check_permission(team.id, "u-stranger", "task", "read") is False
