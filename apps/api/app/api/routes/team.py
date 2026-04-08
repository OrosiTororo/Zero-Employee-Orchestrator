"""Team management API endpoints.

Provides team creation, invitations, member management, and permission checks.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.models.user import User
from app.services.team_service import TeamRole, team_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["teams"])


# ---------- Request Schemas ----------


class CreateTeamRequest(BaseModel):
    """Team creation request."""

    name: str = Field(..., min_length=1, max_length=100)
    company_id: str = Field(..., min_length=1)
    owner_user_id: str = Field(..., min_length=1)


class InviteMemberRequest(BaseModel):
    """Member invitation request."""

    email: str = Field(..., min_length=1)
    role: str = Field(default="member")
    invited_by: str = Field(..., min_length=1)


class AcceptInvitationRequest(BaseModel):
    """Accept invitation request."""

    user_id: str = Field(..., min_length=1)


class RemoveMemberRequest(BaseModel):
    """Remove member request."""

    removed_by: str = Field(..., min_length=1)


# ---------- Response Schemas ----------


class TeamMemberResponse(BaseModel):
    """Team member in a team response."""

    user_id: str
    email: str
    role: str
    joined_at: Any = None
    is_active: bool


class TeamResponse(BaseModel):
    """Response for a single team."""

    id: str
    name: str
    company_id: str
    members: list[TeamMemberResponse]
    created_at: Any = None
    settings: dict | None = None


class InvitationResponse(BaseModel):
    """Response for a team invitation."""

    id: str
    team_id: str
    email: str
    role: str
    invited_by: str
    created_at: Any = None
    expires_at: Any = None


class AcceptedMemberResponse(BaseModel):
    """Response for an accepted invitation."""

    user_id: str
    email: str
    role: str
    joined_at: Any = None
    is_active: bool


class RemoveMemberResponse(BaseModel):
    """Response for member removal."""

    status: str
    team_id: str
    user_id: str


# ---------- Endpoints ----------


@router.post("", status_code=201, response_model=TeamResponse)
async def create_team(req: CreateTeamRequest, user: User = Depends(get_current_user)):
    """Create a team."""
    team = await team_service.create_team(
        name=req.name,
        company_id=req.company_id,
        owner_user_id=req.owner_user_id,
    )
    return _team_to_dict(team)


@router.get("", response_model=list[TeamResponse])
async def list_teams(
    company_id: str = Query(..., min_length=1),
    user: User = Depends(get_current_user),
):
    """Get list of teams for a company."""
    teams = await team_service.list_teams(company_id)
    return [_team_to_dict(t) for t in teams]


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(team_id: str, user: User = Depends(get_current_user)):
    """Get a team by ID."""
    team = await team_service.get_team(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return _team_to_dict(team)


@router.post("/{team_id}/invite", status_code=201, response_model=InvitationResponse)
async def invite_member(
    team_id: str, req: InviteMemberRequest, user: User = Depends(get_current_user)
):
    """Invite a member to a team."""
    try:
        role = TeamRole(req.role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {req.role}. Valid values: {[r.value for r in TeamRole]}",
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


@router.post("/invitations/{invitation_id}/accept", response_model=AcceptedMemberResponse)
async def accept_invitation(
    invitation_id: str, req: AcceptInvitationRequest, user: User = Depends(get_current_user)
):
    """Accept invitation and join a team."""
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


@router.delete("/{team_id}/members/{user_id}", response_model=RemoveMemberResponse)
async def remove_member(
    team_id: str, user_id: str, req: RemoveMemberRequest, user: User = Depends(get_current_user)
):
    """Remove a member from a team."""
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


# ---------- Helpers ----------


def _team_to_dict(team) -> dict:
    """Convert Team to dict."""
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
