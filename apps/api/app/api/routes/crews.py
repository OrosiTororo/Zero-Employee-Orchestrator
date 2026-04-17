"""One-shot Crew spawn API — CrewAI-inspired role prototyping.

Instead of installing a plugin + registering skills + wiring adapters, a user
can POST a crew definition (list of roles) and immediately fan out a task to
each role. Mirrors CrewAI's ``Crew(agents=[...])`` one-liner.

Ephemeral by design: crews live in memory for the duration of a session. They
inherit ZEO's approval-gate + audit-log chain automatically, so a crew
spawned here is still governed by the same policies as a long-lived plugin.

Every crew is owned by exactly one user (``user_id``). List/get/dispatch
operations filter by owner to keep one user's crews invisible to another.
Spawn, dispatch and disband all emit audit-log rows when the caller belongs
to a company.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.core.rate_limit import limiter
from app.core.security import generate_uuid
from app.models.audit import AuditLog
from app.models.user import CompanyMember, User
from app.security.pii_guard import detect_and_mask_pii
from app.security.prompt_guard import ThreatLevel, scan_prompt_injection

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
    user_id: str
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


def _owned_by(crew: Crew, user: User) -> bool:
    return crew.user_id == str(user.id)


def _scrub_pii(text: str) -> str:
    """Mask PII in a free-text user-supplied field before persistence."""
    if not text:
        return text
    return detect_and_mask_pii(text).masked_text


async def _resolve_company_id(db: AsyncSession, user: User) -> uuid.UUID | None:
    result = await db.execute(
        select(CompanyMember.company_id).where(CompanyMember.user_id == user.id).limit(1)
    )
    return result.scalar_one_or_none()


async def _audit(
    db: AsyncSession,
    user: User,
    event_type: str,
    target_id: str | None,
    details: dict,
) -> None:
    company_id = await _resolve_company_id(db, user)
    if company_id is None:
        return
    db.add(
        AuditLog(
            id=generate_uuid(),
            company_id=company_id,
            actor_type="user",
            actor_user_id=user.id,
            event_type=event_type,
            target_type="crew",
            target_id=uuid.UUID(target_id) if target_id else None,
            details_json=details,
        )
    )
    await db.commit()


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
@limiter.limit("30/minute")
async def spawn_crew(
    request: Request,
    req: SpawnCrewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Instantiate a crew in one call — no plugin install required."""
    roles: list[CrewRole] = []
    if req.preset:
        if req.preset not in _ROLE_PRESETS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unknown preset '{req.preset}'. Available: {sorted(_ROLE_PRESETS)}. "
                    "List via GET /crews/presets."
                ),
            )
        roles.extend(_ROLE_PRESETS[req.preset])
    roles.extend(
        CrewRole(name=r.name, preferred_model=r.preferred_model, description=r.description)
        for r in req.roles
    )
    if not roles:
        raise HTTPException(
            status_code=400,
            detail="Supply at least one role via 'roles' or 'preset'. See GET /crews/presets.",
        )
    crew_id = str(uuid.uuid4())
    crew = Crew(
        id=crew_id,
        name=_scrub_pii(req.name),
        user_id=str(user.id),
        members=[CrewMember(role=r) for r in roles],
        execution_mode=req.execution_mode,
        created_at=datetime.now(UTC).isoformat(),
    )
    _CREWS[crew_id] = crew

    await _audit(
        db,
        user,
        "crew.spawned",
        crew_id,
        {"name": req.name, "preset": req.preset, "member_count": len(roles)},
    )
    return {"crew": _serialize(crew)}


@router.get("")
async def list_crews(user: User = Depends(get_current_user)) -> dict:
    return {"crews": [_serialize(c) for c in _CREWS.values() if _owned_by(c, user)]}


@router.get("/{crew_id}")
async def get_crew(crew_id: str, user: User = Depends(get_current_user)) -> dict:
    crew = _CREWS.get(crew_id)
    if not crew or not _owned_by(crew, user):
        raise HTTPException(status_code=404, detail=f"Crew not found: {crew_id}")
    return {"crew": _serialize(crew)}


@router.delete("/{crew_id}")
@limiter.limit("30/minute")
async def disband_crew(
    request: Request,
    crew_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    crew = _CREWS.get(crew_id)
    if not crew or not _owned_by(crew, user):
        raise HTTPException(status_code=404, detail=f"Crew not found: {crew_id}")
    _CREWS.pop(crew_id)
    await _audit(db, user, "crew.disbanded", crew_id, {"name": crew.name})
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
@limiter.limit("30/minute")
async def dispatch_task(
    request: Request,
    crew_id: str,
    req: DispatchTaskRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Fan a single instruction out to every crew member.

    Returns an array of per-role results. Runs in parallel unless the crew
    was spawned with ``execution_mode=sequential``.
    """
    crew = _CREWS.get(crew_id)
    if not crew or not _owned_by(crew, user):
        raise HTTPException(status_code=404, detail=f"Crew not found: {crew_id}")

    guard = scan_prompt_injection(req.instruction)
    if guard.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        raise HTTPException(
            status_code=400,
            detail="Dispatch blocked: instruction contains potentially unsafe content.",
        )

    instruction = _scrub_pii(req.instruction)

    crew.last_run_at = datetime.now(UTC).isoformat()
    crew.last_run_results = []

    if crew.execution_mode == "sequential":
        results = []
        for member in crew.members:
            ctx = req.per_role_context.get(member.role.name, "")
            results.append(await _run_one(member, instruction, ctx))
    else:
        coros = [
            _run_one(m, instruction, req.per_role_context.get(m.role.name, ""))
            for m in crew.members
        ]
        results = await asyncio.gather(*coros)
    crew.last_run_results = results

    succeeded = sum(1 for r in results if r.get("status") == "succeeded")
    await _audit(
        db,
        user,
        "crew.dispatched",
        crew_id,
        {"members": len(results), "succeeded": succeeded},
    )
    return {"crew_id": crew_id, "results": results}
