"""Design Interview Layer (Layer 2).

Handles requirement elicitation through natural language conversation.
Generates structured specs from user intent.
Supports file attachments (text, images) as context for spec generation.

Experience Memory フィードバック:
Design Interview の目的入力時に、Experience Memory と Failure Taxonomy から
過去の類似失敗パターンを検索し、「この種の目的設定は過去に○○の理由で失敗
している」というフィードバックを自動提供する。
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
    """Interview に添付されたファイル."""

    filename: str
    content_type: str  # MIME type
    extracted_text: str = ""  # テキスト抽出結果
    file_path: str = ""  # サーバー上の保存パス
    size_bytes: int = 0
    description: str = ""  # ユーザーによるファイルの説明


@dataclass
class InterviewQuestion:
    question: str
    category: str  # "objective" | "constraint" | "acceptance" | "risk" | "priority"
    required: bool = True
    answered: bool = False
    answer: str | None = None


@dataclass
class FailureWarning:
    """Experience Memory / Failure Taxonomy から検出された過去の失敗警告."""

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

    @property
    def is_complete(self) -> bool:
        return all(q.answered for q in self.questions if q.required)

    def add_answer(self, question_index: int, answer: str) -> None:
        if 0 <= question_index < len(self.questions):
            self.questions[question_index].answered = True
            self.questions[question_index].answer = answer
            self.answers[self.questions[question_index].question] = answer

    def add_attachment(self, attachment: FileAttachment) -> None:
        """ファイルを添付する."""
        self.attachments.append(attachment)

    def get_attachments_context(self) -> str:
        """添付ファイルのテキストをコンテキストとして結合する."""
        if not self.attachments:
            return ""
        parts: list[str] = []
        for att in self.attachments:
            header = f"[添付ファイル: {att.filename}]"
            if att.description:
                header += f" ({att.description})"
            text = att.extracted_text or "(テキスト抽出不可)"
            parts.append(f"{header}\n{text}")
        return "\n\n---\n\n".join(parts)

    def get_pending_questions(self) -> list[InterviewQuestion]:
        return [q for q in self.questions if not q.answered and q.required]


# Standard interview template for new business requests
STANDARD_INTERVIEW_TEMPLATE = [
    InterviewQuestion(
        question="この業務の最終的な目的は何ですか？",
        category="objective",
    ),
    InterviewQuestion(
        question="守るべき制約条件はありますか？（予算、期限、品質基準など）",
        category="constraint",
    ),
    InterviewQuestion(
        question="完了条件（受け入れ基準）は何ですか？",
        category="acceptance",
    ),
    InterviewQuestion(
        question="想定されるリスクや注意点はありますか？",
        category="risk",
        required=False,
    ),
    InterviewQuestion(
        question="優先順位はどの程度ですか？（高/中/低）",
        category="priority",
    ),
    InterviewQuestion(
        question="外部サービスへの接続や送信は必要ですか？",
        category="constraint",
    ),
    InterviewQuestion(
        question="人間の承認が必要な工程はありますか？",
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
    """Failure Taxonomy から目的に関連する頻発障害パターンを検索する.

    Args:
        objective: ユーザーが入力した業務目的テキスト
        failure_taxonomy: Failure Taxonomy インスタンス（None の場合はグローバルを使用）

    Returns:
        検出された失敗警告のリスト
    """
    if failure_taxonomy is None:
        from app.orchestration.failure_taxonomy import (
            failure_taxonomy as global_taxonomy,
        )

        failure_taxonomy = global_taxonomy

    warnings: list[FailureWarning] = []
    objective_lower = objective.lower()

    # 頻発障害パターン（2回以上発生）を取得
    frequent_failures = failure_taxonomy.get_frequent_failures(min_count=2)
    for record in frequent_failures:
        # 目的テキストとの関連性チェック（カテゴリ・説明のキーワードマッチ）
        desc_lower = record.description.lower()
        subcat_lower = record.subcategory.lower()
        prevention_lower = record.prevention_strategy.lower()

        # 目的テキストに障害の説明・サブカテゴリ・予防策のキーワードが含まれるか
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
    """Experience Memory (DB) から目的に関連する失敗パターンを検索する.

    Args:
        objective: ユーザーが入力した業務目的テキスト
        db: AsyncSession インスタンス
        company_id: 会社 ID

    Returns:
        検出された失敗警告のリスト
    """
    from app.orchestration.experience_memory import PersistentExperienceMemory

    memory = PersistentExperienceMemory(db, company_id)
    warnings: list[FailureWarning] = []

    # 頻発する障害パターンを取得
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
    """クエリとターゲットテキスト群のキーワード重複スコアを計算する."""
    query_words = set(query.split())
    # 短すぎる単語（助詞など）を除外
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
    """失敗警告に基づいて動的な追加質問を Interview セッションに注入する.

    Args:
        session: Interview セッション
        warnings: 検出された失敗警告のリスト

    Returns:
        追加された質問のリスト
    """
    session.failure_warnings.extend(warnings)
    added_questions: list[InterviewQuestion] = []

    for warning in warnings:
        question_text = (
            f"過去に類似の業務で「{warning.subcategory}」の問題が "
            f"{warning.occurrence_count} 回発生しています"
            f"（回復成功率: {warning.recovery_success_rate:.0%}）。"
            f"予防策: {warning.prevention_strategy} — "
            f"この点について対策は検討済みですか？"
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
            "Interview %s に %d 件の失敗パターン警告を注入しました",
            session.ticket_id,
            len(warnings),
        )

    return added_questions


def format_failure_feedback(warnings: list[FailureWarning]) -> str:
    """失敗警告をユーザー向けフィードバックテキストとして整形する."""
    if not warnings:
        return ""

    lines = ["⚠ 過去の失敗パターンに基づくフィードバック:"]
    for i, w in enumerate(warnings, 1):
        lines.append(
            f"\n{i}. [{w.category}/{w.subcategory}] "
            f"{w.description}\n"
            f"   発生回数: {w.occurrence_count} 回 / "
            f"回復成功率: {w.recovery_success_rate:.0%}\n"
            f"   予防策: {w.prevention_strategy}"
        )
    return "\n".join(lines)


def generate_spec_from_interview(session: InterviewSession) -> dict:
    """Convert completed interview answers into a structured spec.

    添付ファイルがある場合、テキスト内容を仕様のコンテキストとして統合する。
    失敗警告がある場合、リスクノートとして統合する。
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

    # 失敗警告をリスクノートに統合
    failure_feedback = format_failure_feedback(session.failure_warnings)
    if failure_feedback:
        risks.append(failure_feedback)

    # 添付ファイルからのコンテキストを統合
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

    # 失敗警告のサマリーを追加
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
