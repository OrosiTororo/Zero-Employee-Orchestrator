"""Judge Tuner — auto-tune Judge criteria from Experience Memory."""

from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestration.experience_memory import (
    ExperienceMemoryRecord,
    FailureTaxonomyRecord,
)
from app.orchestration.judge import RuleBasedJudge, rule_judge
from app.security.prompt_guard import wrap_external_data
from app.services.self_improvement_models import JudgeTuningResult, JudgeTuningRule
from app.utils.json_parser import safe_extract_json

logger = logging.getLogger(__name__)


async def tune_judge_from_experience(
    db: AsyncSession,
    company_id: uuid.UUID,
) -> JudgeTuningResult:
    """Propose Judge rules from approval/rejection patterns in Experience Memory."""

    # Retrieve success patterns
    success_records = await db.execute(
        select(ExperienceMemoryRecord)
        .where(
            ExperienceMemoryRecord.company_id == company_id,
        )
        .limit(200)
    )
    successes = list(success_records.scalars().all())

    # Retrieve failure patterns
    failure_records = await db.execute(
        select(FailureTaxonomyRecord)
        .where(
            FailureTaxonomyRecord.company_id == company_id,
        )
        .limit(200)
    )
    failures = list(failure_records.scalars().all())

    total_patterns = len(successes) + len(failures)
    approval_rate = len(successes) / total_patterns if total_patterns > 0 else 0.0
    rejection_rate = len(failures) / total_patterns if total_patterns > 0 else 0.0

    proposed_rules: list[JudgeTuningRule] = []

    # -- Pattern 1: Auto-generate rules from frequently occurring failure categories --
    failure_categories: dict[str, int] = {}
    for f in failures:
        failure_categories[f.category] = failure_categories.get(f.category, 0) + f.occurrence_count

    for category, count in failure_categories.items():
        if count >= 3:
            proposed_rules.append(
                JudgeTuningRule(
                    rule_name=f"auto_check_{category}",
                    rule_type="category_filter",
                    condition={"failure_category": category, "min_occurrences": count},
                    action="warn",
                    confidence=min(0.9, 0.5 + count * 0.05),
                    source_patterns=count,
                    description=f"Failure category '{category}' occurred {count} times. Additional checks recommended for matching patterns in output.",
                )
            )

    # -- Pattern 2: Generate rules from patterns with high effectiveness scores --
    high_effectiveness = [s for s in successes if s.effectiveness_score >= 0.8]
    if high_effectiveness:
        categories = {}
        for s in high_effectiveness:
            categories[s.category] = categories.get(s.category, 0) + 1
        for cat, cnt in categories.items():
            if cnt >= 2:
                proposed_rules.append(
                    JudgeTuningRule(
                        rule_name=f"prefer_{cat}_pattern",
                        rule_type="pattern_match",
                        condition={"success_category": cat, "min_effectiveness": 0.8},
                        action="pass",
                        confidence=min(0.85, 0.5 + cnt * 0.1),
                        source_patterns=cnt,
                        description=f"Category '{cat}' has {cnt} success patterns with effectiveness score >= 0.8. Output in this category tends to be high quality.",
                    )
                )

    # -- Pattern 3: Strict checks from failures with low recovery success rates --
    low_recovery = [
        f for f in failures if f.recovery_success_rate < 0.3 and f.occurrence_count >= 2
    ]
    for f in low_recovery:
        proposed_rules.append(
            JudgeTuningRule(
                rule_name=f"strict_check_{f.category}_{f.subcategory}",
                rule_type="threshold",
                condition={
                    "failure_category": f.category,
                    "failure_subcategory": f.subcategory,
                    "recovery_rate": f.recovery_success_rate,
                },
                action="fail",
                confidence=min(0.95, 0.6 + f.occurrence_count * 0.05),
                source_patterns=f.occurrence_count,
                description=(
                    f"'{f.category}/{f.subcategory}' has a low recovery success rate of {f.recovery_success_rate:.0%} "
                    f"and occurred {f.occurrence_count} times. Strict pre-checks recommended for prevention."
                ),
            )
        )

    # -- Additional rule proposals via LLM --
    try:
        llm_rules = await _llm_propose_judge_rules(successes, failures)
        proposed_rules.extend(llm_rules)
    except Exception as exc:
        logger.warning("Skipping LLM Judge rule proposals: %s", exc)

    summary = (
        f"Analyzed patterns: {total_patterns} (success: {len(successes)}, failure: {len(failures)})."
        f" Approval rate: {approval_rate:.0%}. Proposed rules: {len(proposed_rules)}."
    )

    return JudgeTuningResult(
        company_id=str(company_id),
        proposed_rules=proposed_rules,
        analyzed_patterns=total_patterns,
        approval_rate=approval_rate,
        rejection_rate=rejection_rate,
        summary=summary,
    )


