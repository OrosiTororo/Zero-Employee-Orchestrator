"""Builtin Skills パッケージ.

Zero-Employee Orchestrator に標準搭載されるスキル群。
各スキルは単一目的の専門モジュールとして実装される。

System-protected skills (6):
  spec_writer, plan_writer, task_breakdown, review_assistant,
  artifact_summarizer, local_context

Domain skills (5):
  ContentCreatorSkill, CompetitorAnalysisSkill, TrendAnalysisSkill,
  PerformanceAnalysisSkill, StrategyAdvisorSkill
"""

from skills.builtin.domain_skills import (  # noqa: F401
    DOMAIN_SKILLS,
    BaseDomainSkill,
    CompetitorAnalysisSkill,
    ContentCreatorSkill,
    PerformanceAnalysisSkill,
    StrategyAdvisorSkill,
    TrendAnalysisSkill,
    get_domain_skill_by_id,
    get_domain_skill_manifests,
)

__all__ = [
    # Base
    "BaseDomainSkill",
    # Domain skills
    "ContentCreatorSkill",
    "CompetitorAnalysisSkill",
    "TrendAnalysisSkill",
    "PerformanceAnalysisSkill",
    "StrategyAdvisorSkill",
    # Registry helpers
    "DOMAIN_SKILLS",
    "get_domain_skill_manifests",
    "get_domain_skill_by_id",
]
