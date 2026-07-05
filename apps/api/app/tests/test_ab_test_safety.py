"""Tests for the safety gate in the A/B test skill executor.

危険コードは in-process exec() に到達する前に静的安全分析で拒否されることを固定する。
"""

import pytest

from app.models.skill import Skill
from app.services.self_improvement.ab_test import _execute_skill_for_test


def _skill(code: str) -> Skill:
    return Skill(slug="ab-test-skill", name="AB Test Skill", generated_code=code)


@pytest.mark.asyncio
async def test_execute_skill_blocks_os_system_code():
    result, elapsed = await _execute_skill_for_test(
        _skill("import os\nos.system('echo pwned')"), {"input": "x"}
    )
    assert result["status"] == "error"
    assert "Blocked by safety check" in result["output"]
    assert elapsed == 0.0


@pytest.mark.asyncio
async def test_execute_skill_blocks_exec_code():
    result, _ = await _execute_skill_for_test(_skill("exec('print(1)')"), {"input": "x"})
    assert result["status"] == "error"
    assert "Blocked by safety check" in result["output"]


@pytest.mark.asyncio
async def test_execute_skill_runs_safe_code():
    code = "def execute(context):\n    return {'status': 'success', 'output': context['input']}"
    result, _ = await _execute_skill_for_test(_skill(code), {"input": "hello"})
    assert result["status"] == "success"
    assert result["output"] == "hello"
