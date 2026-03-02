"""Policy Pack テスト"""

import pytest

from app.policy.policy_pack import check_policy


@pytest.mark.asyncio
async def test_clean_text():
    violations = await check_policy("ZPCOSは自然言語でSkillを操作するシステムです。")
    assert len(violations) == 0


@pytest.mark.asyncio
async def test_detect_exaggeration():
    violations = await check_policy("このツールは絶対に失敗しません。100%成功します。")
    assert len(violations) >= 1
    categories = [v.rule.category for v in violations]
    assert "exaggeration" in categories


@pytest.mark.asyncio
async def test_detect_forbidden_expression():
    violations = await check_policy("このサービスを使えば必ず儲かる投資ができます。")
    assert len(violations) >= 1
    categories = [v.rule.category for v in violations]
    assert "forbidden_expression" in categories
