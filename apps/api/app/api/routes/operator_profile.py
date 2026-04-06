"""Operator Profile & Global Instructions API.

Inspired by Claude Cowork's about-me.md and global instructions pattern.
Stores user context (role, priorities, work style) so AI agents can personalize
responses without re-asking every session.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operator-profile", tags=["operator-profile"])

_PROFILE_DIR = Path.home() / ".zero-employee"


class OperatorProfile(BaseModel):
    """User context for AI personalization."""

    display_name: str = ""
    role: str = ""
    team: str = ""
    industry: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    current_priorities: list[str] = Field(default_factory=list)
    work_style: str = ""
    preferred_language: str = "en"
    timezone: str = ""


class GlobalInstructions(BaseModel):
    """Persistent instructions applied to every AI conversation."""

    instructions: str = ""


# ------------------------------------------------------------------ #
#  Profile
# ------------------------------------------------------------------ #


def _profile_path(user_id: str) -> Path:
    return _PROFILE_DIR / f"operator-profile-{user_id}.json"


@router.get("/profile", response_model=OperatorProfile)
async def get_profile(user: User = Depends(get_current_user)):
    """Get the current operator profile."""
    path = _profile_path(user.id)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return OperatorProfile(**data)
    return OperatorProfile(display_name=user.display_name or "")


@router.put("/profile", response_model=OperatorProfile)
async def update_profile(profile: OperatorProfile, user: User = Depends(get_current_user)):
    """Update operator profile. AI agents read this to personalize responses."""
    _PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    path = _profile_path(user.id)
    path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    path.chmod(0o600)
    logger.info("Operator profile updated for user %s", user.id)
    return profile


# ------------------------------------------------------------------ #
#  Global Instructions
# ------------------------------------------------------------------ #


def _instructions_path(user_id: str) -> Path:
    return _PROFILE_DIR / f"global-instructions-{user_id}.txt"


@router.get("/instructions", response_model=GlobalInstructions)
async def get_instructions(user: User = Depends(get_current_user)):
    """Get global instructions (applied to every AI conversation)."""
    path = _instructions_path(user.id)
    if path.exists():
        return GlobalInstructions(instructions=path.read_text(encoding="utf-8"))
    return GlobalInstructions()


@router.put("/instructions", response_model=GlobalInstructions)
async def update_instructions(body: GlobalInstructions, user: User = Depends(get_current_user)):
    """Update global instructions. These are injected into every AI prompt."""
    _PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    path = _instructions_path(user.id)
    path.write_text(body.instructions, encoding="utf-8")
    path.chmod(0o600)
    logger.info(
        "Global instructions updated for user %s (%d chars)", user.id, len(body.instructions)
    )
    return body
