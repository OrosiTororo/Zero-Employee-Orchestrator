"""Multi-model comparison, brainstorming, conversation memory, and agent organization API.

Provides same-input comparison across multiple LLM models, brainstorming sessions,
conversation memory, per-role model configuration for agents, and dynamic organization management.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.security.pii_guard import detect_and_mask_pii
from app.security.prompt_guard import ThreatLevel, scan_prompt_injection

logger = logging.getLogger(__name__)

router = APIRouter()


# ===================================================================
# Schemas
# ===================================================================


class MultiModelCompareRequest(BaseModel):
    """Multi-model comparison request."""

    input_text: str
    model_ids: list[str] = Field(min_length=1)
    session_id: str | None = None
    metadata: dict | None = None


class MultiModelCompareResponse(BaseModel):
    id: str
    input_text: str
    input_char_count: int
    models_requested: list[str]
    responses: dict | None = None
    status: str
    created_at: str


class ModelResponseRecord(BaseModel):
    """Individual model response record."""

    model_id: str
    response_text: str
    latency_ms: int = 0
    tokens_used: int = 0
    error: str | None = None


class BrainstormCreateRequest(BaseModel):
    """Create brainstorming session."""

    title: str = ""
    topic: str | None = None
    session_type: str = "brainstorm"
    model_ids: list[str] | None = None
    is_multi_model: bool = False


class BrainstormMessageRequest(BaseModel):
    """Add brainstorming message."""

    role: str = "user"
    content: str
    model_id: str | None = None
    metadata: dict | None = None


class BrainstormSessionResponse(BaseModel):
    id: str
    title: str
    topic: str | None = None
    session_type: str
    model_ids: list[str] | None = None
    status: str
    message_count: int
    total_chars: int
    is_multi_model: bool
    created_at: str


class ConversationStoreRequest(BaseModel):
    """Store conversation message."""

    role: str
    content: str
    agent_id: str | None = None
    session_ref: str | None = None
    content_type: str = "text"
    metadata: dict | None = None


class ConversationMemoryResponse(BaseModel):
    id: str
    role: str
    content: str
    char_count: int
    content_type: str
    agent_id: str | None = None
    session_ref: str | None = None
    created_at: str


class TextAnalysisRequest(BaseModel):
    """Text analysis request."""

    text: str
    min_chars: int | None = None
    max_chars: int | None = None


class RoleModelConfigRequest(BaseModel):
    """Per-role model configuration."""

    role_name: str
    model_id: str
    agent_id: str | None = None
    fallback_model_id: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    system_prompt: str | None = None


class RoleModelConfigResponse(BaseModel):
    id: str
    role_name: str
    model_id: str
    fallback_model_id: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    is_active: bool
    created_at: str


class AgentAddByRoleRequest(BaseModel):
    """Add agent by role."""

    role: str
    name: str | None = None
    description: str | None = None
    model_name: str | None = None
    provider_name: str = "openrouter"
    team_id: str | None = None
    custom_system_prompt: str | None = None


class AgentRemoveRequest(BaseModel):
    """Remove agent."""

    reason: str = ""


class AgentUpdateRoleRequest(BaseModel):
    """Update agent role."""

    name: str | None = None
    title: str | None = None
    description: str | None = None
    model_name: str | None = None
    provider_name: str | None = None
    autonomy_level: str | None = None
    system_prompt: str | None = None


class CustomRoleCreateRequest(BaseModel):
    """Create custom role."""

    role_key: str
    name: str
    title: str
    description: str
    system_prompt: str | None = None
    autonomy_level: str = "supervised"
    can_delegate: bool = False


class NaturalLanguageRequest(BaseModel):
    """Natural language request."""

    request_text: str
    auto_execute: bool = False


class ModelResponseUpdateResponse(BaseModel):
    id: str
    status: str
    responses: dict | None = None


class ComparisonSummaryResponse(BaseModel):
    id: str
    input_text: str
    input_char_count: int
    models_requested: list[str]
    status: str
    created_at: str


class BrainstormMessageAddedResponse(BaseModel):
    session_id: str
    message_count: int
    total_chars: int
    latest_messages: list[dict]


class BrainstormSessionDetailResponse(BaseModel):
    id: str
    title: str
    topic: str | None = None
    session_type: str
    model_ids: list[str] | None = None
    conversation_history: dict | None = None
    insights: dict | None = None
    status: str
    message_count: int
    total_chars: int
    is_multi_model: bool
    created_at: str


class BrainstormStatusResponse(BaseModel):
    session_id: str
    status: str


class BrainstormSearchResultResponse(BaseModel):
    id: str
    title: str
    topic: str | None = None
    status: str
    message_count: int


class ConversationMemorySearchResponse(BaseModel):
    id: str
    role: str
    content: str
    char_count: int
    content_type: str
    created_at: str


class ConversationStatsResponse(BaseModel):
    total_messages: int
    total_characters: int
    by_role: dict[str, int]
    by_content_type: dict[str, int]


class CharacterAnalysis(BaseModel):
    total: int
    total_excluding_spaces: int
    hiragana: int
    katakana: int
    kanji: int
    ascii: int
    digits: int
    spaces: int
    newlines: int
    other: int
    words_estimate: int


class LengthValidation(BaseModel):
    length: int
    min_required: int
    max_allowed: int | None = None
    is_valid: bool
    over_by: int
    under_by: int


class TextAnalysisResponse(BaseModel):
    analysis: CharacterAnalysis
    validation: LengthValidation | None = None


class DeletedResponse(BaseModel):
    deleted: bool


class AgentByRoleResponse(BaseModel):
    id: str
    name: str
    title: str
    description: str | None = None
    status: str
    model_name: str | None = None
    autonomy_level: str | None = None


class AgentRemovedResponse(BaseModel):
    removed: bool
    agent_id: str


class AgentRoleUpdatedResponse(BaseModel):
    id: str
    name: str
    title: str | None = None
    description: str | None = None
    model_name: str | None = None
    autonomy_level: str | None = None


class CustomRoleResponse(BaseModel):
    id: str
    role_key: str
    name: str
    title: str
    description: str


class CustomRoleListItemResponse(BaseModel):
    id: str
    role_key: str
    name: str
    title: str
    description: str
    autonomy_level: str | None = None
    can_delegate: bool = False


class AvailableRoleResponse(BaseModel):
    role_key: str
    name: str
    title: str
    description: str
    is_preset: bool


class FeatureRequestResponse(BaseModel):
    id: str
    request_text: str
    interpreted_action: str | None = None
    interpreted_details: dict | None = None
    status: str
    result: dict | None = None


class FeatureRequestListItemResponse(BaseModel):
    id: str
    request_text: str
    interpreted_action: str | None = None
    status: str
    created_at: str


# ===================================================================
# Multi-model comparison
# ===================================================================


@router.post(
    "/companies/{company_id}/multi-model/compare",
    response_model=MultiModelCompareResponse,
)
@limiter.limit("20/minute")
async def create_multi_model_comparison(
    request: Request,
    company_id: str,
    req: MultiModelCompareRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a request to send the same input to multiple models and compare responses."""
    # Prompt injection check
    guard_result = scan_prompt_injection(req.input_text)
    if guard_result.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        raise HTTPException(
            status_code=400,
            detail="Request blocked: potentially unsafe content detected.",
        )

    # PII detection and masking
    pii_result = detect_and_mask_pii(req.input_text)
    if pii_result.detected_count > 0:
        logger.warning(
            "PII detected in multi-model compare: types=%s",
            pii_result.detected_types,
        )

    from app.services.multi_model_service import MultiModelService

    svc = MultiModelService(db)
    record = await svc.create_comparison(
        company_id=company_id,
        input_text=pii_result.masked_text,
        model_ids=req.model_ids,
        session_id=req.session_id,
        metadata=req.metadata,
    )
    await db.commit()
    await db.refresh(record)
    return MultiModelCompareResponse(
        id=str(record.id),
        input_text=record.input_text,
        input_char_count=record.input_char_count,
        models_requested=record.models_requested,
        responses=record.responses_json,
        status=record.status,
        created_at=record.created_at.isoformat() if record.created_at else "",
    )


