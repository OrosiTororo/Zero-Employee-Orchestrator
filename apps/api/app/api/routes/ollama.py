"""Ollama management API routes.

Provides endpoints for managing the local Ollama instance:
- Health check
- Model listing / discovery
- Model pull
- Chat completion (direct + streaming SSE)
- RAG search / add
- Heartbeat health check
- Knowledge Pipeline integration
"""

from __future__ import annotations

import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class OllamaHealthResponse(BaseModel):
    available: bool
    base_url: str
    models_count: int = 0
    embedding_available: bool = False


class OllamaModelResponse(BaseModel):
    name: str
    size: int = 0
    size_display: str = ""
    description: str = ""
    modified_at: str = ""


class OllamaModelsResponse(BaseModel):
    models: list[OllamaModelResponse]
    total: int


class OllamaPullRequest(BaseModel):
    model: str = Field(..., description="Model name (e.g. qwen3:8b)")


class OllamaPullResponse(BaseModel):
    success: bool
    model: str
    message: str = ""


class OllamaChatRequest(BaseModel):
    messages: list[dict] = Field(..., description="OpenAI-style message list")
    model: str | None = Field(None, description="Model name (auto-detect if empty)")
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = Field(False, description="Enable SSE streaming")


class OllamaChatResponse(BaseModel):
    content: str
    model_used: str
    provider: str
    tokens_input: int = 0
    tokens_output: int = 0
    finish_reason: str = "stop"
    tool_calls: list[dict] = []


class RAGSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = 5
    min_score: float = 0.05


class RAGSearchResult(BaseModel):
    content: str
    score: float
    metadata: dict = {}


class RAGSearchResponse(BaseModel):
    results: list[RAGSearchResult]
    total: int


class RAGAddRequest(BaseModel):
    content: str = Field(..., description="Document content")
    metadata: dict = Field(default_factory=dict)
    task_id: str | None = Field(None, description="Associated task ID for artifact tracking")


class RAGAddResponse(BaseModel):
    ids: list[str]
    chunks: int
    artifact_id: str | None = None


class HeartbeatCheckResponse(BaseModel):
    ollama_available: bool
    models_count: int
    model_names: list[str]
    embedding_available: bool
    rag_document_count: int
    checked_at: float


class KnowledgeSearchRequest(BaseModel):
    task_context: str = Field(..., description="Task description for knowledge retrieval")
    max_tokens: int = 4000


class KnowledgeSearchResponse(BaseModel):
    entries: list[dict]
    total: int


class KnowledgeStoreRequest(BaseModel):
    task_type: str = Field(..., description="Type of task (e.g. 'code_generation')")
    model: str = Field(..., description="Model used")
    success: bool
    duration_seconds: float
    details: str = ""
    tags: list[str] = Field(default_factory=list)


class KnowledgeStoreResponse(BaseModel):
    entry_id: str
    stored: bool


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/ollama/health", response_model=OllamaHealthResponse)
async def ollama_health(user: User = Depends(get_current_user)):
    """Check Ollama availability and embedding support."""
    from app.providers.local_rag import OllamaEmbeddingStore
    from app.providers.ollama_provider import ollama_provider

    is_up = await ollama_provider.health_check()
    models = await ollama_provider.list_models() if is_up else []

    # Check embedding support
    embedding_available = False
    if is_up:
        embed_store = OllamaEmbeddingStore(ollama_url=ollama_provider.base_url)
        embedding_available = await embed_store.check_embedding_support()

    return OllamaHealthResponse(
        available=is_up,
        base_url=ollama_provider.base_url,
        models_count=len(models),
        embedding_available=embedding_available,
    )


@router.get("/ollama/models", response_model=OllamaModelsResponse)
async def ollama_models(user: User = Depends(get_current_user)):
    """List available Ollama models."""
    from app.providers.ollama_provider import RECOMMENDED_MODELS, ollama_provider

    models = await ollama_provider.list_models(force_refresh=True)

    result = []
    for m in models:
        size_gb = m.size / (1024**3) if m.size else 0
        size_str = f"{size_gb:.1f}GB" if size_gb >= 1.0 else f"{m.size / (1024**2):.0f}MB"
        rec = RECOMMENDED_MODELS.get(m.name, {})
        result.append(
            OllamaModelResponse(
                name=m.name,
                size=m.size,
                size_display=size_str,
                description=rec.get("description", ""),
                modified_at=m.modified_at,
            )
        )

    return OllamaModelsResponse(models=result, total=len(result))


