"""Knowledge Refresh — Addressing context window limitations.

Based on Zero-Employee Orchestrator.md sections 5 and 11.4.2, provides history
management and information re-retrieval mechanisms to handle context window limits.

Knowledge Pipeline stages:
1. Retrieval
2. Extraction
3. Splitting
4. Indexing
5. Search
6. Citation / Summarization
7. Promotion to verified knowledge or rejection
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class KnowledgeStatus(str, Enum):
    """Knowledge status."""

    RAW = "raw"  # Unprocessed
    EXTRACTED = "extracted"  # Extracted
    INDEXED = "indexed"  # Indexed
    VERIFIED = "verified"  # Verified
    EXPERIMENTAL = "experimental"  # Experimental
    REJECTED = "rejected"  # Rejected


class KnowledgeType(str, Enum):
    """Knowledge type (sections 8.0.1, 8.5)."""

    CONVERSATION_LOG = "conversation_log"  # Conversation history
    REUSABLE_IMPROVEMENT = "reusable_improvement"  # Reusable improvement knowledge
    EXPERIMENTAL = "experimental_knowledge"  # Experimental knowledge
    VERIFIED = "verified_knowledge"  # Verified knowledge
    EXPERIENCE_MEMORY = "experience_memory"  # Success patterns
    FAILURE_TAXONOMY = "failure_taxonomy"  # Failure classification
    POLICY_MEMORY = "policy_memory"  # Approval conditions / prohibitions
    SKILL_IMPROVEMENT = "skill_improvement"  # Skill improvement knowledge
    PLUGIN_OPERATION = "plugin_operation"  # Plugin operational know-how


@dataclass
class KnowledgeEntry:
    """Knowledge entry."""

    id: str
    title: str
    content: str
    knowledge_type: KnowledgeType
    status: KnowledgeStatus = KnowledgeStatus.RAW
    source: str = ""
    tags: list[str] = field(default_factory=list)
    approved_by: str | None = None
    effective_conditions: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class KnowledgeRefreshResult:
    """Knowledge Refresh result."""

    context_entries: list[KnowledgeEntry]
    total_tokens_estimated: int
    truncated: bool
    summary: str


class KnowledgeStore:
    """Knowledge storage and search.

    Stores improvement knowledge separated by purpose (section 8.5):
    - Experience Memory: Successful execution patterns
    - Failure Taxonomy: Failure classification, recurrence prevention
    - Policy Memory: Approval conditions, prohibitions
    - Skill Improvement Memory: Skill improvement knowledge
    - Plugin Operation Memory: Operational know-how
    """

    def __init__(self) -> None:
        self._entries: list[KnowledgeEntry] = []

    def add(self, entry: KnowledgeEntry) -> None:
        self._entries.append(entry)

    def search(
        self,
        query: str,
        *,
        knowledge_type: KnowledgeType | None = None,
        status: KnowledgeStatus | None = None,
        limit: int = 10,
    ) -> list[KnowledgeEntry]:
        """Search knowledge."""
        results = []
        query_lower = query.lower()
        for entry in self._entries:
            if knowledge_type and entry.knowledge_type != knowledge_type:
                continue
            if status and entry.status != status:
                continue
            if query_lower in entry.title.lower() or query_lower in entry.content.lower():
                results.append(entry)
            if len(results) >= limit:
                break
        return results

    def promote_to_verified(self, entry_id: str, approved_by: str) -> bool:
        """Promote knowledge to verified status."""
        for entry in self._entries:
            if entry.id == entry_id:
                entry.status = KnowledgeStatus.VERIFIED
                entry.approved_by = approved_by
                entry.updated_at = datetime.now(UTC)
                return True
        return False

    def reject(self, entry_id: str, reason: str = "") -> bool:
        """Reject knowledge."""
        for entry in self._entries:
            if entry.id == entry_id:
                entry.status = KnowledgeStatus.REJECTED
                entry.updated_at = datetime.now(UTC)
                return True
        return False

    def get_by_type(self, knowledge_type: KnowledgeType) -> list[KnowledgeEntry]:
        return [e for e in self._entries if e.knowledge_type == knowledge_type]


def refresh_context(
    store: KnowledgeStore,
    task_context: str,
    max_tokens: int = 8000,
) -> KnowledgeRefreshResult:
    """Refresh knowledge needed for task execution.

    Handles context window limitations by retrieving only relevant knowledge.
    """
    relevant = store.search(task_context, status=KnowledgeStatus.VERIFIED, limit=20)

    total_tokens = 0
    selected: list[KnowledgeEntry] = []
    truncated = False

    for entry in relevant:
        estimated = len(entry.content) // 4  # Simple token estimation
        if total_tokens + estimated > max_tokens:
            truncated = True
            break
        selected.append(entry)
        total_tokens += estimated

    return KnowledgeRefreshResult(
        context_entries=selected,
        total_tokens_estimated=total_tokens,
        truncated=truncated,
        summary=f"Retrieved {len(selected)} relevant knowledge entries (estimated {total_tokens} tokens)",  # noqa: E501
    )


# Global instance
knowledge_store = KnowledgeStore()
