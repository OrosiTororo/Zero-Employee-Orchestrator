"""Ollama integration layer — bridges Ollama/RAG with core orchestration modules.

Connects the Ollama provider and local RAG with:
- Audit logging (record all Ollama operations)
- Heartbeat scheduler (periodic Ollama health checks)
- Knowledge Pipeline (store/retrieve knowledge via RAG)
- Artifact Bridge (register RAG outputs as artifacts)
- OllamaEmbeddingStore auto-activation
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Audit helpers — thin wrappers around audit.logger for Ollama events
# ---------------------------------------------------------------------------

async def audit_ollama_chat(
    db: AsyncSession,
    company_id: str | uuid.UUID,
    model: str,
    tokens_input: int,
    tokens_output: int,
    *,
    actor_type: str = "system",
    actor_user_id: str | uuid.UUID | None = None,
    duration_ms: int = 0,
) -> None:
    """Record an Ollama chat completion in the audit log."""
    try:
        from app.audit.logger import record_audit_event

        await record_audit_event(
            db=db,
            company_id=company_id,
            event_type="ollama.chat.completed",
            target_type="ollama_model",
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            details={
                "model": model,
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "duration_ms": duration_ms,
                "cost_usd": 0.0,
            },
        )
    except Exception as exc:
        logger.debug("Audit log for ollama chat failed: %s", exc)


async def audit_ollama_model_pull(
    db: AsyncSession,
    company_id: str | uuid.UUID,
    model: str,
    success: bool,
    *,
    actor_type: str = "system",
    actor_user_id: str | uuid.UUID | None = None,
    duration_seconds: float = 0.0,
) -> None:
    """Record an Ollama model pull in the audit log."""
    try:
        from app.audit.logger import record_audit_event

        await record_audit_event(
            db=db,
            company_id=company_id,
            event_type="ollama.model.pulled" if success else "ollama.model.pull_failed",
            target_type="ollama_model",
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            details={
                "model": model,
                "success": success,
                "duration_seconds": round(duration_seconds, 2),
            },
        )
    except Exception as exc:
        logger.debug("Audit log for model pull failed: %s", exc)


async def audit_rag_add(
    db: AsyncSession,
    company_id: str | uuid.UUID,
    doc_ids: list[str],
    chunks: int,
    metadata: dict | None = None,
    *,
    actor_type: str = "system",
    actor_user_id: str | uuid.UUID | None = None,
) -> None:
    """Record a RAG document addition in the audit log."""
    try:
        from app.audit.logger import record_audit_event

        await record_audit_event(
            db=db,
            company_id=company_id,
            event_type="rag.document.added",
            target_type="rag_document",
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            details={
                "document_ids": doc_ids[:10],  # limit logged IDs
                "chunks": chunks,
                "metadata_keys": list((metadata or {}).keys()),
            },
        )
    except Exception as exc:
        logger.debug("Audit log for RAG add failed: %s", exc)


async def audit_rag_search(
    db: AsyncSession,
    company_id: str | uuid.UUID,
    query: str,
    results_count: int,
    *,
    actor_type: str = "system",
) -> None:
    """Record a RAG search in the audit log."""
    try:
        from app.audit.logger import record_audit_event

        await record_audit_event(
            db=db,
            company_id=company_id,
            event_type="rag.search.executed",
            target_type="rag_document",
            actor_type=actor_type,
            details={
                "query_length": len(query),
                "results_count": results_count,
            },
        )
    except Exception as exc:
        logger.debug("Audit log for RAG search failed: %s", exc)


# ---------------------------------------------------------------------------
# Heartbeat — Ollama health check integration
# ---------------------------------------------------------------------------

@dataclass
class OllamaHeartbeatResult:
    """Result of an Ollama heartbeat health check."""

    ollama_available: bool
    models_count: int
    model_names: list[str]
    embedding_available: bool
    rag_document_count: int
    checked_at: float


async def run_ollama_heartbeat(
    policy_id: str = "ollama_health_check",
    agent_id: str | None = None,
) -> OllamaHeartbeatResult:
    """Execute an Ollama-specific heartbeat check.

    Checks:
    1. Ollama service availability
    2. Available models
    3. Embedding model availability
    4. RAG document store health
    """
    from app.heartbeat.scheduler import (
        HeartbeatAction,
        HeartbeatTrigger,
        execute_heartbeat,
    )
    from app.providers.ollama_provider import ollama_provider
    from app.providers.local_rag import local_rag

    # Run base heartbeat
    execution = await execute_heartbeat(
        policy_id=policy_id,
        agent_id=agent_id,
        trigger=HeartbeatTrigger.SCHEDULED,
    )

    # Check Ollama
    is_up = await ollama_provider.health_check()
    models = await ollama_provider.list_models() if is_up else []
    model_names = [m.name for m in models]

    execution.add_action(HeartbeatAction(
        action_type="check_ollama",
        description="Ollama ヘルスチェック",
        result="available" if is_up else "unavailable",
    ))

    # Check embedding support
    embedding_available = False
    if is_up:
        from app.providers.local_rag import OllamaEmbeddingStore
        embed_store = OllamaEmbeddingStore(
            ollama_url=ollama_provider.base_url,
        )
        embedding_available = await embed_store.check_embedding_support()
        execution.add_action(HeartbeatAction(
            action_type="check_embedding",
            description="エンベディングモデルの確認",
            result="available" if embedding_available else "unavailable",
        ))

    # Check RAG store
    rag_count = local_rag.document_count
    execution.add_action(HeartbeatAction(
        action_type="check_rag",
        description="RAG ベクトルストアの確認",
        result=f"{rag_count} documents",
    ))

    execution.finish(
        success=is_up,
        summary=(
            f"Ollama: {'✓' if is_up else '✗'}, "
            f"Models: {len(models)}, "
            f"Embedding: {'✓' if embedding_available else '✗'}, "
            f"RAG docs: {rag_count}"
        ),
    )

    return OllamaHeartbeatResult(
        ollama_available=is_up,
        models_count=len(models),
        model_names=model_names,
        embedding_available=embedding_available,
        rag_document_count=rag_count,
        checked_at=time.time(),
    )


# ---------------------------------------------------------------------------
# Knowledge Pipeline — RAG ↔ KnowledgeStore bridge
# ---------------------------------------------------------------------------

def store_ollama_experience(
    task_type: str,
    model: str,
    success: bool,
    duration_seconds: float,
    *,
    details: str = "",
    tags: list[str] | None = None,
) -> str:
    """Store an Ollama task execution result in the Knowledge Pipeline.

    Records both successes (as experience memory) and failures
    (as failure taxonomy) for future reference.
    """
    from app.orchestration.knowledge_refresh import (
        KnowledgeEntry,
        KnowledgeStatus,
        KnowledgeType,
        knowledge_store,
    )

    entry_id = f"ollama_{'success' if success else 'failure'}_{uuid.uuid4().hex[:12]}"

    if success:
        entry = KnowledgeEntry(
            id=entry_id,
            title=f"{model} で {task_type} を実行成功",
            content=(
                f"モデル {model} が {task_type} タスクを "
                f"{duration_seconds:.1f}秒で完了。{details}"
            ),
            knowledge_type=KnowledgeType.EXPERIENCE_MEMORY,
            status=KnowledgeStatus.INDEXED,
            source="ollama_task_execution",
            tags=["ollama", model.split(":")[0], task_type, *(tags or [])],
            effective_conditions=f"model={model}, task_type={task_type}",
        )
    else:
        entry = KnowledgeEntry(
            id=entry_id,
            title=f"{model} で {task_type} が失敗",
            content=(
                f"モデル {model} が {task_type} タスクで失敗。"
                f"所要時間: {duration_seconds:.1f}秒。{details}"
            ),
            knowledge_type=KnowledgeType.FAILURE_TAXONOMY,
            status=KnowledgeStatus.INDEXED,
            source="ollama_task_execution",
            tags=["ollama", "failure", model.split(":")[0], task_type, *(tags or [])],
        )

    knowledge_store.add(entry)
    return entry_id


def retrieve_ollama_knowledge(
    task_context: str,
    max_tokens: int = 4000,
) -> list[dict]:
    """Retrieve relevant Ollama knowledge for a task.

    Searches both Experience Memory and Failure Taxonomy for patterns
    relevant to the given task context.
    """
    from app.orchestration.knowledge_refresh import (
        KnowledgeType,
        knowledge_store,
    )

    results: list[dict] = []

    # Search experience memory
    experiences = knowledge_store.search(
        task_context,
        knowledge_type=KnowledgeType.EXPERIENCE_MEMORY,
        limit=5,
    )
    for entry in experiences:
        results.append({
            "id": entry.id,
            "type": "experience",
            "title": entry.title,
            "content": entry.content,
            "tags": entry.tags,
            "status": entry.status.value,
        })

    # Search failure taxonomy
    failures = knowledge_store.search(
        task_context,
        knowledge_type=KnowledgeType.FAILURE_TAXONOMY,
        limit=3,
    )
    for entry in failures:
        results.append({
            "id": entry.id,
            "type": "failure",
            "title": entry.title,
            "content": entry.content,
            "tags": entry.tags,
            "status": entry.status.value,
        })

    return results


# ---------------------------------------------------------------------------
# Artifact Bridge — RAG ↔ Artifact registration
# ---------------------------------------------------------------------------

def register_rag_artifact(
    task_id: str,
    doc_count: int,
    store_path: str,
    *,
    summary: str = "",
) -> str:
    """Register the RAG vector store as a task artifact.

    Returns the artifact ID.
    """
    from app.orchestration.artifact_bridge import (
        ArtifactType,
        StorageType,
        artifact_bridge,
    )

    ref = artifact_bridge.register_output(
        task_id=task_id,
        title="RAG Vector Index",
        artifact_type=ArtifactType.DATA,
        content_or_path=store_path,
        mime_type="application/json",
        summary=summary or f"RAG ベクトルインデックス ({doc_count} ドキュメント)",
        storage_type=StorageType.LOCAL,
    )
    return ref.artifact_id


def register_ollama_output(
    task_id: str,
    title: str,
    content: str,
    *,
    artifact_type_str: str = "document",
    mime_type: str = "text/plain",
) -> str:
    """Register an Ollama-generated output as a task artifact.

    Returns the artifact ID.
    """
    from app.orchestration.artifact_bridge import (
        ArtifactType,
        StorageType,
        artifact_bridge,
    )

    type_map = {
        "document": ArtifactType.DOCUMENT,
        "code": ArtifactType.CODE,
        "data": ArtifactType.DATA,
        "report": ArtifactType.REPORT,
        "config": ArtifactType.CONFIG,
    }
    atype = type_map.get(artifact_type_str, ArtifactType.DOCUMENT)

    ref = artifact_bridge.register_output(
        task_id=task_id,
        title=title,
        artifact_type=atype,
        content_or_path=content,
        mime_type=mime_type,
        summary=f"Ollama 生成: {title[:100]}",
        storage_type=StorageType.INLINE,
    )
    return ref.artifact_id


# ---------------------------------------------------------------------------
# OllamaEmbeddingStore — smart auto-selection
# ---------------------------------------------------------------------------

_embedding_store_cache: object | None = None
_embedding_checked: bool = False


async def get_rag_store():
    """Get the best available RAG store.

    Returns OllamaEmbeddingStore if an embedding model is available,
    otherwise falls back to the standard TF-IDF LocalVectorStore.
    """
    global _embedding_store_cache, _embedding_checked

    if _embedding_checked and _embedding_store_cache is not None:
        return _embedding_store_cache

    from app.providers.local_rag import LocalVectorStore, OllamaEmbeddingStore

    try:
        from app.providers.ollama_provider import ollama_provider

        embed_store = OllamaEmbeddingStore(
            ollama_url=ollama_provider.base_url,
        )
        has_embedding = await embed_store.check_embedding_support()

        if has_embedding:
            logger.info("Using OllamaEmbeddingStore (high-quality embeddings)")
            _embedding_store_cache = embed_store
            _embedding_checked = True
            return embed_store
    except Exception as exc:
        logger.debug("OllamaEmbeddingStore check failed: %s", exc)

    # Fallback to TF-IDF
    from app.providers.local_rag import local_rag
    _embedding_store_cache = local_rag
    _embedding_checked = True
    return local_rag


def reset_embedding_cache() -> None:
    """Reset the embedding store cache (useful when Ollama state changes)."""
    global _embedding_store_cache, _embedding_checked
    _embedding_store_cache = None
    _embedding_checked = False


# ---------------------------------------------------------------------------
# Cost ledger helper
# ---------------------------------------------------------------------------

async def record_ollama_cost(
    db: AsyncSession,
    company_id: str | uuid.UUID,
    model: str,
    tokens_input: int,
    tokens_output: int,
) -> None:
    """Record Ollama usage in the cost ledger.

    Ollama is always free ($0.00) but we still track usage for reporting.
    """
    try:
        from app.audit.logger import record_audit_event

        await record_audit_event(
            db=db,
            company_id=company_id,
            event_type="cost.ollama.recorded",
            target_type="cost_ledger",
            details={
                "model": model,
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "cost_usd": 0.0,
                "provider": "ollama",
            },
        )
    except Exception as exc:
        logger.debug("Cost ledger recording failed: %s", exc)
