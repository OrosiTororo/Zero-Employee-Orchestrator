"""Ollama management API routes.

Provides endpoints for managing the local Ollama instance:
- Health check
- Model listing / discovery
- Model pull
- Chat completion (direct)
- RAG search
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class OllamaHealthResponse(BaseModel):
    available: bool
    base_url: str
    models_count: int = 0


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


class RAGAddResponse(BaseModel):
    ids: list[str]
    chunks: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/ollama/health", response_model=OllamaHealthResponse)
async def ollama_health():
    """Check Ollama availability."""
    from app.providers.ollama_provider import ollama_provider

    is_up = await ollama_provider.health_check()
    models = await ollama_provider.list_models() if is_up else []

    return OllamaHealthResponse(
        available=is_up,
        base_url=ollama_provider.base_url,
        models_count=len(models),
    )


@router.get("/ollama/models", response_model=OllamaModelsResponse)
async def ollama_models():
    """List available Ollama models."""
    from app.providers.ollama_provider import ollama_provider, RECOMMENDED_MODELS

    models = await ollama_provider.list_models(force_refresh=True)

    result = []
    for m in models:
        size_gb = m.size / (1024 ** 3) if m.size else 0
        size_str = f"{size_gb:.1f}GB" if size_gb >= 1.0 else f"{m.size / (1024**2):.0f}MB"
        rec = RECOMMENDED_MODELS.get(m.name, {})
        result.append(OllamaModelResponse(
            name=m.name,
            size=m.size,
            size_display=size_str,
            description=rec.get("description", ""),
            modified_at=m.modified_at,
        ))

    return OllamaModelsResponse(models=result, total=len(result))


@router.post("/ollama/pull", response_model=OllamaPullResponse)
async def ollama_pull(req: OllamaPullRequest):
    """Pull (download) an Ollama model."""
    from app.providers.ollama_provider import ollama_provider

    is_up = await ollama_provider.health_check()
    if not is_up:
        raise HTTPException(status_code=503, detail="Ollama is not running")

    ok = await ollama_provider.pull_model(req.model)
    return OllamaPullResponse(
        success=ok,
        model=req.model,
        message="Pull accepted" if ok else "Pull failed",
    )


@router.post("/ollama/chat", response_model=OllamaChatResponse)
async def ollama_chat(req: OllamaChatRequest):
    """Send a chat completion to Ollama directly."""
    from app.providers.ollama_provider import ollama_provider

    resp = await ollama_provider.complete(
        messages=req.messages,
        model=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )

    if resp.finish_reason == "error":
        raise HTTPException(status_code=503, detail=resp.content)

    return OllamaChatResponse(
        content=resp.content,
        model_used=resp.model_used,
        provider=resp.provider,
        tokens_input=resp.tokens_input,
        tokens_output=resp.tokens_output,
        finish_reason=resp.finish_reason,
        tool_calls=resp.tool_calls,
    )


@router.post("/ollama/rag/search", response_model=RAGSearchResponse)
async def rag_search(req: RAGSearchRequest):
    """Search the local RAG vector store."""
    from app.providers.local_rag import local_rag

    results = local_rag.search(
        query=req.query,
        top_k=req.top_k,
        min_score=req.min_score,
    )

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
async def rag_add(req: RAGAddRequest):
    """Add a document to the local RAG vector store."""
    from app.providers.local_rag import local_rag

    ids = local_rag.add(
        content=req.content,
        metadata=req.metadata,
    )
    local_rag.save()

    return RAGAddResponse(ids=ids, chunks=len(ids))
