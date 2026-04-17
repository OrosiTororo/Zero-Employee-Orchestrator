"""Workflow template library — Dify-inspired reusable DAG patterns.

Users can save a plan as a template and instantiate it later against a new
ticket. Ships with a few built-in templates (research brief, weekly report,
customer-onboarding sequence) so a new install has something to run day-1.

User-saved templates are scoped per-user and kept in-memory for the duration
of the process; built-in templates are read-only and global. Mutations are
rate-limited and written to the audit log when the caller belongs to a
company.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict, dataclass, field

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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow-templates", tags=["workflow-templates"])


@dataclass
class TemplateNode:
    id: str
    title: str
    depends_on: list[str] = field(default_factory=list)
    role: str = "analyst"
    verification: str = ""


@dataclass
class WorkflowTemplate:
    slug: str
    name: str
    description: str
    category: str
    nodes: list[TemplateNode]
    tags: list[str] = field(default_factory=list)


_BUILTIN_TEMPLATES: dict[str, WorkflowTemplate] = {
    "research-brief": WorkflowTemplate(
        slug="research-brief",
        name="Research Brief",
        description="3-step research pipeline: gather sources → synthesize → verify citations.",
        category="research",
        nodes=[
            TemplateNode(id="n1", title="Gather primary sources", role="researcher"),
            TemplateNode(
                id="n2",
                title="Synthesize findings",
                depends_on=["n1"],
                role="analyst",
                verification="Each claim has a citation",
            ),
            TemplateNode(
                id="n3",
                title="Fact-check and verify citations",
                depends_on=["n2"],
                role="judge",
                verification="No uncited claims remain",
            ),
        ],
        tags=["research", "writing"],
    ),
    "weekly-report": WorkflowTemplate(
        slug="weekly-report",
        name="Weekly Report",
        description="Collect metrics → draft narrative → polish → share.",
        category="reporting",
        nodes=[
            TemplateNode(id="n1", title="Collect metrics from all sources", role="analyst"),
            TemplateNode(
                id="n2", title="Draft narrative summary", depends_on=["n1"], role="writer"
            ),
            TemplateNode(
                id="n3", title="Polish for executive tone", depends_on=["n2"], role="editor"
            ),
            TemplateNode(
                id="n4", title="Post to Slack and email", depends_on=["n3"], role="dispatcher"
            ),
        ],
        tags=["reporting", "weekly"],
    ),
    "customer-onboarding": WorkflowTemplate(
        slug="customer-onboarding",
        name="Customer Onboarding",
        description="Welcome email → provision account → schedule kickoff call.",
        category="customer-success",
        nodes=[
            TemplateNode(id="n1", title="Send welcome email", role="comms"),
            TemplateNode(id="n2", title="Provision workspace and API keys", role="ops"),
            TemplateNode(
                id="n3",
                title="Schedule kickoff call on calendar",
                depends_on=["n1", "n2"],
                role="scheduler",
            ),
        ],
        tags=["customer-success", "onboarding"],
    ),
    "incident-response": WorkflowTemplate(
        slug="incident-response",
        name="Incident Response",
        description="Detect → triage → mitigate → post-mortem draft.",
        category="sre",
        nodes=[
            TemplateNode(id="n1", title="Classify severity and scope", role="sre"),
            TemplateNode(
                id="n2", title="Apply short-term mitigation", depends_on=["n1"], role="sre"
            ),
            TemplateNode(
                id="n3",
                title="Draft post-mortem with timeline",
                depends_on=["n2"],
                role="writer",
                verification="Root cause and contributing factors are both named",
            ),
        ],
        tags=["sre", "incident"],
    ),
    "content-repurpose": WorkflowTemplate(
        slug="content-repurpose",
        name="Content Repurposing",
        description="One long-form article → 5 social posts + 1 newsletter.",
        category="marketing",
        nodes=[
            TemplateNode(id="n1", title="Extract 5 key takeaways", role="editor"),
            TemplateNode(id="n2", title="Draft 5 social posts", depends_on=["n1"], role="writer"),
            TemplateNode(
                id="n3", title="Compose newsletter version", depends_on=["n1"], role="writer"
            ),
        ],
        tags=["marketing", "content"],
    ),
}

# User-scoped: outer key = str(user.id), inner key = slug. This keeps one
# user's templates invisible to another user even when the same process
# serves both.
_USER_TEMPLATES: dict[str, dict[str, WorkflowTemplate]] = {}


class SaveTemplateRequest(BaseModel):
    slug: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    category: str = "custom"
    nodes: list[dict] = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)


class InstantiateRequest(BaseModel):
    ticket_title: str = Field(..., min_length=1, max_length=200)
    variables: dict[str, str] = Field(default_factory=dict)


def _serialize(tpl: WorkflowTemplate) -> dict:
    out = asdict(tpl)
    out["builtin"] = tpl.slug in _BUILTIN_TEMPLATES
    return out


def _user_templates(user: User) -> dict[str, WorkflowTemplate]:
    return _USER_TEMPLATES.setdefault(str(user.id), {})


async def _resolve_company_id(db: AsyncSession, user: User) -> uuid.UUID | None:
    """Best-effort lookup of the user's first company for audit purposes.

    Returns None for users without a company membership (e.g. stub users in
    tests, freshly registered accounts before org setup). Callers should
    skip the audit write in that case rather than fail.
    """
    result = await db.execute(
        select(CompanyMember.company_id).where(CompanyMember.user_id == user.id).limit(1)
    )
    return result.scalar_one_or_none()


@router.get("")
async def list_templates(
    category: str | None = None,
    user: User = Depends(get_current_user),
) -> dict:
    """List every available workflow template (built-in + user-saved)."""
    user_map = _user_templates(user)
    all_templates = {**_BUILTIN_TEMPLATES, **user_map}
    items = [_serialize(t) for t in all_templates.values()]
    if category:
        items = [t for t in items if t["category"] == category]
    return {"templates": items, "total": len(items)}


@router.get("/{slug}")
async def get_template(slug: str, user: User = Depends(get_current_user)) -> dict:
    tpl = _user_templates(user).get(slug) or _BUILTIN_TEMPLATES.get(slug)
    if tpl is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Template not found: {slug}. "
                "List available templates via GET /workflow-templates."
            ),
        )
    return _serialize(tpl)


@router.post("")
@limiter.limit("30/minute")
async def save_template(
    request: Request,
    req: SaveTemplateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Save a new workflow template. Built-in slugs cannot be overwritten."""
    if req.slug in _BUILTIN_TEMPLATES:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Slug '{req.slug}' is reserved for a built-in template. "
                "Pick a different slug or DELETE the user template first."
            ),
        )
    nodes = [TemplateNode(**n) for n in req.nodes]
    tpl = WorkflowTemplate(
        slug=req.slug,
        name=req.name,
        description=req.description,
        category=req.category,
        nodes=nodes,
        tags=req.tags,
    )
    _user_templates(user)[req.slug] = tpl

    company_id = await _resolve_company_id(db, user)
    if company_id is not None:
        db.add(
            AuditLog(
                id=generate_uuid(),
                company_id=company_id,
                actor_type="user",
                actor_user_id=user.id,
                event_type="template.saved",
                target_type="workflow_template",
                details_json={"slug": req.slug, "name": req.name},
            )
        )
        await db.commit()
    return {"saved": True, "template": _serialize(tpl)}


