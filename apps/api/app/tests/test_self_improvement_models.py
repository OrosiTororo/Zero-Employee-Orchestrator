"""Tests for the extracted self_improvement data models.

The data-model classes moved out of ``self_improvement_service.py`` in v0.1.8.
This file asserts (a) every class is importable from the dedicated models
module and (b) the facade ``self_improvement_service`` still re-exports them
so downstream route handlers don't need to change their imports.
"""

from __future__ import annotations

import pytest

from app.services import self_improvement_models as models
from app.services import self_improvement_service as facade

_EXPECTED_NAMES = (
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
)


@pytest.mark.parametrize("name", _EXPECTED_NAMES)
def test_each_model_is_re_exported_from_service_facade(name: str):
    model_cls = getattr(models, name)
    facade_cls = getattr(facade, name)
    assert model_cls is facade_cls, f"{name} diverged from its models-module definition"


def test_analysis_finding_constructs_cleanly():
    f = models.AnalysisFinding(
        category=models.AnalysisCategory.SECURITY,
        priority=models.ImprovementPriority.HIGH,
        title="example",
        description="desc",
        suggestion="fix",
    )
    assert f.category == models.AnalysisCategory.SECURITY
    assert f.priority == models.ImprovementPriority.HIGH
    assert f.line_range is None


def test_skill_analysis_result_sets_default_timestamp():
    r = models.SkillAnalysisResult(
        skill_id="s1",
        skill_slug="demo",
        overall_score=0.85,
        findings=[],
        summary="ok",
    )
    assert r.analyzed_at  # auto-populated in __post_init__


def test_ab_test_config_generates_id_if_missing():
    c = models.ABTestConfig(
        test_id="",
        skill_a_id="a",
        skill_b_id="b",
        test_input={},
    )
    assert c.test_id  # uuid hex slug


def test_auto_test_result_sets_default_timestamp():
    r = models.AutoTestResult(
        skill_id="s1",
        skill_slug="demo",
        test_cases=[],
        total_tests=0,
        normal_tests=0,
        edge_tests=0,
        error_tests=0,
    )
    assert r.generated_at
