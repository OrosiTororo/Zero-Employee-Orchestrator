"""Review Assistant Skill — レビュー・品質チェックを補助する.

タスク成果物に対するレビューコメントの生成、
チェックリストの作成、承認判断の補助を行う。
Judge Layer と連携して品質基準を確認する。
"""

from dataclasses import dataclass, field


@dataclass
class ReviewCheckItem:
    """レビューチェック項目."""

    name: str
    description: str
    passed: bool | None = None  # None = 未チェック
    notes: str = ""


@dataclass
class ReviewReport:
    """レビュー報告書."""

    task_id: str
    reviewer_type: str  # "auto" or "human"
    checklist: list[ReviewCheckItem]
    overall_score: float = 0.0  # 0.0 - 1.0
    summary: str = ""
    recommendations: list[str] = field(default_factory=list)
    approval_recommended: bool = False


# デフォルトのレビューチェックリスト (タスクタイプ別)
DEFAULT_CHECKLISTS: dict[str, list[dict[str, str]]] = {
    "implementation": [
        {"name": "correctness", "description": "実装がSpec要件を満たしているか"},
        {"name": "error_handling", "description": "エラーハンドリングが適切か"},
        {"name": "security", "description": "セキュリティ上の問題がないか"},
        {"name": "performance", "description": "パフォーマンス上の懸念がないか"},
        {"name": "test_coverage", "description": "テストが十分にカバーしているか"},
        {"name": "documentation", "description": "ドキュメントが更新されているか"},
    ],
    "analysis": [
        {"name": "completeness", "description": "分析が網羅的か"},
        {"name": "accuracy", "description": "情報の正確性が確認されているか"},
        {"name": "actionability", "description": "実行可能な提案が含まれているか"},
    ],
    "design": [
        {"name": "feasibility", "description": "実現可能な設計か"},
        {"name": "scalability", "description": "スケーラビリティが考慮されているか"},
        {"name": "maintainability", "description": "保守性が考慮されているか"},
        {"name": "consistency", "description": "既存アーキテクチャとの整合性があるか"},
    ],
}


def generate_review_checklist(task_type: str) -> list[ReviewCheckItem]:
    """タスクタイプに応じたレビューチェックリストを生成する."""
    items = DEFAULT_CHECKLISTS.get(task_type, DEFAULT_CHECKLISTS["implementation"])
    return [
        ReviewCheckItem(name=item["name"], description=item["description"])
        for item in items
    ]


def evaluate_checklist(checklist: list[ReviewCheckItem]) -> float:
    """チェックリストの評価スコアを計算する (0.0 - 1.0)."""
    checked = [item for item in checklist if item.passed is not None]
    if not checked:
        return 0.0
    passed = sum(1 for item in checked if item.passed)
    return passed / len(checked)


def create_review_report(
    task_id: str,
    task_type: str,
    checklist_results: dict[str, bool] | None = None,
) -> ReviewReport:
    """レビュー報告書を作成する.

    Args:
        task_id: タスクID
        task_type: タスクタイプ
        checklist_results: チェック結果 {チェック名: 合否}
    """
    checklist = generate_review_checklist(task_type)

    if checklist_results:
        for item in checklist:
            if item.name in checklist_results:
                item.passed = checklist_results[item.name]

    score = evaluate_checklist(checklist)
    recommendations = []

    failed_items = [item for item in checklist if item.passed is False]
    for item in failed_items:
        recommendations.append(f"「{item.description}」を改善してください")

    unchecked = [item for item in checklist if item.passed is None]
    if unchecked:
        recommendations.append(
            f"{len(unchecked)} 件のチェック項目が未確認です"
        )

    return ReviewReport(
        task_id=task_id,
        reviewer_type="auto",
        checklist=checklist,
        overall_score=round(score, 2),
        summary=f"レビュースコア: {score:.1%} ({len(failed_items)} 件の要改善項目)",
        recommendations=recommendations,
        approval_recommended=score >= 0.8 and not failed_items,
    )


def review_to_markdown(report: ReviewReport) -> str:
    """レビュー報告書を Markdown 形式に変換する."""
    lines = [
        "# レビュー報告書",
        "",
        f"**Task ID:** {report.task_id}",
        f"**レビュー種別:** {report.reviewer_type}",
        f"**総合スコア:** {report.overall_score:.0%}",
        f"**承認推奨:** {'✅ はい' if report.approval_recommended else '❌ いいえ'}",
        "",
        "## チェックリスト",
        "",
    ]

    for item in report.checklist:
        if item.passed is True:
            icon = "✅"
        elif item.passed is False:
            icon = "❌"
        else:
            icon = "⬜"
        lines.append(f"- {icon} **{item.name}:** {item.description}")
        if item.notes:
            lines.append(f"  - {item.notes}")

    lines.append("")

    if report.recommendations:
        lines.append("## 推奨事項")
        for rec in report.recommendations:
            lines.append(f"- {rec}")
        lines.append("")

    return "\n".join(lines)
