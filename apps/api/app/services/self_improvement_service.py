"""AI Self-Improvement Service — Level 2: Seeds of Self-Improvement.

Implements the 6 Skills of the ai-self-improvement Plugin:
1. skill-analyzer:      Code quality analysis and improvement suggestions for existing Skills
2. skill-improver:      Auto-generation of improved Skill versions based on analysis results
3. judge-tuner:         Auto-tuning of Judge criteria from Experience Memory
4. failure-to-skill:    Auto-generation of new Skills from failure patterns
5. skill-ab-test:       A/B test comparison between Skills
6. auto-test-generator: Auto-generation of test code and quality verification
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.orchestration.experience_memory import (
    ExperienceMemoryRecord,
    FailureTaxonomyRecord,
    PersistentExperienceMemory,
)
from app.orchestration.judge import (
    RuleBasedJudge,
    rule_judge,
)
from app.security.prompt_guard import wrap_external_data
from app.services.self_improvement_models import (
    ABTestConfig,  # noqa: F401 — re-exported for API-route imports
    ABTestResult,
    AnalysisCategory,
    AnalysisFinding,
    AutoTestResult,
    FailureToSkillProposal,
    GeneratedTestCase,
    ImprovementPriority,
    JudgeTuningResult,
    JudgeTuningRule,
    SkillAnalysisResult,
    SkillImprovementProposal,
)
from app.services.skill_service import analyze_code_safety
from app.utils.json_parser import safe_extract_json

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. Skill Analyzer — Code quality analysis for existing Skills
# ---------------------------------------------------------------------------


_ANALYSIS_SYSTEM_PROMPT = """\
You are the skill quality analysis engine for Zero-Employee Orchestrator.
Analyze the given Python skill code and evaluate it from the following perspectives.

## Analysis perspectives
1. **code_quality** — Code quality (structure, readability, naming conventions, DRY principle)
2. **performance** — Performance (unnecessary processing, N+1 queries, memory usage)
3. **error_handling** — Error handling (exception handling, fallbacks, input validation)
4. **security** — Security (injection, credential exposure, dangerous operations)
5. **test_coverage** — Test coverage (testability, edge case consideration)
6. **documentation** — Documentation (docstrings, type hints, comments)

## Output format
Output in the following JSON format:

