"""Platform API — MCP, external skills, Sentry, IAM, hypothesis testing, session management.

API endpoints for cross-platform features added in v0.1.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.models.user import User

router = APIRouter()


# ===================================================================
# Shared response models
# ===================================================================


class StatusResponse(BaseModel):
    """Generic status response used across multiple endpoints."""

    success: bool = True
    message: str = ""


class MCPCapabilitiesResponse(BaseModel):
    tools: list[dict] = []
    resources: list[dict] = []
    prompts: list[dict] = []


class MCPToolCallResponse(BaseModel):
    result: dict | list | str | None = None


class ExternalSkillSearchResult(BaseModel):
    name: str
    slug: str
    description: str = ""
    source_type: str
    source_uri: str = ""
    author: str = ""
    stars: int = 0
    downloads: int = 0


class ExternalSkillSearchResponse(BaseModel):
    results: list[ExternalSkillSearchResult]
    total: int


class SkillImportResponse(BaseModel):
    installed: bool
    skill_id: str
    name: str
    slug: str
    source: str


class SentryEventsResponse(BaseModel):
    events: list[dict]
    total: int


class SentryCaptureResponse(BaseModel):
    event_id: str
    captured: bool


class IAMAccountResponse(BaseModel):
    account_id: str
    agent_id: str
    account_name: str
    token: str = ""
    permissions: list[str] = []


class IAMAccountListResponse(BaseModel):
    accounts: list[dict]


class InvestigationHistoryResponse(BaseModel):
    history: list[dict]


class HypothesisListResponse(BaseModel):
    hypotheses: list[dict]


class EvidenceResponse(BaseModel):
    evidence_id: str
    added: bool


class ReviewResponse(BaseModel):
    review_id: str
    submitted: bool


class ResolveResponse(BaseModel):
    resolved: bool
    confirmed: bool


class SessionListResponse(BaseModel):
    sessions: list[dict]


class SessionMessageResponse(BaseModel):
    added: bool
    message_count: int


class WorkingMemoryResponse(BaseModel):
    stored: bool
    key: str


class MCPToolListResponse(BaseModel):
    """Response for listing MCP tools."""

    tools: list[dict] = []


class MCPResourceListResponse(BaseModel):
    """Response for listing MCP resources."""

    resources: list[dict] = []


class MCPPromptListResponse(BaseModel):
    """Response for listing MCP prompts."""

    prompts: list[dict] = []


class SentryStatsResponse(BaseModel):
    """Response for Sentry error statistics."""

    total_events: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    events_by_type: dict = {}
    recent_errors: list[dict] = []


class RevokeAccountResponse(BaseModel):
    """Response for revoking an AI service account."""

    revoked: bool = True


class InvestigationResultResponse(BaseModel):
    """Response for AI investigation query/audit/error results."""

    success: bool = True
    query: str = ""
    rows: list[dict] = []
    row_count: int = 0
    error: str | None = None
    duration_ms: float = 0


class InvestigationMetricsResponse(BaseModel):
    """Response for system metrics from AI investigator."""

    uptime_seconds: float = 0
    total_requests: int = 0
    error_rate: float = 0
    avg_response_ms: float = 0
    active_sessions: int = 0
    memory_usage_mb: float = 0
    db_pool_size: int = 0
    db_pool_available: int = 0


class HypothesisDetailResponse(BaseModel):
    """Response for a single hypothesis."""

    id: str
    title: str
    description: str
    status: str = ""
    proposer_agent_id: str = ""
    task_id: str | None = None
    company_id: str | None = None
    priority: int = 0
    evidence: list[dict] = []
    reviews: list[dict] = []
    created_at: str = ""
    updated_at: str = ""


class SessionDetailResponse(BaseModel):
    """Response for a single session."""

    session_id: str
    agent_id: str
    role: str = ""
    status: str = ""
    company_id: str | None = None
    task_id: str | None = None
    message_count: int = 0
    created_at: str = ""
    last_active_at: str = ""
    working_memory: dict = {}


class SessionIdleResponse(BaseModel):
    """Response for setting a session to idle."""

    status: str = "idle"
    session_id: str


class SessionContextSummaryResponse(BaseModel):
    """Response for resuming a session (context summary)."""

    session_id: str = ""
    agent_id: str = ""
    role: str = ""
    status: str = ""
    message_count: int = 0
    working_memory_keys: list[str] = []
    last_messages: list[dict] = []


class TerminateSessionResponse(BaseModel):
    """Response for terminating a session."""

    terminated: bool = True


# ===================================================================
# MCP endpoints
# ===================================================================


class MCPToolCallRequest(BaseModel):
    name: str
    arguments: dict = {}


@router.get("/mcp/capabilities", response_model=MCPCapabilitiesResponse)
async def mcp_capabilities(user: User = Depends(get_current_user)):
    """Get MCP server capabilities."""
    from app.integrations.mcp_server import mcp_server

    return mcp_server.get_capabilities()


@router.get("/mcp/tools", response_model=MCPToolListResponse)
async def mcp_list_tools(user: User = Depends(get_current_user)):
    """List MCP tools."""
    from app.integrations.mcp_server import mcp_server

    return await mcp_server.handle_list_tools()


@router.post("/mcp/tools/call", response_model=MCPToolCallResponse)
async def mcp_call_tool(req: MCPToolCallRequest, user: User = Depends(get_current_user)):
    """Execute MCP tool."""
    from app.integrations.mcp_server import mcp_server

    return await mcp_server.handle_call_tool(req.name, req.arguments)


@router.get("/mcp/resources", response_model=MCPResourceListResponse)
async def mcp_list_resources(user: User = Depends(get_current_user)):
    """List MCP resources."""
    from app.integrations.mcp_server import mcp_server

    return await mcp_server.handle_list_resources()


@router.get("/mcp/prompts", response_model=MCPPromptListResponse)
async def mcp_list_prompts(user: User = Depends(get_current_user)):
    """List MCP prompts."""
    from app.integrations.mcp_server import mcp_server

    return await mcp_server.handle_list_prompts()


# ===================================================================
# External skill import endpoints
# ===================================================================


class SkillSearchRequest(BaseModel):
    query: str
    source_type: str | None = None
    limit: int = 20


class SkillImportRequest(BaseModel):
    source_type: str  # github_agent_skills, skills_sh, openclaw, claude_code, git_repo, url
    source_uri: str


@router.post("/skills/external/search", response_model=ExternalSkillSearchResponse)
async def search_external_skills(req: SkillSearchRequest, user: User = Depends(get_current_user)):
    """Search for skills from external sources."""
    from app.integrations.external_skills import SkillSourceType, skill_importer

    source = SkillSourceType(req.source_type) if req.source_type else None
    results = await skill_importer.search_skills(req.query, source, req.limit)
    return {
        "results": [
            {
                "name": r.name,
                "slug": r.slug,
                "description": r.description,
                "source_type": r.source_type,
                "source_uri": r.source_uri,
                "author": r.author,
                "stars": r.stars,
                "downloads": r.downloads,
            }
            for r in results
        ],
        "total": len(results),
    }


@router.post("/skills/external/import", response_model=SkillImportResponse)
async def import_external_skill(
    req: SkillImportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import and install a skill from an external source."""
    from app.integrations.external_skills import SkillSourceType, skill_importer
    from app.schemas.registry import SkillCreate
    from app.services import skill_service

    source_type = SkillSourceType(req.source_type)
    manifest = await skill_importer.fetch_skill_manifest(source_type, req.source_uri)
    if not manifest:
        raise HTTPException(status_code=404, detail="Unable to retrieve skill manifest")

    data = skill_importer.to_skill_create_data(manifest)

    # Check for existing
    existing = await skill_service.get_skill_by_slug(db, data["slug"])
    if existing:
        raise HTTPException(status_code=409, detail=f"Skill '{data['slug']}' already exists")

    skill = await skill_service.create_skill(db, SkillCreate(**data))
    await db.commit()

    return {
        "installed": True,
        "skill_id": str(skill.id),
        "name": skill.name,
        "slug": skill.slug,
        "source": req.source_type,
    }


