"""Design Interview Layer (Layer 2).

Handles requirement elicitation through natural language conversation.
Generates structured specs from user intent.
Supports file attachments (text, images) as context for spec generation.

Experience Memory feedback:
During objective input in Design Interview, automatically searches for similar
past failure patterns from Experience Memory and Failure Taxonomy, providing
feedback such as "this type of objective has failed in the past due to X reason".
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.orchestration.failure_taxonomy import FailureTaxonomy

logger = logging.getLogger(__name__)


@dataclass
class FileAttachment:
    """File attached to an interview."""

    filename: str
    content_type: str  # MIME type
    extracted_text: str = ""  # Extracted text result
    file_path: str = ""  # Storage path on server
    size_bytes: int = 0
    description: str = ""  # User-provided file description


@dataclass
class InterviewQuestion:
    question: str
    category: str  # "objective" | "constraint" | "acceptance" | "risk" | "priority"
    required: bool = True
    answered: bool = False
    answer: str | None = None


@dataclass
class FailureWarning:
    """Past failure warning detected from Experience Memory / Failure Taxonomy."""

    category: str
    subcategory: str
    description: str
    prevention_strategy: str
    occurrence_count: int
    recovery_success_rate: float
    source: str  # "experience_memory" | "failure_taxonomy"


@dataclass
class InterviewSession:
    ticket_id: str
    questions: list[InterviewQuestion] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)
    attachments: list[FileAttachment] = field(default_factory=list)
    failure_warnings: list[FailureWarning] = field(default_factory=list)
    status: str = "in_progress"  # in_progress | completed | cancelled
    spec_text: str = ""  # Generated spec from interview answers
    generated_plan: dict | None = None  # DAG plan for execution

    @property
    def is_complete(self) -> bool:
        return all(q.answered for q in self.questions if q.required)

    def add_answer(self, question_index: int, answer: str) -> None:
        if 0 <= question_index < len(self.questions):
            self.questions[question_index].answered = True
            self.questions[question_index].answer = answer
            self.answers[self.questions[question_index].question] = answer

    def add_attachment(self, attachment: FileAttachment) -> None:
        """Attach a file."""
        self.attachments.append(attachment)

    def get_attachments_context(self) -> str:
        """Combine attached file text as context."""
        if not self.attachments:
            return ""
        parts: list[str] = []
        for att in self.attachments:
            header = f"[Attachment: {att.filename}]"
            if att.description:
                header += f" ({att.description})"
            text = att.extracted_text or "(text extraction not available)"
            parts.append(f"{header}\n{text}")
        return "\n\n---\n\n".join(parts)

    def get_pending_questions(self) -> list[InterviewQuestion]:
        return [q for q in self.questions if not q.answered and q.required]


# Standard interview template for new business requests
STANDARD_INTERVIEW_TEMPLATE = [
    InterviewQuestion(
        question="What is the ultimate objective of this task?",
        category="objective",
    ),
    InterviewQuestion(
        question="Are there any constraints to follow? (budget, deadlines, quality standards, etc.)",
        category="constraint",
    ),
    InterviewQuestion(
        question="What are the completion criteria (acceptance criteria)?",
        category="acceptance",
    ),
    InterviewQuestion(
        question="Are there any expected risks or concerns?",
        category="risk",
        required=False,
    ),
    InterviewQuestion(
        question="What is the priority level? (high/medium/low)",
        category="priority",
    ),
    InterviewQuestion(
        question="Is connection or sending to external services required?",
        category="constraint",
    ),
    InterviewQuestion(
        question="Are there any steps that require human approval?",
        category="acceptance",
    ),
]


def create_interview_session(ticket_id: str) -> InterviewSession:
    """Create a new interview session with standard questions."""
    return InterviewSession(
        ticket_id=ticket_id,
        questions=[
            InterviewQuestion(
                question=q.question,
                category=q.category,
                required=q.required,
            )
            for q in STANDARD_INTERVIEW_TEMPLATE
        ],
    )


def gather_failure_feedback_from_taxonomy(
    objective: str,
    failure_taxonomy: FailureTaxonomy | None = None,
) -> list[FailureWarning]:
    """Search for frequent failure patterns related to the objective from Failure Taxonomy.

    Args:
        objective: Business objective text entered by the user
        failure_taxonomy: Failure Taxonomy instance (uses global if None)

    Returns:
        List of detected failure warnings
    """
    if failure_taxonomy is None:
        from app.orchestration.failure_taxonomy import (
            failure_taxonomy as global_taxonomy,
        )

        failure_taxonomy = global_taxonomy

    warnings: list[FailureWarning] = []
    objective_lower = objective.lower()

    # Get frequent failure patterns (occurred 2+ times)
    frequent_failures = failure_taxonomy.get_frequent_failures(min_count=2)
    for record in frequent_failures:
        # Relevance check with objective text (keyword match on category/description)
        desc_lower = record.description.lower()
        subcat_lower = record.subcategory.lower()
        prevention_lower = record.prevention_strategy.lower()

        # Check if objective text contains keywords from failure description/subcategory/prevention
        relevance = _compute_keyword_relevance(
            objective_lower, [desc_lower, subcat_lower, prevention_lower]
        )
        if relevance > 0:
            warnings.append(
                FailureWarning(
                    category=record.category.value
                    if hasattr(record.category, "value")
                    else str(record.category),
                    subcategory=record.subcategory,
                    description=record.description,
                    prevention_strategy=record.prevention_strategy,
                    occurrence_count=record.occurrence_count,
                    recovery_success_rate=record.recovery_success_rate,
                    source="failure_taxonomy",
                )
            )

    return warnings


async def gather_failure_feedback_from_memory(
    objective: str,
    db: AsyncSession,
    company_id: str,
) -> list[FailureWarning]:
    """Search for failure patterns related to the objective from Experience Memory (DB).

    Args:
        objective: Business objective text entered by the user
        db: AsyncSession instance
        company_id: Company ID

    Returns:
        List of detected failure warnings
    """
    from app.orchestration.experience_memory import PersistentExperienceMemory

    memory = PersistentExperienceMemory(db, company_id)
    warnings: list[FailureWarning] = []

    # Get frequent failure patterns
    frequent = await memory.get_frequent_failures(min_count=2)
    for record in frequent:
        desc_lower = record.description.lower()
        subcat_lower = record.subcategory.lower()
        objective_lower = objective.lower()

        relevance = _compute_keyword_relevance(objective_lower, [desc_lower, subcat_lower])
        if relevance > 0:
            warnings.append(
                FailureWarning(
                    category=record.category,
                    subcategory=record.subcategory,
                    description=record.description,
                    prevention_strategy=record.prevention_strategy,
                    occurrence_count=record.occurrence_count,
                    recovery_success_rate=record.recovery_success_rate,
                    source="experience_memory",
                )
            )

    return warnings


def _compute_keyword_relevance(query: str, targets: list[str]) -> int:
    """Calculate keyword overlap score between query and target texts."""
    query_words = set(query.split())
    # Exclude words that are too short (particles, etc.)
    query_words = {w for w in query_words if len(w) >= 2}
    score = 0
    for target in targets:
        target_words = set(target.split())
        overlap = query_words & target_words
        score += len(overlap)
    return score


def inject_failure_warnings(
    session: InterviewSession,
    warnings: list[FailureWarning],
) -> list[InterviewQuestion]:
    """Inject dynamic follow-up questions into the Interview session based on failure warnings.

    Args:
        session: Interview session
        warnings: List of detected failure warnings

    Returns:
        List of added questions
    """
    session.failure_warnings.extend(warnings)
    added_questions: list[InterviewQuestion] = []

    for warning in warnings:
        question_text = (
            f'In similar past tasks, the "{warning.subcategory}" issue occurred '
            f"{warning.occurrence_count} time(s)"
            f" (recovery success rate: {warning.recovery_success_rate:.0%})."
            f" Prevention: {warning.prevention_strategy} — "
            f"Have you considered countermeasures for this?"
        )
        new_q = InterviewQuestion(
            question=question_text,
            category="risk",
            required=False,
        )
        session.questions.append(new_q)
        added_questions.append(new_q)

    if warnings:
        logger.info(
            "Injected %d failure pattern warning(s) into Interview %s",
            len(warnings),
            session.ticket_id,
        )

    return added_questions


def format_failure_feedback(warnings: list[FailureWarning]) -> str:
    """Format failure warnings as user-facing feedback text."""
    if not warnings:
        return ""

    lines = ["⚠ Feedback based on past failure patterns:"]
    for i, w in enumerate(warnings, 1):
        lines.append(
            f"\n{i}. [{w.category}/{w.subcategory}] "
            f"{w.description}\n"
            f"   Occurrences: {w.occurrence_count} / "
            f"Recovery success rate: {w.recovery_success_rate:.0%}\n"
            f"   Prevention: {w.prevention_strategy}"
        )
    return "\n".join(lines)


def generate_spec_from_interview(session: InterviewSession) -> dict:
    """Convert completed interview answers into a structured spec.

    If attachments exist, integrates text content as specification context.
    If failure warnings exist, integrates them as risk notes.
    """
    objective = ""
    constraints = []
    acceptance_criteria = []
    risks = []

    for q in session.questions:
        if q.answer:
            if q.category == "objective":
                objective = q.answer
            elif q.category == "constraint":
                constraints.append(q.answer)
            elif q.category == "acceptance":
                acceptance_criteria.append(q.answer)
            elif q.category == "risk":
                risks.append(q.answer)

    # Integrate failure warnings into risk notes
    failure_feedback = format_failure_feedback(session.failure_warnings)
    if failure_feedback:
        risks.append(failure_feedback)

    # Integrate context from attachments
    file_context = session.get_attachments_context()
    attachment_summaries = []
    if session.attachments:
        for att in session.attachments:
            attachment_summaries.append(
                {
                    "filename": att.filename,
                    "content_type": att.content_type,
                    "size_bytes": att.size_bytes,
                    "description": att.description,
                    "has_text": bool(att.extracted_text),
                }
            )

    result: dict = {
        "objective": objective,
        "constraints_json": {"items": constraints},
        "acceptance_criteria_json": {"items": acceptance_criteria},
        "risk_notes": "\n".join(risks) if risks else None,
    }

    if file_context:
        result["file_context"] = file_context
        result["attachments"] = attachment_summaries

    # Add failure warning summary
    if session.failure_warnings:
        result["failure_warnings"] = [
            {
                "category": w.category,
                "subcategory": w.subcategory,
                "description": w.description,
                "prevention_strategy": w.prevention_strategy,
                "occurrence_count": w.occurrence_count,
                "recovery_success_rate": w.recovery_success_rate,
                "source": w.source,
            }
            for w in session.failure_warnings
        ]

    return result
