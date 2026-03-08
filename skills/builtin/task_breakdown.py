"""Task Breakdown Skill — 大きなタスクをサブタスクに分解する.

Plan Writer が生成した計画内の個々のタスクを、
実行可能な粒度のサブタスクに分解する。
DAG 依存関係を維持しながら並列実行可能なグループを特定する。
"""

from dataclasses import dataclass, field


@dataclass
class SubTask:
    """分解されたサブタスク."""

    id: str
    parent_task_id: str
    title: str
    description: str
    task_type: str
    sequence_no: int
    depends_on: list[str] = field(default_factory=list)
    estimated_minutes: int = 15
    skill_name: str | None = None
    requires_approval: bool = False


@dataclass
class BreakdownResult:
    """タスク分解結果."""

    parent_task_id: str
    subtasks: list[SubTask]
    parallel_groups: list[list[str]] = field(default_factory=list)
    estimated_total_minutes: int = 0

    def __post_init__(self) -> None:
        if not self.estimated_total_minutes:
            self.estimated_total_minutes = sum(t.estimated_minutes for t in self.subtasks)


def breakdown_task(
    task_id: str,
    title: str,
    description: str,
    task_type: str,
) -> BreakdownResult:
    """タスクをサブタスクに分解するテンプレートを生成.

    実際の運用では LLM を使って適切な粒度に分解するが、
    このスキルはタスクタイプに応じたデフォルト分解を提供する。
    """
    subtasks: list[SubTask] = []

    if task_type == "implementation":
        subtasks = [
            SubTask(
                id=f"{task_id}-1",
                parent_task_id=task_id,
                title=f"{title}: コード実装",
                description="メインのコード実装",
                task_type="coding",
                sequence_no=1,
            ),
            SubTask(
                id=f"{task_id}-2",
                parent_task_id=task_id,
                title=f"{title}: ユニットテスト作成",
                description="ユニットテストの作成",
                task_type="testing",
                sequence_no=2,
                depends_on=[f"{task_id}-1"],
            ),
            SubTask(
                id=f"{task_id}-3",
                parent_task_id=task_id,
                title=f"{title}: ドキュメント更新",
                description="関連ドキュメントの更新",
                task_type="documentation",
                sequence_no=3,
                depends_on=[f"{task_id}-1"],
                estimated_minutes=10,
            ),
        ]
    elif task_type == "analysis":
        subtasks = [
            SubTask(
                id=f"{task_id}-1",
                parent_task_id=task_id,
                title=f"{title}: 情報収集",
                description="関連情報の収集と整理",
                task_type="research",
                sequence_no=1,
                estimated_minutes=20,
            ),
            SubTask(
                id=f"{task_id}-2",
                parent_task_id=task_id,
                title=f"{title}: 分析・まとめ",
                description="収集情報の分析とまとめ",
                task_type="analysis",
                sequence_no=2,
                depends_on=[f"{task_id}-1"],
                estimated_minutes=20,
            ),
        ]
    else:
        # Generic breakdown
        subtasks = [
            SubTask(
                id=f"{task_id}-1",
                parent_task_id=task_id,
                title=f"{title}: 準備",
                description="事前準備と確認",
                task_type=task_type,
                sequence_no=1,
                estimated_minutes=10,
            ),
            SubTask(
                id=f"{task_id}-2",
                parent_task_id=task_id,
                title=f"{title}: 実行",
                description=description,
                task_type=task_type,
                sequence_no=2,
                depends_on=[f"{task_id}-1"],
            ),
            SubTask(
                id=f"{task_id}-3",
                parent_task_id=task_id,
                title=f"{title}: 検証",
                description="実行結果の検証",
                task_type="verification",
                sequence_no=3,
                depends_on=[f"{task_id}-2"],
                estimated_minutes=10,
            ),
        ]

    # Identify parallel groups
    parallel_groups = _identify_parallel_groups(subtasks)

    return BreakdownResult(
        parent_task_id=task_id,
        subtasks=subtasks,
        parallel_groups=parallel_groups,
    )


def _identify_parallel_groups(subtasks: list[SubTask]) -> list[list[str]]:
    """依存関係に基づいて並列実行可能なグループを特定する."""
    completed: set[str] = set()
    groups: list[list[str]] = []
    remaining = list(subtasks)

    while remaining:
        # Find tasks whose dependencies are all completed
        ready = [
            t for t in remaining
            if all(dep in completed for dep in t.depends_on)
        ]
        if not ready:
            # Remaining tasks have unresolvable dependencies — add them as single group
            groups.append([t.id for t in remaining])
            break
        groups.append([t.id for t in ready])
        for t in ready:
            completed.add(t.id)
            remaining.remove(t)

    return groups