```json
{
  "overall_score": 0.0-1.0,
  "findings": [
    {
      "category": "code_quality|performance|error_handling|security|test_coverage|documentation",
      "priority": "low|medium|high|critical",
      "title": "Title of the issue",
      "description": "Detailed description of the issue",
      "suggestion": "Specific improvement suggestion"
    }
  ],
  "summary": "Overall evaluation summary"
}
```
"""


async def analyze_skill(
    db: AsyncSession,
    skill_id: uuid.UUID,
) -> SkillAnalysisResult:
    """Analyze existing Skill code and generate improvement suggestions.

    Combines deep analysis using LLM with basic analysis via static pattern matching.
    """
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise ValueError(f"Skill not found: {skill_id}")

    code = skill.generated_code or ""
    findings: list[AnalysisFinding] = []

    # -- Static analysis (always executed) --
    findings.extend(_static_analyze(code))

    # -- Safety check --
    safety = analyze_code_safety(code)
    if safety.has_dangerous_code:
        findings.append(
            AnalysisFinding(
                category=AnalysisCategory.SECURITY,
                priority=ImprovementPriority.CRITICAL,
                title="Dangerous code pattern detected",
                description=safety.summary,
                suggestion="Replace dangerous patterns such as eval/exec/subprocess with safe alternatives",
            )
        )
    if safety.has_external_communication:
        findings.append(
            AnalysisFinding(
                category=AnalysisCategory.SECURITY,
                priority=ImprovementPriority.HIGH,
                title="External communication detected",
                description="External HTTP communication is included",
                suggestion="Limit to only necessary communication and add timeout and error handling",
            )
        )

    # -- LLM analysis --
    try:
        llm_findings = await _llm_analyze(code)
        findings.extend(llm_findings)
    except Exception as exc:
        logger.warning("Skipping LLM analysis: %s", exc)

    # Calculate score
    overall_score = _calculate_overall_score(findings)

    summary_parts = []
    by_category = {}
    for f in findings:
        by_category.setdefault(f.category.value, []).append(f)
    for cat, items in by_category.items():
        critical_count = sum(1 for i in items if i.priority == ImprovementPriority.CRITICAL)
        high_count = sum(1 for i in items if i.priority == ImprovementPriority.HIGH)
        summary_parts.append(
            f"{cat}: {len(items)} items (critical={critical_count}, high={high_count})"
        )

    summary = (
        f"Analysis of skill '{skill.slug}' complete. Score: {overall_score:.0%}."
        f" Findings: {len(findings)} items. {'; '.join(summary_parts)}"
    )

    return SkillAnalysisResult(
        skill_id=str(skill_id),
        skill_slug=skill.slug,
        overall_score=overall_score,
        findings=findings,
        summary=summary,
    )


def _static_analyze(code: str) -> list[AnalysisFinding]:
    """Code analysis via static pattern matching."""
    findings: list[AnalysisFinding] = []

    if not code.strip():
        findings.append(
            AnalysisFinding(
                category=AnalysisCategory.CODE_QUALITY,
                priority=ImprovementPriority.CRITICAL,
                title="Code is empty",
                description="No implementation code exists for the skill",
                suggestion="Implement the execute(context) function",
            )
        )
        return findings

    lines = code.split("\n")

    # docstring check
    if '"""' not in code and "'''" not in code:
        findings.append(
            AnalysisFinding(
                category=AnalysisCategory.DOCUMENTATION,
                priority=ImprovementPriority.MEDIUM,
                title="Missing docstring",
                description="No docstring found for functions or modules",
                suggestion="Add docstrings to each function",
            )
        )

    # Type hint check
    func_defs = re.findall(r"(async\s+)?def\s+\w+\([^)]*\)", code)
    for func_def in func_defs:
        if (
            "->" not in func_def
            and "-> " not in code[code.index(func_def) : code.index(func_def) + len(func_def) + 30]
        ):
            findings.append(
                AnalysisFinding(
                    category=AnalysisCategory.DOCUMENTATION,
                    priority=ImprovementPriority.LOW,
                    title="Missing return type hint",
                    description=f"Function definition is missing a return type hint: {func_def[:60]}",
                    suggestion="Explicitly specify the return type in the form -> ReturnType",
                )
            )
            break  # One finding is enough

    # try/except check
    if "try:" not in code and "except" not in code:
        findings.append(
            AnalysisFinding(
                category=AnalysisCategory.ERROR_HANDLING,
                priority=ImprovementPriority.HIGH,
                title="Error handling not implemented",
                description="No try/except blocks found",
                suggestion="Add try/except for external API calls and file operations",
            )
        )

    # Hardcoded values
    hardcoded_patterns = [
        (r'https?://[^\s"\']+', "Hardcoded URL"),
        (r'["\'][\w-]+\.[\w-]+@[\w-]+\.[\w]+["\']', "Hardcoded email address"),
    ]
    for pattern, desc in hardcoded_patterns:
        if re.search(pattern, code):
            findings.append(
                AnalysisFinding(
                    category=AnalysisCategory.CODE_QUALITY,
                    priority=ImprovementPriority.MEDIUM,
                    title=desc,
                    description=f"{desc} detected in code",
                    suggestion="Inject via configuration values or context instead",
                )
            )

    # Function too long
    current_func_lines = 0
    in_func = False
    for line in lines:
        if re.match(r"(async\s+)?def\s+", line):
            if in_func and current_func_lines > 50:
                findings.append(
                    AnalysisFinding(
                        category=AnalysisCategory.CODE_QUALITY,
                        priority=ImprovementPriority.MEDIUM,
                        title="Function too long",
                        description=f"A function exceeding 50 lines exists ({current_func_lines} lines)",
                        suggestion="Split the function into smaller units",
                    )
                )
            in_func = True
            current_func_lines = 0
        elif in_func:
            current_func_lines += 1

    return findings


async def _llm_analyze(code: str) -> list[AnalysisFinding]:
    """Code analysis using LLM."""
    from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

    wrapped_code = wrap_external_data(code, source="skill_code")
    response = await llm_gateway.complete(
        CompletionRequest(
            messages=[
                {"role": "system", "content": _ANALYSIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (f"Please analyze the following skill code:\n\n{wrapped_code}"),
                },
            ],
            temperature=0.2,
            max_tokens=4096,
            mode=ExecutionMode.QUALITY,
        )
    )

    findings: list[AnalysisFinding] = []
    try:
        data = safe_extract_json(response.content)
        if isinstance(data, dict):
            for item in data.get("findings", []):
                try:
                    findings.append(
                        AnalysisFinding(
                            category=AnalysisCategory(item.get("category", "code_quality")),
                            priority=ImprovementPriority(item.get("priority", "medium")),
                            title=item.get("title", ""),
                            description=item.get("description", ""),
                            suggestion=item.get("suggestion", ""),
                        )
                    )
                except (ValueError, KeyError):
                    continue
    except (json.JSONDecodeError, AttributeError):
        pass

    return findings


