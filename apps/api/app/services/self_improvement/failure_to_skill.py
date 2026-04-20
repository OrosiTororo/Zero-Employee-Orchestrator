"""Failure-to-Skill — auto-generate new Skills from failure patterns."""

from __future__ import annotations

import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestration.experience_memory import FailureTaxonomyRecord, PersistentExperienceMemory
from app.security.prompt_guard import wrap_external_data
from app.services.self_improvement_models import FailureToSkillProposal

logger = logging.getLogger(__name__)


async def generate_skills_from_failures(
    db: AsyncSession,
    company_id: uuid.UUID,
    min_occurrences: int = 2,
) -> list[FailureToSkillProposal]:
    """Propose prevention Skills from frequently occurring failure patterns."""
    memory = PersistentExperienceMemory(db, company_id)
    frequent_failures = await memory.get_frequent_failures(min_count=min_occurrences)

    proposals: list[FailureToSkillProposal] = []

    for failure in frequent_failures:
        slug = f"prevent-{failure.category}-{failure.subcategory}".lower()
        slug = re.sub(r"[^a-z0-9-]", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")

        name = f"Failure prevention: {failure.category}/{failure.subcategory}"

        description = (
            f"Skill to prevent recurrence of failure pattern '{failure.category}/{failure.subcategory}'."
            f" {failure.description}. Prevention strategy: {failure.prevention_strategy}"
        )

        # Attempt code generation with LLM
        code = ""
        try:
            code = await _generate_prevention_skill_code(failure)
        except Exception as exc:
            logger.warning("Skipping LLM prevention skill generation: %s", exc)

        # Fallback: template-based code
        if not code:
            code = _generate_prevention_template(slug, failure)

        confidence = min(0.9, 0.4 + failure.occurrence_count * 0.1)

        proposals.append(
            FailureToSkillProposal(
                failure_category=failure.category,
                failure_subcategory=failure.subcategory,
                occurrence_count=failure.occurrence_count,
                proposed_skill_slug=slug,
                proposed_skill_name=name,
                proposed_skill_description=description,
                proposed_code=code,
                prevention_strategy=failure.prevention_strategy,
                confidence=confidence,
            )
        )

    return proposals


async def _generate_prevention_skill_code(
    failure: FailureTaxonomyRecord,
) -> str:
    """Generate prevention skill code using LLM."""
    from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

    wrapped_failure = wrap_external_data(
        f"Category: {failure.category}\nSubcategory: {failure.subcategory}\n"
        f"Description: {failure.description}\nPrevention strategy: {failure.prevention_strategy}\n"
        f"Occurrences: {failure.occurrence_count}",
        source="failure_taxonomy",
    )
    prompt = f"""Generate Python code for a skill that prevents the following failure pattern.

## Failure pattern
{wrapped_failure}

## Rules
- Implement `async def execute(context: dict) -> dict`
- context contains input, local_context, provider, settings
- Return value: {{ status, output, artifacts, cost_usd }}
- Do not use eval/exec/subprocess
- Check before task execution and return warnings if issues are found

```python
{{code}}
```"""

    response = await llm_gateway.complete(
        CompletionRequest(
            messages=[
                {"role": "system", "content": "You are an expert in skill code generation."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
            mode=ExecutionMode.SPEED,
        )
    )

    py_match = re.search(r"```python\s*\n(.*?)\n```", response.content, re.DOTALL)
    return py_match.group(1) if py_match else ""


def _generate_prevention_template(slug: str, failure: FailureTaxonomyRecord) -> str:
    """Template-based prevention skill code."""
    safe_cat = failure.category.replace('"', '\\"')
    safe_sub = failure.subcategory.replace('"', '\\"')
    safe_desc = failure.description.replace('"', '\\"').replace("\n", "\\n")
    safe_prev = failure.prevention_strategy.replace('"', '\\"').replace("\n", "\\n")

    return f'''"""Failure prevention skill: {slug}

Category: {safe_cat}/{safe_sub}
Prevention strategy: {safe_prev}
"""


async def execute(context: dict) -> dict:
    """Check for failure patterns before task execution.

    Detection target: {safe_desc}
    """
    user_input = context.get("input", "")
    warnings: list[str] = []

    # Failure pattern keyword check
    risk_keywords = ["{safe_cat}", "{safe_sub}"]
    for keyword in risk_keywords:
        if keyword.lower() in user_input.lower():
            warnings.append(
                f"Input contains failure pattern keyword '{{keyword}}'."
                f" Prevention strategy: {safe_prev}"
            )

    if warnings:
        return {{
            "status": "warning",
            "output": "Failure pattern signs detected: " + "; ".join(warnings),
            "artifacts": [],
            "cost_usd": 0.0,
            "prevention_advice": "{safe_prev}",
        }}

    return {{
        "status": "success",
        "output": "No failure pattern signs detected",
        "artifacts": [],
        "cost_usd": 0.0,
    }}
'''