# ===================================================================
# Sentry integration endpoints
# ===================================================================


@router.get("/sentry/stats", response_model=SentryStatsResponse)
async def sentry_stats(user: User = Depends(get_current_user)):
    """Sentry error statistics."""
    from app.integrations.sentry_integration import sentry

    return sentry.get_error_stats()


@router.get("/sentry/events", response_model=SentryEventsResponse)
async def sentry_events(
    level: str | None = None,
    event_type: str | None = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
):
    """List Sentry events."""
    from app.integrations.sentry_integration import EventType, SeverityLevel, sentry

    lvl = SeverityLevel(level) if level else None
    et = EventType(event_type) if event_type else None
    events = sentry.get_recent_events(lvl, et, limit)
    return {
        "events": [e.to_dict() for e in events],
        "total": len(events),
    }


@router.post("/sentry/capture", response_model=SentryCaptureResponse)
async def sentry_capture_message(
    message: str = "",
    level: str = "info",
    tags: dict | None = None,
    user: User = Depends(get_current_user),
):
    """Capture a custom event."""
    from app.integrations.sentry_integration import SeverityLevel, sentry

    event_id = sentry.capture_message(message, SeverityLevel(level), tags=tags)
    return {"event_id": event_id, "captured": True}


# ===================================================================
# IAM endpoints
# ===================================================================


