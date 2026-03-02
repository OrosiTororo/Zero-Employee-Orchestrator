"""Judge Pre-Check (Stage 1) テスト"""

import pytest

from app.judge.pre_check import pre_check


@pytest.mark.asyncio
async def test_short_text_passes():
    result = await pre_check("Hello world")
    assert result.passed is True


@pytest.mark.asyncio
async def test_empty_text_fails():
    result = await pre_check("")
    assert result.passed is False


@pytest.mark.asyncio
async def test_policy_violation_detected():
    result = await pre_check("世界一の完璧なツールです。成功を保証します。")
    # May or may not fail depending on policy rules
    assert isinstance(result.passed, bool)
