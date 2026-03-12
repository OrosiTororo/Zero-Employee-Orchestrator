"""Plan Writer Skill — Spec から実行計画 (Plan) を生成する.

仕様書を受け取り、タスク DAG として分解された実行計画を生成する。
各タスクの依存関係・スキル割当・見積もりを含む。
"""

from dataclasses import dataclass, field


@dataclass
class PlannedTask:
    """計画されたタスク."""

    sequence_no: int
    title: str
    description: str
    task_type: str
    skill_name: str | None = None
    depends_on: list[int] = field(default_factory=list)
    estimated_minutes: int = 30
    requires_approval: bool = False


@dataclass
class ExecutionPlan:
    """タスク DAG としての実行計画."""

    spec_id: str
    version: int
    tasks: list[PlannedTask]
    estimated_total_minutes: int = 0
    parallel_groups: list[list[int]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.estimated_total_minutes:
            self.estimated_total_minutes = sum(t.estimated_minutes for t in self.tasks)


def generate_plan_template(
    spec_id: str,
    goal: str,
    scope: str,
    sections: list[dict[str, str]] | None = None,
    file_context: str = "",
    attachments: list[dict] | None = None,
) -> ExecutionPlan:
    """Spec 情報から実行計画テンプレートを生成する.

    実際の運用では LLM を使ってタスク分解するが、
    このスキルは基本的な計画構造を提供する。

    Args:
        spec_id: 仕様書 ID
        goal: 目標
        scope: スコープ
        sections: 仕様書のセクションリスト
        file_context: 添付ファイルから抽出されたテキストコンテキスト
        attachments: 添付ファイルメタデータのリスト
    """
    tasks = [
        PlannedTask(
            sequence_no=1,
            title="要件分析",
            description=f"仕様「{goal}」の詳細分析",
            task_type="analysis",
            skill_name="spec_writer",
        ),
        PlannedTask(
            sequence_no=2,
            title="設計",
            description="アーキテクチャ・実装設計",
            task_type="design",
            depends_on=[1],
        ),
        PlannedTask(
            sequence_no=3,
            title="実装",
            description=scope or "メインの実装作業",
            task_type="implementation",
            depends_on=[2],
        ),
        PlannedTask(
            sequence_no=4,
            title="テスト",
            description="ユニットテスト・統合テスト",
            task_type="testing",
            depends_on=[3],
        ),
        PlannedTask(
            sequence_no=5,
            title="レビュー・承認",
            description="品質チェックと人間レビュー",
            task_type="review",
            depends_on=[4],
            requires_approval=True,
        ),
    ]

    return ExecutionPlan(
        spec_id=spec_id,
        version=1,
        tasks=tasks,
        parallel_groups=[[1], [2], [3], [4], [5]],
    )


def plan_to_markdown(plan: ExecutionPlan) -> str:
    """実行計画を Markdown 形式に変換する."""
    lines = [
        "# 実行計画",
        "",
        f"**Spec ID:** {plan.spec_id}",
        f"**Version:** {plan.version}",
        f"**推定合計時間:** {plan.estimated_total_minutes} 分",
        "",
        "## タスク一覧",
        "",
    ]

    for task in plan.tasks:
        deps = f" (依存: {task.depends_on})" if task.depends_on else ""
        approval = " 🔒" if task.requires_approval else ""
        lines.append(f"### {task.sequence_no}. {task.title}{approval}")
        lines.append(f"- **種別:** {task.task_type}")
        lines.append(f"- **説明:** {task.description}")
        if task.skill_name:
            lines.append(f"- **スキル:** {task.skill_name}")
        lines.append(f"- **見積もり:** {task.estimated_minutes} 分{deps}")
        lines.append("")

    return "\n".join(lines)