class CreateAIAccountRequest(BaseModel):
    agent_id: str
    account_name: str
    company_id: str | None = None
    custom_permissions: list[str] | None = None


@router.post("/iam/ai-accounts", response_model=IAMAccountResponse)
async def create_ai_account(
    req: CreateAIAccountRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a service account for an AI agent."""
    from app.security.iam import iam_manager

    account, token = await iam_manager.create_ai_account(
        db,
        req.agent_id,
        req.account_name,
        company_id=req.company_id,
        custom_permissions=req.custom_permissions,
    )
    await db.commit()
    return {
        "account_id": str(account.id),
        "agent_id": account.agent_id,
        "account_name": account.account_name,
        "token": token,  # Displayed only once
        "permissions": account.permissions,
    }


@router.get("/iam/ai-accounts", response_model=IAMAccountListResponse)
async def list_ai_accounts(
    company_id: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List AI service accounts."""
    from app.security.iam import iam_manager

    accounts = await iam_manager.list_ai_accounts(db, company_id)
    return {
        "accounts": [
            {
                "id": str(a.id),
                "agent_id": a.agent_id,
                "account_name": a.account_name,
                "account_type": a.account_type,
                "permissions": a.permissions,
                "is_active": a.is_active,
                "last_used_at": str(a.last_used_at) if a.last_used_at else None,
            }
            for a in accounts
        ],
    }


@router.delete("/iam/ai-accounts/{account_id}", response_model=RevokeAccountResponse)
async def revoke_ai_account(
    account_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an AI service account."""
    from app.security.iam import iam_manager

    ok = await iam_manager.revoke_ai_account(db, account_id)
    await db.commit()
    if not ok:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"revoked": True}


# ===================================================================
# AI Investigator endpoints
# ===================================================================


class DBQueryRequest(BaseModel):
    query: str = Field(..., description="Only SELECT statements can be executed")
    params: dict | None = None


class AuditSearchRequest(BaseModel):
    action_type: str | None = None
    entity_type: str | None = None
    actor_id: str | None = None
    since_hours: int = 24
    limit: int = 100


@router.post("/investigate/query", response_model=InvestigationResultResponse)
async def investigate_query(
    req: DBQueryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI investigation: safe DB read query."""
    from app.integrations.ai_investigator import ai_investigator

    result = await ai_investigator.query_db(db, req.query, req.params)
    return result.to_dict()


@router.post("/investigate/audit", response_model=InvestigationResultResponse)
async def investigate_audit(
    req: AuditSearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI investigation: audit log search."""
    from app.integrations.ai_investigator import ai_investigator

    result = await ai_investigator.search_audit_logs(
        db,
        action_type=req.action_type,
        entity_type=req.entity_type,
        actor_id=req.actor_id,
        since_hours=req.since_hours,
        limit=req.limit,
    )
    return result.to_dict()


@router.get("/investigate/errors", response_model=InvestigationResultResponse)
async def investigate_errors(
    since_hours: int = 24,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI investigation: error pattern analysis."""
    from app.integrations.ai_investigator import ai_investigator

    result = await ai_investigator.analyze_errors(db, since_hours, limit)
    return result.to_dict()


@router.get("/investigate/metrics", response_model=InvestigationMetricsResponse)
async def investigate_metrics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI investigation: system metrics."""
    from app.integrations.ai_investigator import ai_investigator

    return await ai_investigator.get_system_metrics(db)


@router.get("/investigate/history", response_model=InvestigationHistoryResponse)
async def investigate_history(limit: int = 50, user: User = Depends(get_current_user)):
    """AI investigation: investigation history."""
    from app.integrations.ai_investigator import ai_investigator

    return {"history": ai_investigator.get_investigation_history(limit)}


# ===================================================================
# Hypothesis testing endpoints
# ===================================================================


class HypothesisRequest(BaseModel):
    title: str
    description: str
    proposer_agent_id: str
    task_id: str | None = None
    company_id: str | None = None
    priority: int = 0


class EvidenceRequest(BaseModel):
    hypothesis_id: str
    agent_id: str
    supports: bool
    description: str
    source: str = ""
    confidence: float = 0.5
    data: dict | None = None


class ReviewRequest(BaseModel):
    hypothesis_id: str
    reviewer_agent_id: str
    verdict: str  # agree, disagree, needs_more_evidence, partially_agree
    reasoning: str
    confidence: float = 0.5
    suggested_actions: list[str] = []


@router.post("/hypotheses", response_model=HypothesisDetailResponse)
async def propose_hypothesis(req: HypothesisRequest, user: User = Depends(get_current_user)):
    """Propose a hypothesis."""
    from app.orchestration.hypothesis_engine import hypothesis_engine

    h = hypothesis_engine.propose(
        req.title,
        req.description,
        req.proposer_agent_id,
        task_id=req.task_id,
        company_id=req.company_id,
        priority=req.priority,
    )
    return h.to_dict()


@router.get("/hypotheses", response_model=HypothesisListResponse)
async def list_hypotheses(
    company_id: str | None = None,
    task_id: str | None = None,
    user: User = Depends(get_current_user),
):
    """List hypotheses."""
    from app.orchestration.hypothesis_engine import hypothesis_engine

    if task_id:
        hypotheses = hypothesis_engine.get_by_task(task_id)
    else:
        hypotheses = hypothesis_engine.get_active(company_id)
    return {"hypotheses": [h.to_dict() for h in hypotheses]}


@router.get("/hypotheses/{hypothesis_id}", response_model=HypothesisDetailResponse)
async def get_hypothesis(hypothesis_id: str, user: User = Depends(get_current_user)):
    """Get hypothesis details."""
    from app.orchestration.hypothesis_engine import hypothesis_engine

    h = hypothesis_engine.get(hypothesis_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return h.to_dict()


@router.post("/hypotheses/evidence", response_model=EvidenceResponse)
async def add_evidence(req: EvidenceRequest, user: User = Depends(get_current_user)):
    """Add evidence."""
    from app.orchestration.hypothesis_engine import hypothesis_engine

    ev = hypothesis_engine.add_evidence(
        req.hypothesis_id,
        req.agent_id,
        req.supports,
        req.description,
        source=req.source,
        confidence=req.confidence,
        data=req.data,
    )
    if not ev:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return {"evidence_id": ev.evidence_id, "added": True}


@router.post("/hypotheses/review", response_model=ReviewResponse)
async def submit_review(req: ReviewRequest, user: User = Depends(get_current_user)):
    """Submit a review."""
    from app.orchestration.hypothesis_engine import ReviewVerdict, hypothesis_engine

    review = hypothesis_engine.submit_review(
        req.hypothesis_id,
        req.reviewer_agent_id,
        ReviewVerdict(req.verdict),
        req.reasoning,
        confidence=req.confidence,
        suggested_actions=req.suggested_actions,
    )
    if not review:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return {"review_id": review.review_id, "submitted": True}


@router.post("/hypotheses/{hypothesis_id}/resolve", response_model=ResolveResponse)
async def resolve_hypothesis(
    hypothesis_id: str, confirmed: bool = True, user: User = Depends(get_current_user)
):
    """Resolve a hypothesis."""
    from app.orchestration.hypothesis_engine import hypothesis_engine

    ok = hypothesis_engine.resolve(hypothesis_id, confirmed)
    if not ok:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return {"resolved": True, "confirmed": confirmed}


@router.get("/hypotheses/needing-review", response_model=HypothesisListResponse)
async def hypotheses_needing_review(
    company_id: str | None = None, user: User = Depends(get_current_user)
):
    """List hypotheses needing review."""
    from app.orchestration.hypothesis_engine import hypothesis_engine

    hypotheses = hypothesis_engine.get_needing_review(company_id)
    return {"hypotheses": [h.to_dict() for h in hypotheses]}


# ===================================================================
# Agent session endpoints
# ===================================================================


class CreateSessionRequest(BaseModel):
    agent_id: str
    role: str = "general"
    company_id: str | None = None
    task_id: str | None = None
    initial_context: dict | None = None
    ttl: float = 86400


class SessionMessageRequest(BaseModel):
    session_id: str
    role: str
    content: str
    metadata: dict | None = None


class WorkingMemoryRequest(BaseModel):
    session_id: str
    key: str
    value: dict | str | list | int | float | bool | None


@router.post("/sessions", response_model=SessionDetailResponse)
async def create_session(req: CreateSessionRequest, user: User = Depends(get_current_user)):
    """Create an agent session."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.create_session(
        req.agent_id,
        req.role,
        company_id=req.company_id,
        task_id=req.task_id,
        initial_context=req.initial_context,
        ttl=req.ttl,
    )
    return session.to_dict()


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    company_id: str | None = None,
    status: str | None = None,
    agent_id: str | None = None,
    user: User = Depends(get_current_user),
):
    """List sessions."""
    from app.orchestration.agent_session import SessionStatus, session_manager

    st = SessionStatus(status) if status else None
    sessions = session_manager.list_sessions(company_id, st, agent_id)
    return {"sessions": [s.to_dict() for s in sessions]}


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str, user: User = Depends(get_current_user)):
    """Get session details."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@router.get("/sessions/agent/{agent_id}", response_model=SessionDetailResponse)
async def get_agent_session(agent_id: str, user: User = Depends(get_current_user)):
    """Get active session for an agent."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_active_session(agent_id)
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")
    return session.to_dict()


