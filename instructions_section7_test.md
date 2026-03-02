# Section 7 — テスト・ベンチマーク（Claude Code 用）v11.2

> 担当: Claude Code（全ステップ）
> 前提: Section 3〜5 が完了していること
> 完了条件: pytest 全パス + ZPCOS-Bench 結果が docs/BENCHMARK.md に記録
> v11.2 追加: test_self_healing, test_local_context, test_skill_registry

---

## ステップ 7.1 — test_token_store.py（変更なし、v11.0と同じ）

AES-GCM の暗号化/復号、save/load/has/delete をテスト。

---

## ステップ 7.2 — test_gateway.py（変更なし）

---

## ステップ 7.3 — test_auth.py（変更なし）

---

## ステップ 7.4 — test_state_machine.py（変更なし）

---

## ステップ 7.5 — test_skills.py（変更なし）

---

## ステップ 7.6 — test_skill_generator.py（変更なし）

---

## ステップ 7.7 — test_orchestrator.py（変更なし）

---

## ステップ 7.8 — test_policy_pack.py ★v11.1

```python
"""Policy Pack のテスト。"""
import pytest
from app.policy.policy_pack import check_policy


@pytest.mark.asyncio
async def test_no_violations():
    result = await check_policy("これは普通のテキストです。")
    assert len(result) == 0


@pytest.mark.asyncio
async def test_exaggeration_detection():
    result = await check_policy("この投資は絶対に儲かります。")
    assert len(result) >= 1
    assert any(v.rule.category == "exaggeration" for v in result)


@pytest.mark.asyncio
async def test_forbidden_expression():
    result = await check_policy("必ず儲かる方法を教えます。")
    assert len(result) >= 1
    assert any(v.rule.severity == "error" for v in result)
```

---

## ステップ 7.9 — test_pre_check.py ★v11.1

```python
"""Two-stage Detection (Pre-check) のテスト。"""
import pytest
from app.judge.pre_check import pre_check


@pytest.mark.asyncio
async def test_empty_input():
    result = await pre_check("")
    assert result.passed is False


@pytest.mark.asyncio
async def test_short_input():
    result = await pre_check("短い")
    assert result.passed is False


@pytest.mark.asyncio
async def test_valid_input():
    result = await pre_check("これは十分な長さのテキストです。内容を検証してください。")
    assert result.passed is True


@pytest.mark.asyncio
async def test_policy_violation_in_precheck():
    result = await pre_check("この方法は絶対に必ず儲かるので投資してください。")
    assert result.passed is False
```

---

## ステップ 7.10 — test_failure_taxonomy.py ★v11.1

```python
"""Failure Taxonomy のテスト。"""
import pytest
from app.state.failure import classify_failure, suggest_recovery, FailureType


@pytest.mark.asyncio
async def test_auth_error():
    record = await classify_failure("401 Unauthorized")
    assert record.failure_type == FailureType.AUTH_ERROR
    assert record.recoverable is True


@pytest.mark.asyncio
async def test_rate_limit():
    record = await classify_failure("429 Rate limit exceeded")
    assert record.failure_type == FailureType.RATE_LIMIT
    recovery = await suggest_recovery(record)
    assert recovery.auto_applicable is True


@pytest.mark.asyncio
async def test_timeout():
    record = await classify_failure("Request timeout after 30s")
    assert record.failure_type == FailureType.TIMEOUT


@pytest.mark.asyncio
async def test_unknown():
    record = await classify_failure("Something weird happened")
    assert record.failure_type == FailureType.UNKNOWN
```

---

## ステップ 7.11 — test_experience_memory.py ★v11.1

```python
"""Experience Memory のテスト。"""
import pytest
from app.state.experience import init_experience_db, save_experience, get_relevant_experiences, ExperienceCard


@pytest.fixture(autouse=True)
async def setup_db(tmp_path):
    await init_experience_db(str(tmp_path / "exp.db"))


@pytest.mark.asyncio
async def test_save_and_retrieve():
    card = ExperienceCard(
        task_type="youtube_analysis",
        success_factors=["trend data was fresh", "used quality model"],
        model_used="quality", score=0.92, context="YouTube改善タスク",
    )
    await save_experience(card)
    results = await get_relevant_experiences("youtube_analysis")
    assert len(results) == 1
    assert results[0].score == 0.92
```

