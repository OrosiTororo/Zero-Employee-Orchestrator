"""State & Memory Layer (Layer 7) - State machines, Experience Memory, Failure Taxonomy."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class MemoryType(str, Enum):
    CONVERSATION = "conversation_log"
    REUSABLE = "reusable_improvement"
    EXPERIMENTAL = "experimental_knowledge"
    VERIFIED = "verified_knowledge"


@dataclass
class ExperienceMemoryEntry:
    """A unit of reusable knowledge derived from execution history."""
    id: str
    memory_type: MemoryType
    category: str  # task_type, plugin_type, domain
    title: str
    content: str
    source_ticket_id: str | None = None
    source_task_id: str | None = None
    approved_by: str | None = None
    conditions: dict = field(default_factory=dict)
    effectiveness_score: float = 0.0
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class FailureTaxonomyEntry:
    """Classification of a failure for learning and prevention."""
    category: str
    subcategory: str
    description: str
    prevention_strategy: str
    occurrence_count: int = 1
    last_occurred: str = ""
    recovery_success_rate: float = 0.0


class ExperienceMemory:
    """Manages reusable knowledge across execution history.

    Separates improvement knowledge by layer:
    - Experience Memory: successful patterns
    - Failure Taxonomy: failure classification and prevention
    - Policy Memory: approval conditions, prohibitions
    - Skill Improvement Memory: per-skill improvements
    - Plugin Operation Memory: per-plugin operational know-how
    """

    def __init__(self) -> None:
        self.entries: list[ExperienceMemoryEntry] = []
        self.failures: list[FailureTaxonomyEntry] = []

    def add_success_pattern(
        self,
        title: str,
        content: str,
        category: str,
        source_ticket_id: str | None = None,
    ) -> ExperienceMemoryEntry:
        entry = ExperienceMemoryEntry(
            id=f"exp-{len(self.entries)}",
            memory_type=MemoryType.REUSABLE,
            category=category,
            title=title,
            content=content,
            source_ticket_id=source_ticket_id,
        )
        self.entries.append(entry)
        return entry

    def add_failure(
        self,
        category: str,
        subcategory: str,
        description: str,
        prevention_strategy: str,
    ) -> FailureTaxonomyEntry:
        # Check for existing entry
        for f in self.failures:
            if f.category == category and f.subcategory == subcategory:
                f.occurrence_count += 1
                f.last_occurred = datetime.now(timezone.utc).isoformat()
                return f

        entry = FailureTaxonomyEntry(
            category=category,
            subcategory=subcategory,
            description=description,
            prevention_strategy=prevention_strategy,
            last_occurred=datetime.now(timezone.utc).isoformat(),
        )
        self.failures.append(entry)
        return entry

    def search(self, query: str, category: str | None = None) -> list[ExperienceMemoryEntry]:
        results = []
        query_lower = query.lower()
        for entry in self.entries:
            if category and entry.category != category:
                continue
            if query_lower in entry.title.lower() or query_lower in entry.content.lower():
                results.append(entry)
        return results

    def get_frequent_failures(self, min_count: int = 2) -> list[FailureTaxonomyEntry]:
        return [f for f in self.failures if f.occurrence_count >= min_count]


# Global experience memory instance
experience_memory = ExperienceMemory()
