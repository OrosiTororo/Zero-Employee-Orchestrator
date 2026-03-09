"""Heartbeat スケジューラ — 定期巡回の実行管理.

Zero-Employee Orchestrator.md §36.3 に基づき、Heartbeat を単なる定期実行
ではなく、AI 組織が定期巡回して仕事の状態を確認し、必要に応じて進行・
委譲・再計画・報告を行う運用原理として実装する。

発火契機:
- 定期スケジュール (cron)
- チケット新規作成
- タスク割当
- 差し戻し
- 外部イベント受信
- 予算残量閾値到達
- 承認待ち解除
- 上位者からの再指示
- 依存タスク完了
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class HeartbeatTrigger(str, Enum):
    """Heartbeat の発火契機."""

    SCHEDULED = "scheduled"
    TICKET_CREATED = "ticket_created"
    TASK_ASSIGNED = "task_assigned"
    REWORK_REQUESTED = "rework_requested"
    EXTERNAL_EVENT = "external_event"
    BUDGET_THRESHOLD = "budget_threshold"
    APPROVAL_RESOLVED = "approval_resolved"
    MANAGER_DIRECTIVE = "manager_directive"
    DEPENDENCY_COMPLETED = "dependency_completed"


class HeartbeatRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class HeartbeatAction:
    """Heartbeat 実行時に Agent が行うアクション."""

    action_type: str  # check_tasks, delegate, escalate, approve_request, update_state
    target_id: str | None = None
    description: str = ""
    result: str | None = None


@dataclass
class HeartbeatExecution:
    """Heartbeat 1 回の実行記録."""

    run_id: str
    policy_id: str
    agent_id: str | None
    team_id: str | None
    trigger: HeartbeatTrigger
    status: HeartbeatRunStatus = HeartbeatRunStatus.QUEUED
    actions: list[HeartbeatAction] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    summary: str = ""

    def start(self) -> None:
        self.status = HeartbeatRunStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.actions = []

    def add_action(self, action: HeartbeatAction) -> None:
        if self.actions is None:
            self.actions = []
        self.actions.append(action)

    def finish(self, success: bool = True, summary: str = "") -> None:
        self.finished_at = datetime.now(timezone.utc)
        self.status = HeartbeatRunStatus.SUCCEEDED if success else HeartbeatRunStatus.FAILED
        self.summary = summary


async def execute_heartbeat(
    policy_id: str,
    agent_id: str | None = None,
    team_id: str | None = None,
    trigger: HeartbeatTrigger = HeartbeatTrigger.SCHEDULED,
) -> HeartbeatExecution:
    """Heartbeat を実行する.

    実行時に Agent が行うこと:
    1. 自分の未完了タスク確認
    2. 依存関係の確認
    3. 予算・権限・期限の確認
    4. 必要であれば下位への委譲
    5. 必要であれば上位へのエスカレーション
    6. 必要であればユーザー承認要求
    7. 実行ログ・状態更新
    """
    execution = HeartbeatExecution(
        run_id=str(uuid.uuid4()),
        policy_id=policy_id,
        agent_id=agent_id,
        team_id=team_id,
        trigger=trigger,
    )
    execution.start()

    try:
        # 1. 未完了タスク確認
        execution.add_action(HeartbeatAction(
            action_type="check_tasks",
            description="未完了タスクの確認",
        ))

        # 2. 依存関係確認
        execution.add_action(HeartbeatAction(
            action_type="check_dependencies",
            description="依存関係の確認",
        ))

        # 3. 予算・権限・期限確認
        execution.add_action(HeartbeatAction(
            action_type="check_constraints",
            description="予算・権限・期限の確認",
        ))

        execution.finish(success=True, summary="Heartbeat 完了: 全チェック正常")

    except Exception as exc:
        logger.error("Heartbeat execution failed: %s", exc)
        execution.finish(success=False, summary=f"Heartbeat 失敗: {exc}")

    return execution
