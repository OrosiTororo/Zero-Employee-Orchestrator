"""Self-Healing DAG — 失敗からの自律回復。"""

from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel
from app.state.failure import FailureRecord, FailureType

MAX_HEAL_ATTEMPTS = 3


class HealStrategy(str, Enum):
    RETRY_SAME = "retry_same"
    SWAP_SKILL = "swap_skill"
    REPLAN = "replan"
    DECOMPOSE = "decompose"


class HealAttempt(BaseModel):
    attempt_number: int
    strategy: HealStrategy
    original_error: str
    new_plan_id: str | None = None
    result: str = "pending"  # success | failed | escalated
    timestamp: str = ""


# メモリ内ストレージ
_heal_history: dict[str, list[HealAttempt]] = {}


async def choose_strategy(failure: FailureRecord, attempt_number: int) -> HealStrategy:
    """失敗タイプと試行回数から回復戦略を選択。"""
    if attempt_number >= MAX_HEAL_ATTEMPTS:
        return HealStrategy.REPLAN

    if failure.failure_type == FailureType.RATE_LIMIT:
        return HealStrategy.RETRY_SAME
    elif failure.failure_type == FailureType.AUTH_ERROR:
        if attempt_number == 1:
            return HealStrategy.RETRY_SAME
        return HealStrategy.SWAP_SKILL
    elif failure.failure_type == FailureType.TIMEOUT:
        if attempt_number == 1:
            return HealStrategy.RETRY_SAME
        return HealStrategy.DECOMPOSE
    elif failure.failure_type in (FailureType.EVIDENCE_WEAK, FailureType.CONTRADICTION):
        return HealStrategy.SWAP_SKILL
    else:
        if attempt_number == 1:
            return HealStrategy.RETRY_SAME
        return HealStrategy.REPLAN


async def self_heal(orchestration_id: str, failure: FailureRecord) -> HealAttempt:
    """失敗からの自律回復を試みる。"""
    history = _heal_history.get(orchestration_id, [])
    attempt_number = len(history) + 1
    now = datetime.now(timezone.utc).isoformat()

    if attempt_number > MAX_HEAL_ATTEMPTS:
        attempt = HealAttempt(
            attempt_number=attempt_number,
            strategy=HealStrategy.REPLAN,
            original_error=failure.original_error or failure.message,
            result="escalated",
            timestamp=now,
        )
        history.append(attempt)
        _heal_history[orchestration_id] = history
        return attempt

    strategy = await choose_strategy(failure, attempt_number)

    attempt = HealAttempt(
        attempt_number=attempt_number,
        strategy=strategy,
        original_error=failure.original_error or failure.message,
        result="success" if failure.recoverable else "failed",
        timestamp=now,
    )

    history.append(attempt)
    _heal_history[orchestration_id] = history
    return attempt


async def get_heal_history(orchestration_id: str) -> list[HealAttempt]:
    """自己修復の試行履歴を返す。"""
    return _heal_history.get(orchestration_id, [])
