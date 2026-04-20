"""Auto Test Generator — generate pytest cases for a Skill."""

from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.security.prompt_guard import wrap_external_data
from app.services.self_improvement_models import AutoTestResult, GeneratedTestCase
from app.utils.json_parser import safe_extract_json

logger = logging.getLogger(__name__)

_TEST_GEN_SYSTEM_PROMPT = """\
You are the test auto-generation engine for Zero-Employee Orchestrator.
Generate pytest-format test code from the given skill code.

## Test types
1. **normal** — Normal tests (verify correct behavior with expected input)
2. **edge** — Edge case tests (empty input, very long input, special characters)
3. **error** — Error tests (invalid input, provider=None, exception raising)

## Output format
```json
{
  "test_cases": [
    {
      "test_name": "test_returns_success_with_normal_input",
      "test_type": "normal|edge|error",
      "input_data": {"input": "test input"},
      "expected_behavior": "returns status=success",
      "test_code": "async def test_...(): ..."
    }
  ]
}
```
"""


async def generate_tests_for_skill(
    db: AsyncSession,
    skill_id: uuid.UUID,
) -> AutoTestResult:
    """Auto-generate test cases from Skill code."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise ValueError(f"Skill not found: {skill_id}")

    code = skill.generated_code or ""
    test_cases: list[GeneratedTestCase] = []

    # -- Static test generation (always executed) --
    test_cases.extend(_generate_static_tests(skill.slug, code))

    # -- LLM test generation --
    try:
        llm_tests = await _llm_generate_tests(skill.slug, code)
        test_cases.extend(llm_tests)
    except Exception as exc:
        logger.warning("Skipping LLM test generation: %s", exc)

    normal_count = sum(1 for t in test_cases if t.test_type == "normal")
    edge_count = sum(1 for t in test_cases if t.test_type == "edge")
    error_count = sum(1 for t in test_cases if t.test_type == "error")

    return AutoTestResult(
        skill_id=str(skill_id),
        skill_slug=skill.slug,
        test_cases=test_cases,
        total_tests=len(test_cases),
        normal_tests=normal_count,
        edge_tests=edge_count,
        error_tests=error_count,
    )


def _generate_static_tests(slug: str, code: str) -> list[GeneratedTestCase]:
    """Test case generation based on static analysis."""
    tests: list[GeneratedTestCase] = []
    safe_slug = slug.replace("-", "_")

    # Normal: basic execution test
    tests.append(
        GeneratedTestCase(
            test_name=f"test_{safe_slug}_normal_execution",
            test_type="normal",
            input_data={"input": "test input data"},
            expected_behavior="Returns status of success or warning",
            test_code=f'''import pytest


@pytest.mark.asyncio
async def test_{safe_slug}_normal_execution():
    """Verify execution with normal input."""
    context = {{
        "input": "test input data",
        "local_context": {{}},
        "provider": None,
        "settings": {{}},
    }}
    # Get execute function
    namespace = {{}}
    exec(SKILL_CODE, namespace)
    execute = namespace["execute"]
    result = await execute(context)
    assert isinstance(result, dict)
    assert "status" in result
    assert result["status"] in ("success", "warning")
''',
        )
    )

    # Edge: empty input test
    tests.append(
        GeneratedTestCase(
            test_name=f"test_{safe_slug}_empty_input",
            test_type="edge",
            input_data={"input": ""},
            expected_behavior="Does not error on empty input",
            test_code=f'''import pytest


@pytest.mark.asyncio
async def test_{safe_slug}_empty_input():
    """Verify no crash on empty input."""
    context = {{
        "input": "",
        "local_context": {{}},
        "provider": None,
        "settings": {{}},
    }}
    namespace = {{}}
    exec(SKILL_CODE, namespace)
    execute = namespace["execute"]
    result = await execute(context)
    assert isinstance(result, dict)
    assert "status" in result
''',
        )
    )

    # Error: incomplete context
    tests.append(
        GeneratedTestCase(
            test_name=f"test_{safe_slug}_minimal_context",
            test_type="error",
            input_data={},
            expected_behavior="Error handling works with minimal context",
            test_code=f'''import pytest


@pytest.mark.asyncio
async def test_{safe_slug}_minimal_context():
    """Verify no crash with minimal context."""
    context = {{}}
    namespace = {{}}
    exec(SKILL_CODE, namespace)
    execute = namespace["execute"]
    try:
        result = await execute(context)
        assert isinstance(result, dict)
    except (KeyError, TypeError):
        pass  # Exception may occur if context is not checked
''',
        )
    )

    return tests


async def _llm_generate_tests(slug: str, code: str) -> list[GeneratedTestCase]:
    """Test case generation using LLM."""
    from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

    wrapped_code = wrap_external_data(code, source="skill_code")
    response = await llm_gateway.complete(
        CompletionRequest(
            messages=[
                {"role": "system", "content": _TEST_GEN_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (f"Generate tests for the following skill code:\n\n{wrapped_code}"),
                },
            ],
            temperature=0.3,
            max_tokens=4096,
            mode=ExecutionMode.SPEED,
        )
    )

    tests: list[GeneratedTestCase] = []
    try:
        data = safe_extract_json(response.content)
        if isinstance(data, dict):
            for item in data.get("test_cases", []):
                tests.append(
                    GeneratedTestCase(
                        test_name=item.get("test_name", "test_unnamed"),
                        test_type=item.get("test_type", "normal"),
                        input_data=item.get("input_data", {}),
                        expected_behavior=item.get("expected_behavior", ""),
                        test_code=item.get("test_code", ""),
                    )
                )
    except (json.JSONDecodeError, AttributeError):
        pass

    return tests