---

## ステップ 7.12 — test_cost_guard.py ★v11.1

```python
"""Cost Guard のテスト。"""
import pytest
from app.orchestrator.cost_guard import estimate_cost
from app.orchestrator.models import OrchestrationPlan, OrchestrationStep


@pytest.mark.asyncio
async def test_cost_estimate():
    plan = OrchestrationPlan(
        intent="test",
        steps=[
            OrchestrationStep(step_id="s1", skill_name="yt-trend"),
            OrchestrationStep(step_id="s2", skill_name="yt-rival"),
        ],
    )
    est = await estimate_cost(plan, quality_mode="balanced")
    assert est.total_api_calls > 0
    assert est.estimated_cost_usd >= 0


@pytest.mark.asyncio
async def test_budget_exceeded():
    plan = OrchestrationPlan(intent="test", steps=[
        OrchestrationStep(step_id=f"s{i}", skill_name="yt-trend")
        for i in range(50)
    ])
    est = await estimate_cost(plan, budget_limit_usd=0.001)
    assert est.budget_exceeded is True
```

---

## ステップ 7.13 — test_quality_sla.py ★v11.1

```python
"""Quality SLA Selector のテスト。"""
from app.orchestrator.quality_sla import QualityMode, get_model_for_mode, should_run_judge


def test_fastest_mode():
    assert get_model_for_mode(QualityMode.FASTEST) == "fast"
    assert should_run_judge(QualityMode.FASTEST) is False


def test_balanced_mode():
    assert should_run_judge(QualityMode.BALANCED) is True


def test_high_quality_mode():
    model = get_model_for_mode(QualityMode.HIGH_QUALITY, "complex")
    assert model == "reason"
```

---

## ステップ 7.14 — test_gap_detector.py ★v11.1

```python
"""Skill Gap Negotiation のテスト。"""
import pytest
from app.skills.gap_detector import detect_gaps
from app.skills.framework import SkillRegistry
from app.orchestrator.models import OrchestrationPlan, OrchestrationStep


@pytest.mark.asyncio
async def test_no_gaps():
    registry = SkillRegistry()
    plan = OrchestrationPlan(intent="test", steps=[])
    gaps = await detect_gaps(plan, registry)
    assert len(gaps) == 0


@pytest.mark.asyncio
async def test_detect_missing_skill():
    registry = SkillRegistry()
    plan = OrchestrationPlan(intent="test", steps=[
        OrchestrationStep(step_id="s1", skill_name="nonexistent-skill"),
    ])
    gaps = await detect_gaps(plan, registry)
    assert len(gaps) == 1
    assert gaps[0].required_skill == "nonexistent-skill"
    assert len(gaps[0].options) == 3
```

---

## ステップ 7.15 — test_self_healing.py ★v11.2

```python
"""Self-Healing DAG のテスト。"""
import pytest
from app.orchestrator.self_healing import (
    self_heal, get_heal_history, choose_strategy,
    HealStrategy, MAX_HEAL_ATTEMPTS,
)
from app.state.failure import FailureRecord, FailureType


@pytest.mark.asyncio
async def test_choose_strategy_auth_error():
    failure = FailureRecord(
        failure_type=FailureType.AUTH_ERROR,
        original_error="401 Unauthorized",
        recoverable=True,
    )
    strategy = await choose_strategy(failure, attempt_number=1)
    assert strategy == HealStrategy.RETRY_SAME


@pytest.mark.asyncio
async def test_choose_strategy_escalation():
    failure = FailureRecord(
        failure_type=FailureType.AUTH_ERROR,
        original_error="401 Unauthorized",
        recoverable=True,
    )
    # 2回目以降はエスカレーション
    strategy = await choose_strategy(failure, attempt_number=2)
    assert strategy == HealStrategy.SWAP_SKILL


@pytest.mark.asyncio
async def test_self_heal_success():
    failure = FailureRecord(
        failure_type=FailureType.RATE_LIMIT,
        original_error="429 Rate limit",
        recoverable=True,
    )
    attempt = await self_heal("test-orch-1", failure)
    assert attempt.attempt_number == 1
    assert attempt.strategy in list(HealStrategy)


@pytest.mark.asyncio
async def test_self_heal_max_attempts():
    failure = FailureRecord(
        failure_type=FailureType.TIMEOUT,
        original_error="Timeout",
        recoverable=True,
    )
    oid = "test-orch-max"
    for _ in range(MAX_HEAL_ATTEMPTS + 1):
        attempt = await self_heal(oid, failure)
    assert attempt.result == "escalated"


@pytest.mark.asyncio
async def test_heal_history():
    failure = FailureRecord(
        failure_type=FailureType.TIMEOUT,
        original_error="Timeout",
        recoverable=True,
    )
    oid = "test-orch-history"
    await self_heal(oid, failure)
    await self_heal(oid, failure)
    history = await get_heal_history(oid)
    assert len(history) == 2
```

