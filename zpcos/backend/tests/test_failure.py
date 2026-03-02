"""Failure Classification テスト"""

import pytest

from app.state.failure import classify_failure, suggest_recovery, FailureType


@pytest.mark.asyncio
async def test_classify_timeout():
    record = await classify_failure("Connection timeout after 30 seconds")
    assert record.failure_type == FailureType.TIMEOUT


@pytest.mark.asyncio
async def test_classify_rate_limit():
    record = await classify_failure("Rate limit exceeded, retry after 60s")
    assert record.failure_type == FailureType.RATE_LIMIT


@pytest.mark.asyncio
async def test_classify_auth():
    record = await classify_failure("401 Unauthorized: Invalid API key")
    assert record.failure_type == FailureType.AUTH_ERROR


@pytest.mark.asyncio
async def test_classify_unknown():
    record = await classify_failure("Something completely unexpected happened")
    assert record.failure_type == FailureType.UNKNOWN


@pytest.mark.asyncio
async def test_suggest_recovery_rate_limit():
    record = await classify_failure("429 Rate limit")
    strategy = await suggest_recovery(record)
    assert strategy.strategy in ("retry", "skip", "escalate", "modify_input")


@pytest.mark.asyncio
async def test_suggest_recovery_auth():
    record = await classify_failure("401 Unauthorized")
    strategy = await suggest_recovery(record)
    assert strategy.strategy in ("retry", "skip", "escalate", "modify_input")
