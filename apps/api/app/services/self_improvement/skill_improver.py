"""Skill Improver — generate improved Skill versions from analysis results."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.security.prompt_guard import wrap_external_data
from app.services.self_improvement.skill_analyzer import analyze_skill
from app.services.self_improvement_models import (
    AnalysisCategory,
    AnalysisFinding,
    SkillAnalysisResult,
    SkillImprovementProposal,
)
from app.services.skill_service import analyze_code_safety
from app.utils.json_parser import safe_extract_json

logger = logging.getLogger(__name__)

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