---

## ステップ 7.16 — test_local_context.py ★v11.2

```python
"""Local Context Skill のテスト。"""
import pytest
import json
from pathlib import Path
from app.skills.builtins.local_context.executor import (
    _is_path_allowed, _read_file_content, _load_allowed_dirs,
)


def test_path_allowed(tmp_path):
    allowed = [str(tmp_path)]
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")
    assert _is_path_allowed(str(test_file), allowed) is True


def test_path_not_allowed(tmp_path):
    allowed = [str(tmp_path / "safe")]
    test_file = tmp_path / "unsafe" / "secret.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("secret")
    assert _is_path_allowed(str(test_file), allowed) is False


def test_read_text_file(tmp_path):
    test_file = tmp_path / "test.md"
    test_file.write_text("# Hello World")
    content = _read_file_content(test_file)
    assert content == "# Hello World"


def test_read_unsupported_file(tmp_path):
    test_file = tmp_path / "test.exe"
    test_file.write_bytes(b"\x00\x01\x02")
    content = _read_file_content(test_file)
    assert content is None
```

---

## ステップ 7.17 — test_skill_registry.py ★v11.2

```python
"""Skill Registry のテスト。"""
import pytest
import json
from pathlib import Path
from app.skills.registry import (
    search_registry, publish_skill, install_skill, get_popular,
    SkillPackage, _registry_path, _save_registry, _load_registry,
)


@pytest.fixture(autouse=True)
def clean_registry(tmp_path, monkeypatch):
    """テスト用の一時レジストリを使用。"""
    test_registry = tmp_path / "skill_registry.json"
    monkeypatch.setattr("app.skills.registry._registry_path", test_registry)
    yield


@pytest.mark.asyncio
async def test_search_empty():
    results = await search_registry("test")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_publish_and_search(tmp_path):
    # テスト用Skillディレクトリ作成
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.json").write_text(json.dumps({
        "name": "my-test-skill",
        "version": "1.0.0",
        "description": "A test skill for YouTube analysis",
        "tags": ["youtube", "analysis"],
    }))

    pkg = await publish_skill(str(skill_dir), "test-author")
    assert pkg.name == "my-test-skill"

    results = await search_registry("youtube")
    assert len(results) == 1
    assert results[0].name == "my-test-skill"


@pytest.mark.asyncio
async def test_popular_ordering(tmp_path):
    packages = [
        SkillPackage(name="popular", version="1.0", author="a", description="desc", downloads=100),
        SkillPackage(name="unpopular", version="1.0", author="b", description="desc", downloads=1),
    ]
    _save_registry(packages)

    popular = await get_popular()
    assert popular[0].name == "popular"
```

---

## ステップ 7.18 — テスト実行

```powershell
cd zpcos/backend
uv run python -m pytest tests/ -v
# 全テスト PASS を確認
```

---

## ステップ 7.18b — ZPCOS-Bench（変更なし）

---

## ステップ 7.19 — コミット

```powershell
git add -A
git commit -m "test: add unit tests including v11.2 modules (Section 7 v11.2)"
```

セクション 7 完了。
