"""Workflow template library — Dify-inspired reusable DAG patterns.

Users can save a plan as a template and instantiate it later against a new
ticket. Ships with a few built-in templates (research brief, weekly report,
customer-onboarding sequence) so a new install has something to run day-1.

All templates are pure-Python dataclasses; there is no database table yet —
intentionally lightweight so the library ships with the product and can be
extended by plugin packs later.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict, dataclass, field

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.models.user import User

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

_USER_TEMPLATES: dict[str, WorkflowTemplate] = {}


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


@router.get("")
async def list_templates(
    category: str | None = None,
    _: User = Depends(get_current_user),
) -> dict:
    """List every available workflow template (built-in + user-saved)."""
    all_templates = {**_BUILTIN_TEMPLATES, **_USER_TEMPLATES}
    items = [_serialize(t) for t in all_templates.values()]
    if category:
        items = [t for t in items if t["category"] == category]
    return {"templates": items, "total": len(items)}


@router.get("/{slug}")
async def get_template(slug: str, _: User = Depends(get_current_user)) -> dict:
    tpl = _USER_TEMPLATES.get(slug) or _BUILTIN_TEMPLATES.get(slug)
    if tpl is None:
        raise HTTPException(status_code=404, detail=f"Template not found: {slug}")
    return _serialize(tpl)


@router.post("")
async def save_template(
    request: SaveTemplateRequest,
    _: User = Depends(get_current_user),
) -> dict:
    """Save a new workflow template. Built-in slugs cannot be overwritten."""
    if request.slug in _BUILTIN_TEMPLATES:
        raise HTTPException(
            status_code=409,
            detail=f"Slug '{request.slug}' is reserved for a built-in template.",
        )
    nodes = [TemplateNode(**n) for n in request.nodes]
    tpl = WorkflowTemplate(
        slug=request.slug,
        name=request.name,
        description=request.description,
        category=request.category,
        nodes=nodes,
        tags=request.tags,
    )
    _USER_TEMPLATES[request.slug] = tpl
    return {"saved": True, "template": _serialize(tpl)}


@router.delete("/{slug}")
async def delete_template(slug: str, _: User = Depends(get_current_user)) -> dict:
    if slug in _BUILTIN_TEMPLATES:
        raise HTTPException(status_code=403, detail="Cannot delete a built-in template.")
    if slug not in _USER_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template not found: {slug}")
    _USER_TEMPLATES.pop(slug)
    return {"deleted": slug}


@router.post("/{slug}/instantiate")
async def instantiate_template(
    slug: str,
    request: InstantiateRequest,
    _: User = Depends(get_current_user),
) -> dict:
    """Materialise a template into a concrete plan draft.

    Returns a plan shape compatible with the DAG builder. This does NOT write
    to the database — the caller decides whether to persist it as a plan.
    Variables in node titles are substituted via simple ``{var}`` templating.
    """
    tpl = _USER_TEMPLATES.get(slug) or _BUILTIN_TEMPLATES.get(slug)
    if tpl is None:
        raise HTTPException(status_code=404, detail=f"Template not found: {slug}")
    plan_id = str(uuid.uuid4())
    nodes = []
    for n in tpl.nodes:
        title = n.title
        for key, val in request.variables.items():
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
        "ticket_title": request.ticket_title,
        "template_slug": slug,
        "nodes": nodes,
        "ready_to_execute": True,
    }
