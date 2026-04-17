"""One-shot Crew spawn API — CrewAI-inspired role prototyping.

Instead of installing a plugin + registering skills + wiring adapters, a user
can POST a crew definition (list of roles) and immediately fan out a task to
each role. Mirrors CrewAI's ``Crew(agents=[...])`` one-liner.

Ephemeral by design: crews live in memory for the duration of a session. They
inherit ZEO's approval-gate + audit-log chain automatically, so a crew
spawned here is still governed by the same policies as a long-lived plugin.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crews", tags=["crews"])


@dataclass
class CrewRole:
    name: str
    preferred_model: str = "anthropic/claude-sonnet"
    description: str = ""


@dataclass
class CrewMember:
    role: CrewRole
    status: str = "idle"
    last_result: str | None = None
    tokens_used: int = 0


@dataclass
class Crew:
    id: str
    name: str
    members: list[CrewMember]
    execution_mode: str = "parallel"
    created_at: str = ""
    last_run_at: str | None = None
    last_run_results: list[dict] = field(default_factory=list)


_CREWS: dict[str, Crew] = {}

_ROLE_PRESETS: dict[str, list[CrewRole]] = {
    "startup-founding-team": [
        CrewRole(name="CEO", preferred_model="anthropic/claude-opus", description="Sets strategy"),
        CrewRole(name="CTO", preferred_model="anthropic/claude-sonnet", description="Owns tech"),
        CrewRole(name="CMO", preferred_model="anthropic/claude-sonnet", description="Owns growth"),
        CrewRole(name="COO", preferred_model="anthropic/claude-haiku", description="Owns ops"),
    ],
    "research-squad": [
        CrewRole(name="Researcher", description="Gathers primary sources"),
        CrewRole(name="Analyst", description="Synthesizes findings"),
        CrewRole(name="FactChecker", description="Validates citations"),
    ],
    "content-studio": [
        CrewRole(name="Editor", description="Extracts key points"),
        CrewRole(name="Writer", description="Drafts long-form copy"),
        CrewRole(name="SocialManager", description="Adapts for social channels"),
    ],
    "sre-response": [
        CrewRole(name="FirstResponder", description="Triages the page"),
        CrewRole(name="Mitigator", description="Applies short-term fix"),
        CrewRole(name="PostMortemWriter", description="Drafts the RCA"),
    ],
}


class CrewRoleSpec(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    preferred_model: str = "anthropic/claude-sonnet"
    description: str = ""


class SpawnCrewRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    roles: list[CrewRoleSpec] = Field(default_factory=list)
    preset: str | None = Field(
        default=None,
        description="Use a named role preset instead of passing roles explicitly.",
    )
    execution_mode: str = Field(default="parallel", pattern=r"^(parallel|sequential)$")


class DispatchTaskRequest(BaseModel):
    instruction: str = Field(..., min_length=1)
    per_role_context: dict[str, str] = Field(default_factory=dict)


def _serialize(crew: Crew) -> dict:
    return {
        "id": crew.id,
        "name": crew.name,
        "execution_mode": crew.execution_mode,
        "created_at": crew.created_at,
        "last_run_at": crew.last_run_at,
        "members": [
            {
                "role": m.role.name,
                "preferred_model": m.role.preferred_model,
                "description": m.role.description,
                "status": m.status,
                "tokens_used": m.tokens_used,
            }
            for m in crew.members
        ],
        "last_run_results": crew.last_run_results,
    }


@router.get("/presets")
async def list_presets(_: User = Depends(get_current_user)) -> dict:
    """List built-in role presets (CrewAI-style kits)."""
    return {
        "presets": {
            slug: [{"name": r.name, "description": r.description} for r in roles]
            for slug, roles in _ROLE_PRESETS.items()
        }
    }


@router.post("")
async def spawn_crew(
    request: SpawnCrewRequest,
    _: User = Depends(get_current_user),
) -> dict:
    """Instantiate a crew in one call — no plugin install required."""
    roles: list[CrewRole] = []
    if request.preset:
        if request.preset not in _ROLE_PRESETS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown preset '{request.preset}'. Available: {sorted(_ROLE_PRESETS)}",
            )
        roles.extend(_ROLE_PRESETS[request.preset])
    roles.extend(
        CrewRole(name=r.name, preferred_model=r.preferred_model, description=r.description)
        for r in request.roles
    )
    if not roles:
        raise HTTPException(
            status_code=400,
            detail="Supply at least one role (via 'roles' or 'preset').",
        )
    crew_id = str(uuid.uuid4())
    crew = Crew(
        id=crew_id,
        name=request.name,
        members=[CrewMember(role=r) for r in roles],
        execution_mode=request.execution_mode,
        created_at=datetime.now(UTC).isoformat(),
    )
    _CREWS[crew_id] = crew
    return {"crew": _serialize(crew)}


@router.get("")
async def list_crews(_: User = Depends(get_current_user)) -> dict:
    return {"crews": [_serialize(c) for c in _CREWS.values()]}


@router.get("/{crew_id}")
async def get_crew(crew_id: str, _: User = Depends(get_current_user)) -> dict:
    crew = _CREWS.get(crew_id)
    if not crew:
        raise HTTPException(status_code=404, detail=f"Crew not found: {crew_id}")
    return {"crew": _serialize(crew)}


@router.delete("/{crew_id}")
async def disband_crew(crew_id: str, _: User = Depends(get_current_user)) -> dict:
    if crew_id not in _CREWS:
        raise HTTPException(status_code=404, detail=f"Crew not found: {crew_id}")
    _CREWS.pop(crew_id)
    return {"disbanded": crew_id}


async def _run_one(member: CrewMember, instruction: str, extra_context: str) -> dict:
    """Dispatch a single task to one member via the LLM gateway (best-effort)."""
    member.status = "running"
    prompt = instruction
    if extra_context:
        prompt = f"Context:\n{extra_context}\n\nTask:\n{instruction}"
    try:
        from app.providers.gateway import CompletionRequest, ExecutionMode, LLMGateway

        gw = LLMGateway()
        resp = await gw.complete(
            CompletionRequest(
                messages=[
                    {
                        "role": "system",
                        "content": f"You are acting as the {member.role.name}. {member.role.description}".strip(),
                    },
                    {"role": "user", "content": prompt},
                ],
                mode=ExecutionMode.QUALITY,
                temperature=0.5,
                max_tokens=1024,
            )
        )
        member.status = "succeeded"
        member.last_result = resp.content
        member.tokens_used = resp.tokens_input + resp.tokens_output
        return {
            "role": member.role.name,
            "status": "succeeded",
            "content": resp.content,
            "model": resp.model_used,
            "tokens": member.tokens_used,
        }
    except Exception as e:  # noqa: BLE001
        logger.warning("Crew member %s failed: %s", member.role.name, e)
        member.status = "failed"
        member.last_result = f"Error: {e}"
        return {"role": member.role.name, "status": "failed", "error": str(e)}


@router.post("/{crew_id}/dispatch")
async def dispatch_task(
    crew_id: str,
    request: DispatchTaskRequest,
    _: User = Depends(get_current_user),
) -> dict:
    """Fan a single instruction out to every crew member.

    Returns an array of per-role results. Runs in parallel unless the crew
    was spawned with ``execution_mode=sequential``.
    """
    crew = _CREWS.get(crew_id)
    if not crew:
        raise HTTPException(status_code=404, detail=f"Crew not found: {crew_id}")
    crew.last_run_at = datetime.now(UTC).isoformat()
    crew.last_run_results = []

    if crew.execution_mode == "sequential":
        results = []
        for member in crew.members:
            ctx = request.per_role_context.get(member.role.name, "")
            results.append(await _run_one(member, request.instruction, ctx))
    else:
        coros = [
            _run_one(m, request.instruction, request.per_role_context.get(m.role.name, ""))
            for m in crew.members
        ]
        results = await asyncio.gather(*coros)
    crew.last_run_results = results
    return {"crew_id": crew_id, "results": results}
