"""State & Memory Layer (Layer 7) - State machines, Experience Memory, Failure Taxonomy."""

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

# Maximum number of state transition history entries to retain (prevents unbounded memory growth)
_MAX_HISTORY_SIZE = 1000

# ---------------------------------------------------------------------------
# State Machine base
# ---------------------------------------------------------------------------


class StateMachineError(Exception):
    """Exception raised when an invalid state transition is attempted."""


class BaseStateMachine:
    """Generic state machine: validates and executes state transitions based on a transition table."""

    transitions: dict[str, list[str]] = {}

    def __init__(self, initial_state: str, max_history: int = _MAX_HISTORY_SIZE) -> None:
        if initial_state not in self.transitions:
            raise StateMachineError(f"Unknown initial state: {initial_state}")
        self._state = initial_state
        self._history: deque[dict[str, str]] = deque(maxlen=max_history)

    @property
    def state(self) -> str:
        return self._state

    @property
    def history(self) -> list[dict[str, str]]:
        return list(self._history)

    def can_transition(self, target: str) -> bool:
        return target in self.transitions.get(self._state, [])

    def transition(self, target: str, reason: str = "") -> str:
        if not self.can_transition(target):
            raise StateMachineError(
                f"Transition not allowed: {self._state} -> {target} "
                f"(allowed: {self.transitions.get(self._state, [])})"
            )
        old = self._state
        self._state = target
        self._history.append(
            {
                "from": old,
                "to": target,
                "reason": reason,
                "at": datetime.now(UTC).isoformat(),
            }
        )
        return self._state

    def available_transitions(self) -> list[str]:
        return list(self.transitions.get(self._state, []))


class TicketStateMachine(BaseStateMachine):
    """Manage Ticket state transitions."""

    transitions: dict[str, list[str]] = {
        "draft": ["open", "cancelled"],
        "open": ["interviewing", "planning", "cancelled"],
        "interviewing": ["open", "planning", "cancelled"],
        "planning": ["ready", "open", "cancelled"],
        "ready": ["in_progress", "cancelled"],
        "in_progress": ["review", "blocked", "cancelled"],
        "blocked": ["in_progress", "cancelled"],
        "review": ["done", "rework", "cancelled"],
        "rework": ["in_progress", "cancelled"],
        "done": ["closed", "reopened"],
        "reopened": ["in_progress", "cancelled"],
        "closed": ["reopened"],
        "cancelled": [],
    }


class TaskStateMachine(BaseStateMachine):
    """Manage Task state transitions."""

    transitions: dict[str, list[str]] = {
        "pending": ["ready", "cancelled"],
        "ready": ["running", "blocked"],
        "running": ["succeeded", "failed", "awaiting_approval", "blocked"],
        "awaiting_approval": ["running", "cancelled"],
        "blocked": ["ready", "cancelled"],
        "failed": ["retrying", "cancelled"],
        "retrying": ["running", "failed"],
        "succeeded": ["verified", "archived"],
        "verified": ["archived", "rework_requested"],
        "rework_requested": ["ready", "running"],
        "cancelled": [],
        "archived": [],
    }


class ApprovalStateMachine(BaseStateMachine):
    """Manage approval request state transitions."""

    transitions: dict[str, list[str]] = {
        "requested": ["approved", "rejected", "expired", "cancelled"],
        "approved": ["executed"],
        "rejected": ["superseded"],
        "expired": ["requested", "cancelled"],
        "cancelled": [],
        "executed": [],
        "superseded": [],
    }


class AgentStateMachine(BaseStateMachine):
    """Manage Agent state transitions."""

    transitions: dict[str, list[str]] = {
        "provisioning": ["idle", "error"],
        "idle": ["busy", "paused", "decommissioned"],
        "busy": ["idle", "error", "paused"],
        "paused": ["idle", "decommissioned"],
        "error": ["idle", "paused", "decommissioned"],
        "decommissioned": [],
    }


# ---------------------------------------------------------------------------
# Experience Memory
# ---------------------------------------------------------------------------


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
            self.created_at = datetime.now(UTC).isoformat()


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
                f.last_occurred = datetime.now(UTC).isoformat()
                return f

        entry = FailureTaxonomyEntry(
            category=category,
            subcategory=subcategory,
            description=description,
            prevention_strategy=prevention_strategy,
            last_occurred=datetime.now(UTC).isoformat(),
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