@router.post("/sessions/agent/{agent_id}/get-or-create", response_model=SessionDetailResponse)
async def get_or_create_session(
    agent_id: str, req: CreateSessionRequest, user: User = Depends(get_current_user)
):
    """Get session or create if not found."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_or_create_session(
        agent_id,
        req.role,
        company_id=req.company_id,
        task_id=req.task_id,
        initial_context=req.initial_context,
        ttl=req.ttl,
    )
    return session.to_dict()


@router.post("/sessions/message", response_model=SessionMessageResponse)
async def add_session_message(req: SessionMessageRequest, user: User = Depends(get_current_user)):
    """Add a message to a session."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.add_message(req.role, req.content, req.metadata)
    return {"added": True, "message_count": session.message_count}


@router.post("/sessions/memory", response_model=WorkingMemoryResponse)
async def add_working_memory(req: WorkingMemoryRequest, user: User = Depends(get_current_user)):
    """Add information to working memory."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.add_to_working_memory(req.key, req.value)
    return {"stored": True, "key": req.key}


@router.post("/sessions/{session_id}/idle", response_model=SessionIdleResponse)
async def set_session_idle(session_id: str, user: User = Depends(get_current_user)):
    """Set session to idle state."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.go_idle()
    return {"status": "idle", "session_id": session_id}


@router.post("/sessions/{session_id}/resume", response_model=SessionContextSummaryResponse)
async def resume_session(session_id: str, user: User = Depends(get_current_user)):
    """Resume a session."""
    from app.orchestration.agent_session import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.resume()
    return session.get_context_summary()


@router.delete("/sessions/{session_id}", response_model=TerminateSessionResponse)
async def terminate_session(session_id: str, user: User = Depends(get_current_user)):
    """Terminate a session."""
    from app.orchestration.agent_session import session_manager

    ok = session_manager.terminate_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"terminated": True}
