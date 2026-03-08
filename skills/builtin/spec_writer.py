"""Spec Writer Skill — Ticket から仕様書 (Spec) を生成する.

Design Interview の結果を受け取り、構造化された仕様書を生成する。
仕様書は Goal → Scope → 制約 → 成功基準 の形式で出力する。
"""

from dataclasses import dataclass, field


@dataclass
class SpecSection:
    """仕様書のセクション."""

    title: str
    content: str
    subsections: list["SpecSection"] = field(default_factory=list)


@dataclass
class SpecDocument:
    """構造化された仕様書."""

    ticket_id: str
    version: int
    goal: str
    scope: str
    constraints: list[str]
    success_criteria: list[str]
    sections: list[SpecSection] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)


def generate_spec_template(
    ticket_id: str,
    title: str,
    description: str,
    interview_notes: list[str] | None = None,
) -> SpecDocument:
    """Ticket 情報から仕様書テンプレートを生成する.

    実際の運用では LLM を使って内容を充実させるが、
    このスキルはテンプレートの構造を提供する。
    """
    return SpecDocument(
        ticket_id=ticket_id,
        version=1,
        goal=title,
        scope=description or "",
        constraints=[],
        success_criteria=[],
        sections=[
            SpecSection(title="概要", content=description or ""),
            SpecSection(title="要件", content="", subsections=[
                SpecSection(title="機能要件", content=""),
                SpecSection(title="非機能要件", content=""),
            ]),
            SpecSection(title="設計方針", content=""),
            SpecSection(title="テスト計画", content=""),
        ],
        non_goals=[],
    )


def spec_to_markdown(spec: SpecDocument) -> str:
    """仕様書を Markdown 形式に変換する."""
    lines = [
        f"# 仕様書: {spec.goal}",
        "",
        f"**Ticket ID:** {spec.ticket_id}",
        f"**Version:** {spec.version}",
        "",
        "## スコープ",
        spec.scope or "_未定義_",
        "",
    ]

    if spec.constraints:
        lines.append("## 制約")
        for c in spec.constraints:
            lines.append(f"- {c}")
        lines.append("")

    if spec.success_criteria:
        lines.append("## 成功基準")
        for s in spec.success_criteria:
            lines.append(f"- {s}")
        lines.append("")

    if spec.non_goals:
        lines.append("## 非スコープ")
        for n in spec.non_goals:
            lines.append(f"- {n}")
        lines.append("")

    for section in spec.sections:
        lines.append(f"## {section.title}")
        lines.append(section.content or "_TBD_")
        lines.append("")
        for sub in section.subsections:
            lines.append(f"### {sub.title}")
            lines.append(sub.content or "_TBD_")
            lines.append("")

    return "\n".join(lines)