async def _llm_propose_judge_rules(
    successes: list[ExperienceMemoryRecord],
    failures: list[FailureTaxonomyRecord],
) -> list[JudgeTuningRule]:
    """Propose rules from patterns using LLM."""
    from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

    # Summarize data
    success_summary = "\n".join(
        f"- [{s.category}] {s.title} (effectiveness: {s.effectiveness_score})"
        for s in successes[:20]
    )
    failure_summary = "\n".join(
        f"- [{f.category}/{f.subcategory}] {f.description} (occurrences: {f.occurrence_count}, recovery rate: {f.recovery_success_rate:.0%})"
        for f in failures[:20]
    )

    wrapped_success = wrap_external_data(success_summary or "(no data)", source="success_patterns")
    wrapped_failures = wrap_external_data(failure_summary or "(no data)", source="failure_patterns")
    prompt = f"""Please propose quality check rules for the Judge Layer from the following data.

## Success patterns
{wrapped_success}

## Failure patterns
{wrapped_failures}

Output as a JSON array:
```json
[
  {{
    "rule_name": "rule_name (English snake_case)",
    "description": "Description of the rule",
    "action": "warn or fail"
  }}
]
```"""

    response = await llm_gateway.complete(
        CompletionRequest(
            messages=[
                {"role": "system", "content": "You are a quality management expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
            mode=ExecutionMode.SPEED,
        )
    )

    rules: list[JudgeTuningRule] = []
    try:
        items = safe_extract_json(response.content)
        if isinstance(items, list):
            for item in items[:5]:  # Maximum 5 rules
                rules.append(
                    JudgeTuningRule(
                        rule_name=item.get("rule_name", "llm_rule"),
                        rule_type="pattern_match",
                        condition={},
                        action=item.get("action", "warn"),
                        confidence=0.6,
                        source_patterns=0,
                        description=item.get("description", ""),
                    )
                )
    except (json.JSONDecodeError, AttributeError):
        pass

    return rules


async def apply_judge_tuning(
    tuning_result: JudgeTuningResult,
    judge: RuleBasedJudge | None = None,
) -> int:
    """Apply proposed Judge rules (called after approval)."""
    target_judge = judge or rule_judge
    applied = 0

    for rule in tuning_result.proposed_rules:
        if rule.confidence < 0.5:
            continue

        severity = "error" if rule.action == "fail" else "warning"

        def make_check(r: JudgeTuningRule):
            def check_fn(output: dict, context: dict) -> bool:
                # For category filter
                if r.rule_type == "category_filter":
                    cat = r.condition.get("failure_category", "")
                    content = json.dumps(output, ensure_ascii=False, default=str)
                    return cat.lower() not in content.lower()
                return True

            return check_fn

        target_judge.add_rule(
            name=rule.rule_name,
            check_fn=make_check(rule),
            severity=severity,
        )
        applied += 1

    logger.info("Applied %d Judge rules", applied)
    return applied