@router.delete("/{slug}")
@limiter.limit("30/minute")
async def delete_template(
    request: Request,
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    if slug in _BUILTIN_TEMPLATES:
        raise HTTPException(status_code=403, detail="Cannot delete a built-in template.")
    user_map = _user_templates(user)
    if slug not in user_map:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Template not found: {slug}. "
                "List available templates via GET /workflow-templates."
            ),
        )
    user_map.pop(slug)

    company_id = await _resolve_company_id(db, user)
    if company_id is not None:
        db.add(
            AuditLog(
                id=generate_uuid(),
                company_id=company_id,
                actor_type="user",
                actor_user_id=user.id,
                event_type="template.deleted",
                target_type="workflow_template",
                details_json={"slug": slug},
            )
        )
        await db.commit()
    return {"deleted": slug}


@router.post("/{slug}/instantiate")
async def instantiate_template(
    slug: str,
    req: InstantiateRequest,
    user: User = Depends(get_current_user),
) -> dict:
    """Materialise a template into a concrete plan draft.

    Returns a plan shape compatible with the DAG builder. This does NOT write
    to the database — the caller decides whether to persist it as a plan.
    Variables in node titles are substituted via simple ``{var}`` templating.
    """
    tpl = _user_templates(user).get(slug) or _BUILTIN_TEMPLATES.get(slug)
    if tpl is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Template not found: {slug}. "
                "List available templates via GET /workflow-templates."
            ),
        )
    plan_id = str(uuid.uuid4())
    nodes = []
    for n in tpl.nodes:
        title = n.title
        for key, val in req.variables.items():
            title = title.replace("{" + key + "}", val)
        nodes.append(
            {
                "id": n.id,
                "title": title,
                "depends_on": list(n.depends_on),
                "role": n.role,
                "verification_criteria": n.verification,
            }
        )
    return {
        "plan_id": plan_id,
        "ticket_title": req.ticket_title,
        "template_slug": slug,
        "nodes": nodes,
        "ready_to_execute": True,
    }
