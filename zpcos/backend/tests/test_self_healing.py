"""Self-Healing テスト"""

import pytest

from app.orchestrator.self_healing import choose_strategy, HealStrategy
from app.state.failure import FailureRecord, FailureType


@pytest.mark.asyncio
async def test_choose_retry_for_rate_limit():
    failure = FailureRecord(
        failure_type=FailureType.RATE_LIMIT,
        original_error="429 Too Many Requests",
        message="rate limited",
        recoverable=True,
    )
    strategy = await choose_strategy(failure, attempt_number=1)
    assert strategy == HealStrategy.RETRY_SAME


@pytest.mark.asyncio
async def test_choose_retry_for_timeout_first():
    failure = FailureRecord(
        failure_type=FailureType.TIMEOUT,
        original_error="Connection timed out",
        message="timeout",
        recoverable=True,
    )
    strategy = await choose_strategy(failure, attempt_number=1)
    assert strategy == HealStrategy.RETRY_SAME


@pytest.mark.asyncio
async def test_choose_decompose_for_timeout_second():
    failure = FailureRecord(
        failure_type=FailureType.TIMEOUT,
        original_error="Connection timed out",
        message="timeout",
        recoverable=True,
    )
    strategy = await choose_strategy(failure, attempt_number=2)
    assert strategy == HealStrategy.DECOMPOSE


@pytest.mark.asyncio
async def test_replan_after_max_attempts():
    failure = FailureRecord(
        failure_type=FailureType.TIMEOUT,
        original_error="timeout",
        message="timeout",
        recoverable=True,
    )
    strategy = await choose_strategy(failure, attempt_number=3)
    assert strategy == HealStrategy.REPLAN


@pytest.mark.asyncio
async def test_swap_for_evidence_weak():
    failure = FailureRecord(
        failure_type=FailureType.EVIDENCE_WEAK,
        original_error="weak evidence",
        message="evidence weak",
        recoverable=True,
    )
    strategy = await choose_strategy(failure, attempt_number=1)
    assert strategy == HealStrategy.SWAP_SKILL
