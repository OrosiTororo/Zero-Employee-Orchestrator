"""Skill Analyzer — code-quality analysis for existing Skills.

Extracted from ``self_improvement_service.py`` in v0.1.7 to keep each of the
six self-improvement skills in its own module. Public names are re-exported
from ``self_improvement_service`` for backward compatibility.
"""

from __future__ import annotations

import json
import logging
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.security.prompt_guard import wrap_external_data
from app.services.self_improvement_models import (
    AnalysisCategory,
    AnalysisFinding,
    ImprovementPriority,
    SkillAnalysisResult,
)
from app.services.skill_service import analyze_code_safety
from app.utils.json_parser import safe_extract_json

logger = logging.getLogger(__name__)

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
