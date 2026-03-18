"""チーム管理 API エンドポイント.

チームの作成・招待・メンバー管理・権限チェックを提供する。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.team_service import TeamRole, team_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["teams"])


# ---------- Schemas ----------


class CreateTeamRequest(BaseModel):
    """チーム作成リクエスト."""

    name: str = Field(..., min_length=1, max_length=100)
    company_id: str = Field(..., min_length=1)
    owner_user_id: str = Field(..., min_length=1)


class InviteMemberRequest(BaseModel):
    """メンバー招待リクエスト."""

    email: str = Field(..., min_length=1)
    role: str = Field(default="member")
    invited_by: str = Field(..., min_length=1)


class AcceptInvitationRequest(BaseModel):
    """招待受諾リクエスト."""

    user_id: str = Field(..., min_length=1)


class RemoveMemberRequest(BaseModel):
    """メンバー除外リクエスト."""

    removed_by: str = Field(..., min_length=1)


# ---------- Endpoints ----------


@router.post("", status_code=201)
async def create_team(req: CreateTeamRequest) -> dict:
    """チームを作成する."""
    team = await team_service.create_team(
        name=req.name,
        company_id=req.company_id,
        owner_user_id=req.owner_user_id,
    )
    return _team_to_dict(team)


@router.get("")
async def list_teams(
    company_id: str = Query(..., min_length=1),
) -> list[dict]:
    """企業のチーム一覧を取得する."""
    teams = await team_service.list_teams(company_id)
    return [_team_to_dict(t) for t in teams]


@router.get("/{team_id}")
async def get_team(team_id: str) -> dict:
    """チームを ID で取得する."""
    team = await team_service.get_team(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="チームが見つかりません")
    return _team_to_dict(team)


@router.post("/{team_id}/invite", status_code=201)
async def invite_member(team_id: str, req: InviteMemberRequest) -> dict:
    """メンバーをチームに招待する."""
    try:
        role = TeamRole(req.role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"無効なロール: {req.role}。有効値: {[r.value for r in TeamRole]}",
        )

    try:
        invitation = await team_service.invite_member(
            team_id=team_id,
            email=req.email,
            role=role,
            invited_by=req.invited_by,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return {
        "id": invitation.id,
        "team_id": invitation.team_id,
        "email": invitation.email,
        "role": invitation.role.value,
        "invited_by": invitation.invited_by,
        "created_at": invitation.created_at,
        "expires_at": invitation.expires_at,
    }


@router.post("/invitations/{invitation_id}/accept")
async def accept_invitation(invitation_id: str, req: AcceptInvitationRequest) -> dict:
    """招待を受諾してチームに参加する."""
    try:
        member = await team_service.accept_invitation(
            invitation_id=invitation_id,
            user_id=req.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "user_id": member.user_id,
        "email": member.email,
        "role": member.role.value,
        "joined_at": member.joined_at,
        "is_active": member.is_active,
    }


@router.delete("/{team_id}/members/{user_id}")
async def remove_member(team_id: str, user_id: str, req: RemoveMemberRequest) -> dict:
    """メンバーをチームから除外する."""
    try:
        await team_service.remove_member(
            team_id=team_id,
            user_id=user_id,
            removed_by=req.removed_by,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return {"status": "removed", "team_id": team_id, "user_id": user_id}


# ---------- ヘルパー ----------


def _team_to_dict(team) -> dict:
    """Team を dict に変換する."""
    return {
        "id": team.id,
        "name": team.name,
        "company_id": team.company_id,
        "members": [
            {
                "user_id": m.user_id,
                "email": m.email,
                "role": m.role.value,
                "joined_at": m.joined_at,
                "is_active": m.is_active,
            }
            for m in team.members
        ],
        "created_at": team.created_at,
        "settings": team.settings,
    }