@router.post("/multi-model/{comparison_id}/response", response_model=ModelResponseUpdateResponse)
async def record_model_response(
    comparison_id: str,
    req: ModelResponseRecord,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Record an individual model response."""
    from app.services.multi_model_service import MultiModelService

    svc = MultiModelService(db)
    record = await svc.record_model_response(
        comparison_id=comparison_id,
        model_id=req.model_id,
        response_text=req.response_text,
        latency_ms=req.latency_ms,
        tokens_used=req.tokens_used,
        error=req.error,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Comparison not found")
    await db.commit()
    await db.refresh(record)
    return {
        "id": str(record.id),
        "status": record.status,
        "responses": record.responses_json,
    }


@router.get("/multi-model/{comparison_id}", response_model=MultiModelCompareResponse)
async def get_comparison(
    comparison_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get comparison result."""
    from app.services.multi_model_service import MultiModelService

    svc = MultiModelService(db)
    try:
        record = await svc.get_comparison(comparison_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Comparison not found")
    if not record:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return {
        "id": str(record.id),
        "input_text": record.input_text,
        "input_char_count": record.input_char_count,
        "models_requested": record.models_requested,
        "responses": record.responses_json,
        "status": record.status,
        "created_at": record.created_at.isoformat() if record.created_at else "",
    }


@router.get(
    "/companies/{company_id}/multi-model/comparisons",
    response_model=list[ComparisonSummaryResponse],
)
async def list_comparisons(
    company_id: str,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List comparisons."""
    from app.services.multi_model_service import MultiModelService

    svc = MultiModelService(db)
    records = await svc.list_comparisons(company_id=company_id, offset=offset, limit=limit)
    return [
        {
            "id": str(r.id),
            "input_text": r.input_text[:200],
            "input_char_count": r.input_char_count,
            "models_requested": r.models_requested,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else "",
        }
        for r in records
    ]


# ===================================================================
# Brainstorming
# ===================================================================


@router.post(
    "/companies/{company_id}/brainstorm",
    response_model=BrainstormSessionResponse,
)
async def create_brainstorm_session(
    company_id: str,
    req: BrainstormCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a brainstorming session."""
    from app.services.multi_model_service import BrainstormService

    svc = BrainstormService(db)
    record = await svc.create_session(
        company_id=company_id,
        title=req.title,
        topic=req.topic,
        session_type=req.session_type,
        model_ids=req.model_ids,
        is_multi_model=req.is_multi_model,
    )
    await db.commit()
    await db.refresh(record)
    return BrainstormSessionResponse(
        id=str(record.id),
        title=record.title,
        topic=record.topic,
        session_type=record.session_type,
        model_ids=record.model_ids,
        status=record.status,
        message_count=record.message_count,
        total_chars=record.total_chars,
        is_multi_model=record.is_multi_model,
        created_at=record.created_at.isoformat() if record.created_at else "",
    )


@router.post("/brainstorm/{session_id}/message", response_model=BrainstormMessageAddedResponse)
@limiter.limit("30/minute")
async def add_brainstorm_message(
    request: Request,
    session_id: str,
    req: BrainstormMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add a message to a brainstorming session."""
    # Prompt injection check
    guard_result = scan_prompt_injection(req.content)
    if guard_result.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        raise HTTPException(
            status_code=400,
            detail="Request blocked: potentially unsafe content detected.",
        )

    # PII masking
    pii_result = detect_and_mask_pii(req.content)
    if pii_result.detected_count > 0:
        logger.warning(
            "PII detected in brainstorm message: types=%s",
            pii_result.detected_types,
        )

    from app.services.multi_model_service import BrainstormService

    svc = BrainstormService(db)
    record = await svc.add_message(
        session_id=session_id,
        role=req.role,
        content=pii_result.masked_text,
        model_id=req.model_id,
        metadata=req.metadata,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.commit()
    await db.refresh(record)
    return {
        "session_id": str(record.id),
        "message_count": record.message_count,
        "total_chars": record.total_chars,
        "latest_messages": (record.conversation_history or {}).get("messages", [])[-5:],
    }


@router.get("/brainstorm/{session_id}", response_model=BrainstormSessionDetailResponse)
async def get_brainstorm_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a brainstorming session."""
    from app.services.multi_model_service import BrainstormService

    svc = BrainstormService(db)
    try:
        record = await svc.get_session(session_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": str(record.id),
        "title": record.title,
        "topic": record.topic,
        "session_type": record.session_type,
        "model_ids": record.model_ids,
        "conversation_history": record.conversation_history,
        "insights": record.insights_json,
        "status": record.status,
        "message_count": record.message_count,
        "total_chars": record.total_chars,
        "is_multi_model": record.is_multi_model,
        "created_at": record.created_at.isoformat() if record.created_at else "",
    }


@router.get(
    "/companies/{company_id}/brainstorm/sessions",
    response_model=list[BrainstormSessionResponse],
)
async def list_brainstorm_sessions(
    company_id: str,
    status: str | None = None,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List brainstorming sessions."""
    from app.services.multi_model_service import BrainstormService

    svc = BrainstormService(db)
    records = await svc.list_sessions(
        company_id=company_id, status=status, offset=offset, limit=limit
    )
    return [
        BrainstormSessionResponse(
            id=str(r.id),
            title=r.title,
            topic=r.topic,
            session_type=r.session_type,
            model_ids=r.model_ids,
            status=r.status,
            message_count=r.message_count,
            total_chars=r.total_chars,
            is_multi_model=r.is_multi_model,
            created_at=r.created_at.isoformat() if r.created_at else "",
        ).model_dump()
        for r in records
    ]


@router.post("/brainstorm/{session_id}/status", response_model=BrainstormStatusResponse)
async def update_brainstorm_status(
    session_id: str,
    status: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update brainstorming session status."""
    from app.services.multi_model_service import BrainstormService

    svc = BrainstormService(db)
    record = await svc.update_session_status(session_id, status)
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.commit()
    return {"session_id": str(record.id), "status": record.status}


@router.get(
    "/companies/{company_id}/brainstorm/search",
    response_model=list[BrainstormSearchResultResponse],
)
async def search_brainstorm_sessions(
    company_id: str,
    q: str = "",
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Search brainstorming sessions."""
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    from app.services.multi_model_service import BrainstormService

    svc = BrainstormService(db)
    records = await svc.search_sessions(company_id=company_id, query=q, limit=limit)
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "topic": r.topic,
            "status": r.status,
            "message_count": r.message_count,
        }
        for r in records
    ]


# ===================================================================
# Conversation memory
# ===================================================================


@router.post(
    "/companies/{company_id}/conversation-memory",
    response_model=ConversationMemoryResponse,
)
async def store_conversation_message(
    company_id: str,
    req: ConversationStoreRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Store a conversation message."""
    from app.services.multi_model_service import ConversationMemoryService

    svc = ConversationMemoryService(db)
    record = await svc.store_message(
        company_id=company_id,
        role=req.role,
        content=req.content,
        agent_id=req.agent_id,
        session_ref=req.session_ref,
        content_type=req.content_type,
        metadata=req.metadata,
    )
    await db.commit()
    await db.refresh(record)
    return ConversationMemoryResponse(
        id=str(record.id),
        role=record.role,
        content=record.content,
        char_count=record.char_count,
        content_type=record.content_type,
        agent_id=str(record.agent_id) if record.agent_id else None,
        session_ref=record.session_ref,
        created_at=record.created_at.isoformat() if record.created_at else "",
    )


@router.get(
    "/companies/{company_id}/conversation-memory",
    response_model=list[ConversationMemoryResponse],
)
async def get_conversation_history(
    company_id: str,
    user_id: str | None = None,
    agent_id: str | None = None,
    session_ref: str | None = None,
    content_type: str | None = None,
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get conversation history."""
    from app.services.multi_model_service import ConversationMemoryService

    svc = ConversationMemoryService(db)
    records = await svc.get_conversation_history(
        company_id=company_id,
        user_id=user_id,
        agent_id=agent_id,
        session_ref=session_ref,
        content_type=content_type,
        offset=offset,
        limit=limit,
    )
    return [
        ConversationMemoryResponse(
            id=str(r.id),
            role=r.role,
            content=r.content,
            char_count=r.char_count,
            content_type=r.content_type,
            agent_id=str(r.agent_id) if r.agent_id else None,
            session_ref=r.session_ref,
            created_at=r.created_at.isoformat() if r.created_at else "",
        ).model_dump()
        for r in records
    ]


@router.get(
    "/companies/{company_id}/conversation-memory/search",
    response_model=list[ConversationMemorySearchResponse],
)
async def search_conversation_memory(
    company_id: str,
    q: str = "",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Search conversation memory."""
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    from app.services.multi_model_service import ConversationMemoryService

    svc = ConversationMemoryService(db)
    records = await svc.search_memories(company_id=company_id, query=q, limit=limit)
    return [
        {
            "id": str(r.id),
            "role": r.role,
            "content": r.content[:200],
            "char_count": r.char_count,
            "content_type": r.content_type,
            "created_at": r.created_at.isoformat() if r.created_at else "",
        }
        for r in records
    ]


@router.get(
    "/companies/{company_id}/conversation-memory/stats",
    response_model=ConversationStatsResponse,
)
async def get_conversation_stats(
    company_id: str,
    user_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get conversation memory statistics."""
    from app.services.multi_model_service import ConversationMemoryService

    svc = ConversationMemoryService(db)
    return await svc.get_total_stats(company_id=company_id, user_id=user_id)


# ===================================================================
# Text analysis (character counting)
# ===================================================================


@router.post("/text/analyze", response_model=TextAnalysisResponse)
async def analyze_text(req: TextAnalysisRequest, user: User = Depends(get_current_user)):
    """Analyze text (accurate character counting)."""
    from app.services.multi_model_service import TextAnalyzer

    analysis = TextAnalyzer.count_characters(req.text)
    result: dict = {"analysis": analysis}

    if req.min_chars is not None or req.max_chars is not None:
        validation = TextAnalyzer.validate_length(
            req.text,
            min_chars=req.min_chars or 0,
            max_chars=req.max_chars,
        )
        result["validation"] = validation

    return result


# ===================================================================
# Per-role model configuration
# ===================================================================


@router.put("/companies/{company_id}/role-models", response_model=RoleModelConfigResponse)
async def set_role_model(
    company_id: str,
    req: RoleModelConfigRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add or update model configuration for a role."""
    from app.services.multi_model_service import AgentRoleModelService

    svc = AgentRoleModelService(db)
    config = await svc.set_role_model(
        company_id=company_id,
        role_name=req.role_name,
        model_id=req.model_id,
        agent_id=req.agent_id,
        fallback_model_id=req.fallback_model_id,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        system_prompt=req.system_prompt,
    )
    await db.commit()
    await db.refresh(config)
    return RoleModelConfigResponse(
        id=str(config.id),
        role_name=config.role_name,
        model_id=config.model_id,
        fallback_model_id=config.fallback_model_id,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        is_active=config.is_active,
        created_at=config.created_at.isoformat() if config.created_at else "",
    )


@router.get(
    "/companies/{company_id}/role-models",
    response_model=list[RoleModelConfigResponse],
)
async def list_role_models(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all role model configurations."""
    from app.services.multi_model_service import AgentRoleModelService

    svc = AgentRoleModelService(db)
    configs = await svc.list_role_models(company_id)
    return [
        RoleModelConfigResponse(
            id=str(c.id),
            role_name=c.role_name,
            model_id=c.model_id,
            fallback_model_id=c.fallback_model_id,
            max_tokens=c.max_tokens,
            temperature=c.temperature,
            is_active=c.is_active,
            created_at=c.created_at.isoformat() if c.created_at else "",
        ).model_dump()
        for c in configs
    ]


@router.get(
    "/companies/{company_id}/role-models/{role_name}",
    response_model=RoleModelConfigResponse,
)
async def get_role_model(
    company_id: str,
    role_name: str,
    agent_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get model configuration for a specific role."""
    from app.services.multi_model_service import AgentRoleModelService

    svc = AgentRoleModelService(db)
    config = await svc.get_role_model(company_id=company_id, role_name=role_name, agent_id=agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Role model config not found")
    return RoleModelConfigResponse(
        id=str(config.id),
        role_name=config.role_name,
        model_id=config.model_id,
        fallback_model_id=config.fallback_model_id,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        is_active=config.is_active,
        created_at=config.created_at.isoformat() if config.created_at else "",
    )


@router.delete("/role-models/{config_id}", response_model=DeletedResponse)
async def delete_role_model(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a role model configuration."""
    from app.services.multi_model_service import AgentRoleModelService

    svc = AgentRoleModelService(db)
    deleted = await svc.delete_role_model(config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Config not found")
    await db.commit()
    return {"deleted": True}


# ===================================================================
# Agent organization management (dynamic add/remove/role customization)
# ===================================================================


@router.post("/companies/{company_id}/agents/by-role", response_model=AgentByRoleResponse)
async def add_agent_by_role(
    company_id: str,
    req: AgentAddByRoleRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add an agent by specifying a role."""
    from app.services.agent_org_service import AgentOrgService

    svc = AgentOrgService(db)
    agent = await svc.add_agent_by_role(
        company_id=company_id,
        role=req.role,
        name=req.name,
        description=req.description,
        model_name=req.model_name,
        provider_name=req.provider_name,
        team_id=req.team_id,
        custom_system_prompt=req.custom_system_prompt,
    )
    return {
        "id": str(agent.id),
        "name": agent.name,
        "title": agent.title,
        "description": agent.description,
        "status": agent.status,
        "model_name": agent.model_name,
        "autonomy_level": agent.autonomy_level,
    }


@router.delete("/agents/{agent_id}/remove", response_model=AgentRemovedResponse)
async def remove_agent(
    agent_id: str,
    req: AgentRemoveRequest | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Remove an agent from the organization."""
    from app.services.agent_org_service import AgentOrgService

    svc = AgentOrgService(db)
    reason = req.reason if req else ""
    removed = await svc.remove_agent(agent_id, reason=reason)
    if not removed:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"removed": True, "agent_id": agent_id}


@router.patch("/agents/{agent_id}/role", response_model=AgentRoleUpdatedResponse)
async def update_agent_role(
    agent_id: str,
    req: AgentUpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update agent role settings."""
    from app.services.agent_org_service import AgentOrgService

    svc = AgentOrgService(db)
    agent = await svc.update_agent_role(
        agent_id=agent_id,
        name=req.name,
        title=req.title,
        description=req.description,
        model_name=req.model_name,
        provider_name=req.provider_name,
        autonomy_level=req.autonomy_level,
        system_prompt=req.system_prompt,
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "id": str(agent.id),
        "name": agent.name,
        "title": agent.title,
        "description": agent.description,
        "model_name": agent.model_name,
        "autonomy_level": agent.autonomy_level,
    }


# ===================================================================
# Custom role management
# ===================================================================


@router.post("/companies/{company_id}/custom-roles", response_model=CustomRoleResponse)
async def create_custom_role(
    company_id: str,
    req: CustomRoleCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a custom agent role."""
    from app.services.agent_org_service import AgentOrgService

    svc = AgentOrgService(db)
    role = await svc.create_custom_role(
        company_id=company_id,
        role_key=req.role_key,
        name=req.name,
        title=req.title,
        description=req.description,
        system_prompt=req.system_prompt,
        autonomy_level=req.autonomy_level,
        can_delegate=req.can_delegate,
    )
    await db.commit()
    await db.refresh(role)
    return {
        "id": str(role.id),
        "role_key": role.role_key,
        "name": role.name,
        "title": role.title,
        "description": role.description,
    }


@router.get(
    "/companies/{company_id}/custom-roles",
    response_model=list[CustomRoleListItemResponse],
)
async def list_custom_roles(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List custom roles."""
    from app.services.agent_org_service import AgentOrgService

    svc = AgentOrgService(db)
    roles = await svc.list_custom_roles(company_id)
    return [
        {
            "id": str(r.id),
            "role_key": r.role_key,
            "name": r.name,
            "title": r.title,
            "description": r.description,
            "autonomy_level": r.autonomy_level,
            "can_delegate": r.can_delegate,
        }
        for r in roles
    ]


@router.delete("/custom-roles/{role_id}", response_model=DeletedResponse)
async def delete_custom_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a custom role."""
    from app.services.agent_org_service import AgentOrgService

    svc = AgentOrgService(db)
    deleted = await svc.delete_custom_role(role_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Custom role not found")
    await db.commit()
    return {"deleted": True}


@router.get(
    "/companies/{company_id}/available-roles",
    response_model=list[AvailableRoleResponse],
)
async def get_available_roles(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all available roles (preset + custom)."""
    from app.services.agent_org_service import AgentOrgService

    svc = AgentOrgService(db)
    return await svc.get_available_roles(company_id)


# ===================================================================
# Natural language feature requests
# ===================================================================


@router.post("/companies/{company_id}/feature-requests", response_model=FeatureRequestResponse)
@limiter.limit("20/minute")
async def submit_natural_language_request(
    request: Request,
    company_id: str,
    req: NaturalLanguageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Submit a request to the AI organization in natural language."""
    # Prompt injection check
    guard_result = scan_prompt_injection(req.request_text)
    if guard_result.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        raise HTTPException(
            status_code=400,
            detail="Request blocked: potentially unsafe content detected.",
        )

    # PII masking
    pii_result = detect_and_mask_pii(req.request_text)
    if pii_result.detected_count > 0:
        logger.warning(
            "PII detected in feature request: types=%s",
            pii_result.detected_types,
        )

    from app.services.agent_org_service import AgentOrgService

    svc = AgentOrgService(db)
    record = await svc.process_natural_language_request(
        company_id=company_id,
        request_text=pii_result.masked_text,
        auto_execute=req.auto_execute,
    )
    await db.commit()
    await db.refresh(record)
    return {
        "id": str(record.id),
        "request_text": record.request_text,
        "interpreted_action": record.interpreted_action,
        "interpreted_details": record.interpreted_details,
        "status": record.status,
        "result": record.result_json,
    }


@router.get(
    "/companies/{company_id}/feature-requests",
    response_model=list[FeatureRequestListItemResponse],
)
async def list_feature_requests(
    company_id: str,
    status: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List feature requests."""
    from app.services.agent_org_service import AgentOrgService

    svc = AgentOrgService(db)
    records = await svc.list_feature_requests(company_id=company_id, status=status, limit=limit)
    return [
        {
            "id": str(r.id),
            "request_text": r.request_text,
            "interpreted_action": r.interpreted_action,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else "",
        }
        for r in records
    ]
