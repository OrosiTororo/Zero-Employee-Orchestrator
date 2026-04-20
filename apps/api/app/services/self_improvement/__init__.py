"""AI Self-Improvement package — six skill modules.

Re-exports the public functions and data classes so legacy callers can still::

    from app.services.self_improvement_service import analyze_skill

after the v0.1.7 split without code changes.
"""

from __future__ import annotations

from app.services.self_improvement.ab_test import run_skill_ab_test
from app.services.self_improvement.batch import run_improvement_cycle
from app.services.self_improvement.failure_to_skill import generate_skills_from_failures
from app.services.self_improvement.judge_tuner import (
    apply_judge_tuning,
    tune_judge_from_experience,
)
from app.services.self_improvement.skill_analyzer import analyze_skill
from app.services.self_improvement.skill_improver import apply_improvement, improve_skill
from app.services.self_improvement.test_generator import generate_tests_for_skill
from app.services.self_improvement_models import (
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
