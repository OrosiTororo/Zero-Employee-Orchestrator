"""Design Interview Layer (Layer 2).

Handles requirement elicitation through natural language conversation.
Generates structured specs from user intent.
Supports file attachments (text, images) as context for spec generation.
"""

from dataclasses import dataclass, field


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
class InterviewSession:
    ticket_id: str
    questions: list[InterviewQuestion] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)
    attachments: list[FileAttachment] = field(default_factory=list)
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


def generate_spec_from_interview(session: InterviewSession) -> dict:
    """Convert completed interview answers into a structured spec.

    添付ファイルがある場合、テキスト内容を仕様のコンテキストとして統合する。
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

    return result
