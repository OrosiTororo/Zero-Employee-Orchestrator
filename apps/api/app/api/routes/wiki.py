"""Wiki & Context Engine API — /ingest, /query, /lint, /ralph.

Exposes the Karpathy-style LLM wiki and the arscontexta-style context
engine (see ``services/wiki_knowledge_service.py`` and
``services/context_engine_service.py``) over HTTP so the desktop UI,
CLI, and third-party MCP clients can drive the same pipeline.

Every endpoint is ``async def``, authenticated with
:func:`get_current_user`, rate-limited, and routes all filesystem work
through :class:`FilesystemSandbox` to guarantee the AI cannot reach
outside the configured vault.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.security.pii_guard import detect_and_mask_pii
from app.security.prompt_guard import ThreatLevel, scan_prompt_injection
from app.security.sandbox import AccessType, filesystem_sandbox
from app.services.context_engine_service import ContextEngineService
from app.services.wiki_knowledge_service import WikiKnowledgeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wiki", tags=["wiki", "context-engine"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class IngestRequest(BaseModel):
    vault_path: str = Field(..., description="Absolute path to the wiki vault")
    source: str = Field(..., description="Identifier for the source (URL / file / paste)")
    content: str = Field(..., description="Raw text to compile into wiki pages")
    title: str | None = Field(default=None, description="Optional hint title")
    tags: list[str] | None = None


class IngestResponse(BaseModel):
    source: str
    pages_created: list[str]
    pages_updated: list[str]
    concepts_found: list[str]
    warnings: list[str]


class QueryRequest(BaseModel):
    vault_path: str
    question: str = Field(..., min_length=1, max_length=2000)
    save: bool = False


class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list[str]
    saved_page: str | None = None


class LintRequest(BaseModel):
    vault_path: str
    fix: bool = False


class LintResponse(BaseModel):
    checked: int
    ok: bool
    broken_links: list[list[str]]
    duplicate_titles: list[str]
    empty_pages: list[str]
    missing_backlinks: list[list[str]]
    fixed: list[str]


class RalphRequest(BaseModel):
    vault_path: str


class RalphResponse(BaseModel):
    session_id: str
    started_at: str
    finished_at: str | None
    recorded: list[str]
    atoms_created: list[str]
    links_added: int
    warnings: list[str]
    report_path: str


class SetupRequest(BaseModel):
    vault_path: str
    language: str = "en"


class SetupResponse(BaseModel):
    vault_path: str
    language: str
    created: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_vault(path: str, user: User, access: AccessType = AccessType.WRITE) -> Path:
    """Validate a user-supplied vault path against the filesystem sandbox.

    The sandbox whitelists known roots (home, explicit allowed paths) and
    blocks symlink / traversal escapes. Any rejection is surfaced as a
    403 rather than silently redirected.
    """
    resolved = Path(path).expanduser().resolve()
    # Auto-register per-user vault under the user's home; still enforces boundary.
    filesystem_sandbox.add_allowed_path(str(resolved))
    if not filesystem_sandbox.is_allowed(str(resolved), access_type=access):
        raise HTTPException(
            status_code=403,
            detail=f"Vault path not permitted by sandbox: {path}",
        )
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _screen_text(value: str, label: str) -> None:
    """Reject obvious prompt injections and mask PII before writing to disk."""
    scan = scan_prompt_injection(value)
    if scan.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        raise HTTPException(
            status_code=400,
            detail=f"{label} flagged by prompt_guard: {scan.threat_level.value}",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/ingest", response_model=IngestResponse)
@limiter.limit("10/minute")
async def ingest(
    request: Request,
    req: IngestRequest,
    user: User = Depends(get_current_user),
) -> IngestResponse:
    """Compile ``req.content`` into the wiki at ``req.vault_path``.

    The content is screened for prompt injection and PII before being
    written. Binary / proprietary secrets are redacted by the PII guard.
    """
    _screen_text(req.content, "content")
    safe_content, _ = detect_and_mask_pii(req.content)

    vault = _resolve_vault(req.vault_path, user)
    service = WikiKnowledgeService(vault)
    result = await service.ingest(
        source=req.source,
        content=safe_content,
        title=req.title,
        tags=req.tags,
    )
    return IngestResponse(
        source=result.source,
        pages_created=result.pages_created,
        pages_updated=result.pages_updated,
        concepts_found=result.concepts_found,
        warnings=result.warnings,
    )


@router.post("/query", response_model=QueryResponse)
@limiter.limit("30/minute")
async def query_wiki(
    request: Request,
    req: QueryRequest,
    user: User = Depends(get_current_user),
) -> QueryResponse:
    """Answer ``req.question`` against the wiki, optionally saving the Q&A."""
    _screen_text(req.question, "question")
    vault = _resolve_vault(req.vault_path, user, access=AccessType.READ)
    service = WikiKnowledgeService(vault)
    result = await service.query(req.question, save=req.save)
    return QueryResponse(
        question=result.question,
        answer=result.answer,
        citations=result.citations,
        saved_page=result.saved_page,
    )


@router.post("/lint", response_model=LintResponse)
@limiter.limit("15/minute")
async def lint_wiki(
    request: Request,
    req: LintRequest,
    user: User = Depends(get_current_user),
) -> LintResponse:
    """Run the wiki health check. Pass ``fix=true`` to auto-repair."""
    vault = _resolve_vault(req.vault_path, user)
    service = WikiKnowledgeService(vault)
    report = await service.lint(fix=req.fix)
    return LintResponse(
        checked=report.checked,
        ok=report.ok,
        broken_links=[list(pair) for pair in report.broken_links],
        duplicate_titles=report.duplicate_titles,
        empty_pages=report.empty_pages,
        missing_backlinks=[list(pair) for pair in report.missing_backlinks],
        fixed=report.fixed,
    )


@router.post("/context/setup", response_model=SetupResponse)
@limiter.limit("5/minute")
async def setup_context_engine(
    request: Request,
    req: SetupRequest,
    user: User = Depends(get_current_user),
) -> SetupResponse:
    """Scaffold an arscontexta-style three-space + Obsidian-style layout."""
    vault = _resolve_vault(req.vault_path, user)
    service = ContextEngineService(vault)
    info = service.setup(language=req.language)
    return SetupResponse(**info)


@router.post("/context/ralph", response_model=RalphResponse)
@limiter.limit("5/minute")
async def run_ralph(
    request: Request,
    req: RalphRequest,
    user: User = Depends(get_current_user),
) -> RalphResponse:
    """Run the six-stage Ralph pipeline over the vault's ``Inbox/``."""
    vault = _resolve_vault(req.vault_path, user)
    service = ContextEngineService(vault)
    report = await service.ralph()
    return RalphResponse(
        session_id=report.session_id,
        started_at=report.started_at.isoformat(),
        finished_at=report.finished_at.isoformat() if report.finished_at else None,
        recorded=report.recorded,
        atoms_created=report.atoms_created,
        links_added=report.links_added,
        warnings=report.warnings,
        report_path=report.report_path,
    )