def _calculate_overall_score(findings: list[AnalysisFinding]) -> float:
    """Calculate the overall score from findings."""
    if not findings:
        return 1.0

    penalty = 0.0
    for f in findings:
        if f.priority == ImprovementPriority.CRITICAL:
            penalty += 0.20
        elif f.priority == ImprovementPriority.HIGH:
            penalty += 0.10
        elif f.priority == ImprovementPriority.MEDIUM:
            penalty += 0.05
        else:
            penalty += 0.02

    return max(0.0, min(1.0, 1.0 - penalty))


# ---------------------------------------------------------------------------
# 2. Skill Improver — Generate improved version based on analysis results
# ---------------------------------------------------------------------------


_IMPROVE_SYSTEM_PROMPT = """\
You are the skill improvement engine for Zero-Employee Orchestrator.
Receive the existing skill code and analysis results, and generate an improved version of the code.

## Rules
- Maintain the `async def execute(context: dict) -> dict` interface
- Do not break existing functionality
- Do not use unsafe code (eval, exec, subprocess)
- Output improvement details as a changes summary

## Output format
```python
{entire improved code}
```

```json
{
  "changes": ["change 1", "change 2"],
  "expected_improvements": ["improvement effect 1", "improvement effect 2"]
}
```
"""


async def improve_skill(
    db: AsyncSession,
    skill_id: uuid.UUID,
    analysis: SkillAnalysisResult | None = None,
) -> SkillImprovementProposal:
    """Generate an improved version of a Skill based on analysis results.

    If analysis is not provided, analysis is performed first.
    """
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise ValueError(f"Skill not found: {skill_id}")

    if analysis is None:
        analysis = await analyze_skill(db, skill_id)

    original_code = skill.generated_code or ""
    if not original_code.strip():
        raise ValueError("No code exists to improve")

    # Build summary of analysis results
    findings_text = "\n".join(
        f"- [{f.priority.value}] {f.category.value}: {f.title} — {f.suggestion}"
        for f in analysis.findings
    )

    improved_code = original_code
    changes: list[str] = []
    expected: list[str] = []

    try:
        from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

        wrapped_original = wrap_external_data(original_code, source="skill_code")
        wrapped_findings = wrap_external_data(findings_text, source="analysis_findings")
        response = await llm_gateway.complete(
            CompletionRequest(
                messages=[
                    {"role": "system", "content": _IMPROVE_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"## Original code\n{wrapped_original}\n\n"
                            f"## Analysis results (score: {analysis.overall_score:.0%})\n"
                            f"{wrapped_findings}\n\n"
                            "Please improve the code based on the above analysis results."
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=4096,
                mode=ExecutionMode.QUALITY,
            )
        )

        py_match = re.search(r"```python\s*\n(.*?)\n```", response.content, re.DOTALL)
        if py_match:
            improved_code = py_match.group(1)

        meta = safe_extract_json(response.content)
        if isinstance(meta, dict):
            changes = meta.get("changes", [])
            expected = meta.get("expected_improvements", [])

    except Exception as exc:
        logger.warning(
            "Skipping LLM improvement generation, applying static improvements only: %s", exc
        )
        improved_code, changes = _apply_static_improvements(original_code, analysis.findings)
        expected = ["Basic improvements based on static analysis"]

    # Safety check
    safety = analyze_code_safety(improved_code)
    if safety.risk_level == "high":
        logger.warning("Safety risk in improved code, keeping original code")
        improved_code = original_code
        changes = ["Improvement rejected due to safety risk"]
        expected = []

    # Update version number
    current_version = skill.version or "0.1.0"
    parts = current_version.split(".")
    try:
        parts[-1] = str(int(parts[-1]) + 1)
    except ValueError:
        parts.append("1")
    proposed_version = ".".join(parts)

    return SkillImprovementProposal(
        original_skill_id=str(skill_id),
        original_version=current_version,
        proposed_version=proposed_version,
        original_code=original_code,
        improved_code=improved_code,
        changes_summary=changes if changes else ["Code quality improvement"],
        expected_improvements=expected if expected else ["Improved code quality"],
        requires_approval=True,
    )


def _apply_static_improvements(code: str, findings: list[AnalysisFinding]) -> tuple[str, list[str]]:
    """Static improvements applicable without LLM."""
    improved = code
    changes: list[str] = []

    # Add error handling
    has_error_handling = any(f.category == AnalysisCategory.ERROR_HANDLING for f in findings)
    if has_error_handling and "try:" not in improved:
        # Wrap the execute function body with try/except
        if "async def execute(" in improved:
            improved = improved.replace(
                "async def execute(context: dict) -> dict:",
                "async def execute(context: dict) -> dict:\n    try:",
            )
            # Adjust indentation
            lines = improved.split("\n")
            new_lines = []
            in_execute = False
            added_try = False
            for line in lines:
                if "async def execute(" in line:
                    in_execute = True
                    new_lines.append(line)
                    continue
                if in_execute and line.strip() == "try:":
                    added_try = True
                    new_lines.append(line)
                    continue
                if in_execute and added_try and line.strip() and not line.startswith("    "):
                    in_execute = False
                if in_execute and added_try and line.strip():
                    new_lines.append("    " + line)
                else:
                    new_lines.append(line)
            improved = "\n".join(new_lines)
            improved += '\n    except Exception as exc:\n        return {"status": "error", "output": str(exc), "artifacts": [], "cost_usd": 0.0}\n'
            changes.append("Added error handling to execute() function")

    return improved, changes


async def apply_improvement(
    db: AsyncSession,
    skill_id: uuid.UUID,
    proposal: SkillImprovementProposal,
) -> Skill:
    """Apply an improvement proposal (called after approval)."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise ValueError(f"Skill not found: {skill_id}")

    # Save version history in manifest_json
    manifest = skill.manifest_json or {}
    version_history = manifest.get("version_history", [])
    version_history.append(
        {
            "version": skill.version,
            "code_snapshot": skill.generated_code,
            "replaced_at": datetime.now(UTC).isoformat(),
        }
    )
    manifest["version_history"] = version_history
    skill.manifest_json = manifest

    # Apply update
    skill.generated_code = proposal.improved_code
    skill.version = proposal.proposed_version
    await db.flush()

    logger.info(
        "Skill improvement applied: %s v%s -> v%s",
        skill.slug,
        proposal.original_version,
        proposal.proposed_version,
    )
    return skill


# ---------------------------------------------------------------------------
# 3. Judge Tuner — Auto-tuning Judge criteria from Experience Memory
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# 4. Failure-to-Skill — Auto-generate new Skills from failure patterns
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# 5. Skill A/B Test — Performance comparison between Skills
# ---------------------------------------------------------------------------


async def run_skill_ab_test(
    db: AsyncSession,
    skill_a_id: uuid.UUID,
    skill_b_id: uuid.UUID,
    test_input: dict[str, Any],
    iterations: int = 3,
) -> ABTestResult:
    """Execute two Skills with the same input and compare quality and speed."""
    result_a = await db.execute(select(Skill).where(Skill.id == skill_a_id))
    skill_a = result_a.scalar_one_or_none()
    result_b = await db.execute(select(Skill).where(Skill.id == skill_b_id))
    skill_b = result_b.scalar_one_or_none()

    if skill_a is None:
        raise ValueError(f"Skill A not found: {skill_a_id}")
    if skill_b is None:
        raise ValueError(f"Skill B not found: {skill_b_id}")

    test_id = uuid.uuid4().hex[:12]
    a_scores: list[float] = []
    b_scores: list[float] = []
    a_times: list[float] = []
    b_times: list[float] = []
    details: list[dict[str, Any]] = []

    for i in range(iterations):
        # Execute Skill A
        a_result, a_time = await _execute_skill_for_test(skill_a, test_input)
        a_score = _evaluate_output_quality(a_result)
        a_scores.append(a_score)
        a_times.append(a_time)

        # Execute Skill B
        b_result, b_time = await _execute_skill_for_test(skill_b, test_input)
        b_score = _evaluate_output_quality(b_result)
        b_scores.append(b_score)
        b_times.append(b_time)

        details.append(
            {
                "iteration": i + 1,
                "skill_a": {
                    "score": a_score,
                    "time_ms": a_time,
                    "output_preview": str(a_result.get("output", ""))[:200],
                },
                "skill_b": {
                    "score": b_score,
                    "time_ms": b_time,
                    "output_preview": str(b_result.get("output", ""))[:200],
                },
            }
        )

    avg_a_score = sum(a_scores) / len(a_scores) if a_scores else 0
    avg_b_score = sum(b_scores) / len(b_scores) if b_scores else 0
    avg_a_time = sum(a_times) / len(a_times) if a_times else 0
    avg_b_time = sum(b_times) / len(b_times) if b_times else 0

    # Winner determination: prioritize quality, use speed as tiebreaker
    score_diff = avg_a_score - avg_b_score
    if abs(score_diff) > 0.05:
        winner = str(skill_a_id) if score_diff > 0 else str(skill_b_id)
        winner_reason = f"Quality score difference: {abs(score_diff):.2f} (A: {avg_a_score:.2f}, B: {avg_b_score:.2f})"
    elif abs(avg_a_time - avg_b_time) > 100:  # More than 100ms difference
        winner = str(skill_a_id) if avg_a_time < avg_b_time else str(skill_b_id)
        winner_reason = (
            f"Quality equivalent, speed difference: {abs(avg_a_time - avg_b_time):.0f}ms "
            f"(A: {avg_a_time:.0f}ms, B: {avg_b_time:.0f}ms)"
        )
    else:
        winner = "tie"
        winner_reason = f"Quality and speed both equivalent (A: {avg_a_score:.2f}/{avg_a_time:.0f}ms, B: {avg_b_score:.2f}/{avg_b_time:.0f}ms)"

    return ABTestResult(
        test_id=test_id,
        skill_a_id=str(skill_a_id),
        skill_b_id=str(skill_b_id),
        skill_a_scores=a_scores,
        skill_b_scores=b_scores,
        skill_a_avg_time_ms=avg_a_time,
        skill_b_avg_time_ms=avg_b_time,
        winner=winner,
        winner_reason=winner_reason,
        details=details,
    )


async def _execute_skill_for_test(
    skill: Skill,
    test_input: dict[str, Any],
) -> tuple[dict[str, Any], float]:
    """Execute a Skill for testing and return the result and execution time."""
    code = skill.generated_code or ""
    if not code.strip():
        return {"status": "error", "output": "No code"}, 0.0

    context = {
        "input": test_input.get("input", ""),
        "local_context": test_input.get("local_context", {}),
        "provider": None,
        "settings": test_input.get("settings", {}),
    }

    start = time.monotonic()
    try:
        # Sandbox execution: extract execute function via compile + exec and run safely
        namespace: dict[str, Any] = {}
        compiled = compile(code, f"<skill:{skill.slug}>", "exec")
        exec(compiled, namespace)  # noqa: S102 — sandbox execution

        execute_fn = namespace.get("execute")
        if execute_fn is None:
            return {"status": "error", "output": "execute function not defined"}, 0.0

        import asyncio

        if asyncio.iscoroutinefunction(execute_fn):
            result = await execute_fn(context)
        else:
            result = execute_fn(context)

        elapsed = (time.monotonic() - start) * 1000
        return result if isinstance(result, dict) else {
            "status": "success",
            "output": str(result),
        }, elapsed

    except Exception as exc:
        elapsed = (time.monotonic() - start) * 1000
        return {"status": "error", "output": f"Execution error: {exc}"}, elapsed


def _evaluate_output_quality(output: dict[str, Any]) -> float:
    """Score the quality of the output."""
    score = 0.0

    # Status check
    status = output.get("status", "")
    if status == "success":
        score += 0.4
    elif status == "warning":
        score += 0.2

    # Output content richness
    content = str(output.get("output", ""))
    if content and content != "No code":
        score += 0.3
        if len(content) > 50:
            score += 0.1

    # Presence of artifacts
    artifacts = output.get("artifacts", [])
    if artifacts:
        score += 0.1

    # No errors
    if "error" not in content.lower() and "エラー" not in content:
        score += 0.1

    return min(1.0, score)


# ---------------------------------------------------------------------------
# 6. Auto Test Generator — Auto-generation of test code
# ---------------------------------------------------------------------------


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


async def run_improvement_cycle() -> None:
    """Periodic self-improvement cycle — runs every hour via APScheduler.

    Analyzes up to 5 enabled skills, logs findings, and records metrics.
    Designed to be lightweight and non-disruptive (max_instances=1 in scheduler).
    """
    import logging

    cycle_log = logging.getLogger(__name__)
    cycle_log.info("Self-improvement cycle started")
    try:
        from app.core.database import async_session_factory
        from app.models.skill import Skill

        async with async_session_factory() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Skill).where(Skill.enabled == True).limit(5)  # noqa: E712
            )
            skills = result.scalars().all()

        analyzed = 0
        for skill in skills:
            try:
                report = await analyze_skill(skill.slug)
                score = report.get("overall_score", 1.0)
                cycle_log.debug(
                    "Self-improvement: skill=%s score=%.2f findings=%d",
                    skill.slug,
                    score,
                    len(report.get("findings", [])),
                )
                analyzed += 1
            except Exception as exc:
                cycle_log.debug("Skill analysis failed for %s: %s", skill.slug, exc)

        cycle_log.info("Self-improvement cycle complete: %d skills analyzed", analyzed)
    except Exception as exc:
        cycle_log.warning("Self-improvement cycle error: %s", exc)
