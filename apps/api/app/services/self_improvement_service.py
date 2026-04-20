"""Backward-compatible facade for the self-improvement skill package.

v0.1.7 split the 1,500-line module into the ``app.services.self_improvement``
package (one sub-module per skill). Existing callers importing from
``app.services.self_improvement_service`` keep working because this file
re-exports everything.

For new code, import directly from the package::

    from app.services.self_improvement import analyze_skill, improve_skill
"""

from __future__ import annotations

from app.services.self_improvement import (
    ABTestConfig,
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
    analyze_skill,
    apply_improvement,
    apply_judge_tuning,
    generate_skills_from_failures,
    generate_tests_for_skill,
    improve_skill,
    run_improvement_cycle,
    run_skill_ab_test,
    tune_judge_from_experience,
)

__all__ = [
    "ABTestConfig",
    "ABTestResult",
    "AnalysisCategory",
    "AnalysisFinding",
    "AutoTestResult",
    "FailureToSkillProposal",
    "GeneratedTestCase",
    "ImprovementPriority",
    "JudgeTuningResult",
    "JudgeTuningRule",
    "SkillAnalysisResult",
    "SkillImprovementProposal",
    "analyze_skill",
    "apply_improvement",
    "apply_judge_tuning",
    "generate_skills_from_failures",
    "generate_tests_for_skill",
    "improve_skill",
    "run_improvement_cycle",
    "run_skill_ab_test",
    "tune_judge_from_experience",
]