@router.post("/ollama/pull", response_model=OllamaPullResponse)
async def ollama_pull(
    req: OllamaPullRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pull (download) an Ollama model with audit logging."""
    from app.providers.ollama_integration import (
        audit_ollama_model_pull,
        reset_embedding_cache,
    )
    from app.providers.ollama_provider import ollama_provider

    is_up = await ollama_provider.health_check()
    if not is_up:
        raise HTTPException(status_code=503, detail="Ollama is not running")

    start = time.monotonic()
    ok = await ollama_provider.pull_model(req.model)
    duration = time.monotonic() - start

    # Audit log (best-effort, don't fail the request)
    try:
        await audit_ollama_model_pull(
            db=db,
            company_id="00000000-0000-0000-0000-000000000000",
            model=req.model,
            success=ok,
            duration_seconds=duration,
        )
    except Exception:
        pass

    # Reset embedding cache since new models might include embedding model
    if ok:
        reset_embedding_cache()

    return OllamaPullResponse(
        success=ok,
        model=req.model,
        message="Pull accepted" if ok else "Pull failed",
    )


@router.post("/ollama/chat", response_model=OllamaChatResponse)
async def ollama_chat(
    req: OllamaChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a chat completion to Ollama directly.

    If ``stream=true``, returns an SSE stream instead of JSON.
    """
    if req.stream:
        return await _ollama_chat_stream(req)

    from app.providers.ollama_integration import audit_ollama_chat, record_ollama_cost
    from app.providers.ollama_provider import ollama_provider

    start = time.monotonic()
    resp = await ollama_provider.complete(
        messages=req.messages,
        model=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    duration_ms = int((time.monotonic() - start) * 1000)

    if resp.finish_reason == "error":
        raise HTTPException(status_code=503, detail=resp.content)

    # Audit & cost (best-effort)
    try:
        await audit_ollama_chat(
            db=db,
            company_id="00000000-0000-0000-0000-000000000000",
            model=resp.model_used,
            tokens_input=resp.tokens_input,
            tokens_output=resp.tokens_output,
            duration_ms=duration_ms,
        )
        await record_ollama_cost(
            db=db,
            company_id="00000000-0000-0000-0000-000000000000",
            model=resp.model_used,
            tokens_input=resp.tokens_input,
            tokens_output=resp.tokens_output,
        )
    except Exception:
        pass

    return OllamaChatResponse(
        content=resp.content,
        model_used=resp.model_used,
        provider=resp.provider,
        tokens_input=resp.tokens_input,
        tokens_output=resp.tokens_output,
        finish_reason=resp.finish_reason,
        tool_calls=resp.tool_calls,
    )


async def _ollama_chat_stream(req: OllamaChatRequest) -> StreamingResponse:
    """SSE streaming chat completion from Ollama."""
    from app.providers.ollama_provider import ollama_provider

    async def event_generator():
        try:
            async for chunk in ollama_provider.complete_stream(
                messages=req.messages,
                model=req.model,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            ):
                data = json.dumps({"content": chunk, "done": False}, ensure_ascii=False)
                yield f"data: {data}\n\n"

            # Final event
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
        except Exception as exc:
            error_data = json.dumps({"error": str(exc), "done": True})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/ollama/chat/stream")
async def ollama_chat_stream(req: OllamaChatRequest, user: User = Depends(get_current_user)):
    """Dedicated SSE streaming endpoint for Ollama chat.

    Returns a Server-Sent Events stream with chunks:
    ``data: {"content": "...", "done": false}``

    Final event:
    ``data: {"content": "", "done": true}``
    """
    return await _ollama_chat_stream(req)


@router.post("/ollama/rag/search", response_model=RAGSearchResponse)
async def rag_search(
    req: RAGSearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search the local RAG vector store (auto-selects best backend)."""
    from app.providers.ollama_integration import audit_rag_search, get_rag_store

    store = await get_rag_store()
    results = store.search(
        query=req.query,
        top_k=req.top_k,
        min_score=req.min_score,
    )

    # Audit (best-effort)
    try:
        await audit_rag_search(
            db=db,
            company_id="00000000-0000-0000-0000-000000000000",
            query=req.query,
            results_count=len(results),
        )
    except Exception:
        pass

    return RAGSearchResponse(
        results=[
            RAGSearchResult(
                content=r.chunk_text,
                score=r.score,
                metadata=r.document.metadata,
            )
            for r in results
        ],
        total=len(results),
    )


@router.post("/ollama/rag/add", response_model=RAGAddResponse)
async def rag_add(
    req: RAGAddRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a document to the local RAG vector store with artifact tracking."""
    from app.providers.ollama_integration import (
        audit_rag_add,
        get_rag_store,
        register_rag_artifact,
    )

    store = await get_rag_store()
    ids = store.add(
        content=req.content,
        metadata=req.metadata,
    )
    store.save()

    # Register as artifact if task_id provided
    artifact_id = None
    if req.task_id:
        try:
            artifact_id = register_rag_artifact(
                task_id=req.task_id,
                doc_count=len(ids),
                store_path=str(store.store_dir),
                summary=f"Added {len(ids)} chunks to RAG store",
            )
        except Exception:
            pass

    # Audit (best-effort)
    try:
        await audit_rag_add(
            db=db,
            company_id="00000000-0000-0000-0000-000000000000",
            doc_ids=ids,
            chunks=len(ids),
            metadata=req.metadata,
        )
    except Exception:
        pass

    return RAGAddResponse(ids=ids, chunks=len(ids), artifact_id=artifact_id)


# ---------------------------------------------------------------------------
# Heartbeat endpoint
# ---------------------------------------------------------------------------


@router.get("/ollama/heartbeat", response_model=HeartbeatCheckResponse)
async def ollama_heartbeat(user: User = Depends(get_current_user)):
    """Run an Ollama heartbeat health check.

    Checks Ollama availability, model list, embedding support,
    and RAG store health.
    """
    from app.providers.ollama_integration import run_ollama_heartbeat

    result = await run_ollama_heartbeat()

    return HeartbeatCheckResponse(
        ollama_available=result.ollama_available,
        models_count=result.models_count,
        model_names=result.model_names,
        embedding_available=result.embedding_available,
        rag_document_count=result.rag_document_count,
        checked_at=result.checked_at,
    )


# ---------------------------------------------------------------------------
# Knowledge Pipeline endpoints
# ---------------------------------------------------------------------------


@router.post("/ollama/knowledge/search", response_model=KnowledgeSearchResponse)
async def knowledge_search(req: KnowledgeSearchRequest, user: User = Depends(get_current_user)):
    """Search the Knowledge Pipeline for Ollama task patterns.

    Returns experience memories and failure taxonomy entries
    relevant to the given task context.
    """
    from app.providers.ollama_integration import retrieve_ollama_knowledge

    entries = retrieve_ollama_knowledge(
        task_context=req.task_context,
        max_tokens=req.max_tokens,
    )

    return KnowledgeSearchResponse(entries=entries, total=len(entries))


@router.post("/ollama/knowledge/store", response_model=KnowledgeStoreResponse)
async def knowledge_store_endpoint(
    req: KnowledgeStoreRequest, user: User = Depends(get_current_user)
):
    """Store an Ollama task execution result in the Knowledge Pipeline.

    Records successes as experience memory and failures as failure taxonomy.
    """
    from app.providers.ollama_integration import store_ollama_experience

    entry_id = store_ollama_experience(
        task_type=req.task_type,
        model=req.model,
        success=req.success,
        duration_seconds=req.duration_seconds,
        details=req.details,
        tags=req.tags,
    )

    return KnowledgeStoreResponse(entry_id=entry_id, stored=True)
