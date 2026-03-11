"""Domain Skills -- 汎用ドメインスキル群.

Zero-Employee Orchestrator の汎用ビジネススキル。
YouTube 固有のスキルを排し、あらゆる業務ドメインで利用可能な
5 つの専門スキルを提供する。

各スキルは以下のインターフェースに準拠する:
  - SKILL_MANIFEST: メタデータ辞書
  - execute(context) -> dict: スキル実行
  - accepts_artifact_types() -> list[str]: 受け入れ可能な成果物タイプ
  - produces_artifact_types() -> list[str]: 生成する成果物タイプ
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# i18n helpers (self-contained -- no dependency on core.i18n at import time)
# ---------------------------------------------------------------------------

_I18N: dict[str, dict[str, str]] = {
    # -- ContentCreatorSkill --
    "content_creator_name": {
        "ja": "コンテンツ作成",
        "en": "Content Creator",
        "zh": "内容创作",
    },
    "content_creator_desc": {
        "ja": "ブログ、SNS、メール、動画台本、プレゼンなど、あらゆるプラットフォーム向けの構造化コンテンツを生成する",
        "en": "Generate structured content for any platform: blog posts, social media, email newsletters, video scripts, presentations",
        "zh": "为任何平台生成结构化内容：博客、社交媒体、电子邮件通讯、视频脚本、演示文稿",
    },
    # -- CompetitorAnalysisSkill --
    "competitor_analysis_name": {
        "ja": "競合分析",
        "en": "Competitor Analysis",
        "zh": "竞争分析",
    },
    "competitor_analysis_desc": {
        "ja": "市場分析、SWOT、価格比較、機能比較など、あらゆるドメインの競合を分析する",
        "en": "Analyze competitors in any domain: market analysis, SWOT, pricing comparison, feature comparison",
        "zh": "分析任何领域的竞争对手：市场分析、SWOT、价格比较、功能比较",
    },
    # -- TrendAnalysisSkill --
    "trend_analysis_name": {
        "ja": "トレンド分析",
        "en": "Trend Analysis",
        "zh": "趋势分析",
    },
    "trend_analysis_desc": {
        "ja": "市場・技術・SNS・業界など、あらゆるドメインのトレンドを分析する",
        "en": "Analyze trends in any domain: market, technology, social media, industry trends",
        "zh": "分析任何领域的趋势：市场、技术、社交媒体、行业趋势",
    },
    # -- PerformanceAnalysisSkill --
    "performance_analysis_name": {
        "ja": "パフォーマンス分析",
        "en": "Performance Analysis",
        "zh": "绩效分析",
    },
    "performance_analysis_desc": {
        "ja": "KPI追跡、ROI分析、コンバージョン分析、エンゲージメント指標など、業務パフォーマンスを分析する",
        "en": "Analyze performance metrics: KPI tracking, ROI analysis, conversion analysis, engagement metrics",
        "zh": "分析绩效指标：KPI跟踪、ROI分析、转化分析、参与度指标",
    },
    # -- StrategyAdvisorSkill --
    "strategy_advisor_name": {
        "ja": "戦略アドバイザー",
        "en": "Strategy Advisor",
        "zh": "战略顾问",
    },
    "strategy_advisor_desc": {
        "ja": "次のアクション、リソース配分、リスク評価、機会特定など、クロスドメインの戦略的提言を行う",
        "en": "Cross-domain strategic recommendations: next actions, resource allocation, risk assessment, opportunity identification",
        "zh": "跨领域战略建议：下一步行动、资源分配、风险评估、机会识别",
    },
}


def _t(key: str, lang: str = "en") -> str:
    """Translate a key for the given language."""
    entry = _I18N.get(key)
    if entry is None:
        return key
    return entry.get(lang, entry.get("en", key))


# ---------------------------------------------------------------------------
# Base Skill
# ---------------------------------------------------------------------------


class BaseDomainSkill(ABC):
    """全ドメインスキル共通の基底クラス."""

    SKILL_MANIFEST: dict[str, Any] = {}

    @classmethod
    @abstractmethod
    def accepts_artifact_types(cls) -> list[str]:
        """このスキルが入力として受け入れるアーティファクトタイプ."""
        ...

    @classmethod
    @abstractmethod
    def produces_artifact_types(cls) -> list[str]:
        """このスキルが出力として生成するアーティファクトタイプ."""
        ...

    @abstractmethod
    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """スキルを実行する.

        Args:
            context: 実行コンテキスト（入力パラメータ + artifact_refs など）

        Returns:
            実行結果辞書
        """
        ...

    # -- helpers --

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _base_result(self, *, skill_id: str, status: str = "completed") -> dict[str, Any]:
        return {
            "skill_id": skill_id,
            "status": status,
            "generated_at": self._now_iso(),
        }


# ---------------------------------------------------------------------------
# 1. ContentCreatorSkill
# ---------------------------------------------------------------------------

_CONTENT_SECTIONS = {
    "blog": ["introduction", "body", "conclusion", "cta"],
    "social_media": ["hook", "body", "hashtags", "cta"],
    "email_newsletter": ["subject_line", "preview_text", "body", "cta"],
    "video_script": ["hook", "intro", "main_points", "outro", "cta"],
    "presentation": ["title_slide", "agenda", "slides", "summary", "cta"],
}


class ContentCreatorSkill(BaseDomainSkill):
    """あらゆるプラットフォーム向けの構造化コンテンツを生成するスキル."""

    SKILL_MANIFEST: dict[str, Any] = {
        "id": "content-creator",
        "name": {lang: _t("content_creator_name", lang) for lang in ("ja", "en", "zh")},
        "description": {lang: _t("content_creator_desc", lang) for lang in ("ja", "en", "zh")},
        "version": "1.0.0",
        "domain": "content",
        "is_system_protected": False,
        "input_schema": {
            "type": "object",
            "required": ["topic", "content_type"],
            "properties": {
                "topic": {"type": "string", "description": "Content topic / subject"},
                "platform": {"type": "string", "description": "Target platform (e.g. blog, twitter, youtube)"},
                "tone": {"type": "string", "description": "Writing tone (formal, casual, persuasive, etc.)"},
                "target_audience": {"type": "string", "description": "Intended audience"},
                "content_type": {
                    "type": "string",
                    "enum": list(_CONTENT_SECTIONS.keys()),
                    "description": "Type of content to generate",
                },
                "artifact_refs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Artifact IDs to use as context (e.g. trend reports)",
                },
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "object", "description": "Structured content with sections"},
                "metadata": {"type": "object"},
            },
        },
    }

    @classmethod
    def accepts_artifact_types(cls) -> list[str]:
        return [
            "trend_report",
            "competitor_report",
            "performance_report",
            "strategy_plan",
            "market_context",
            "document",
            "spec",
        ]

    @classmethod
    def produces_artifact_types(cls) -> list[str]:
        return ["structured_content", "document"]

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """コンテンツのテンプレート構造を生成する.

        実運用では LLM が内容を充実させる。
        このスキルは構造テンプレートと指示を提供する。
        """
        topic = context.get("topic", "")
        content_type = context.get("content_type", "blog")
        platform = context.get("platform", "")
        tone = context.get("tone", "neutral")
        target_audience = context.get("target_audience", "general")
        artifact_refs = context.get("artifact_refs", [])

        sections = _CONTENT_SECTIONS.get(content_type, _CONTENT_SECTIONS["blog"])

        result = self._base_result(skill_id="content-creator")
        result.update({
            "content": {
                "topic": topic,
                "content_type": content_type,
                "platform": platform,
                "tone": tone,
                "target_audience": target_audience,
                "sections": {section: "" for section in sections},
            },
            "metadata": {
                "section_order": sections,
                "artifact_refs_used": artifact_refs,
            },
            "artifact_types_produced": self.produces_artifact_types(),
        })
        return result


# ---------------------------------------------------------------------------
# 2. CompetitorAnalysisSkill
# ---------------------------------------------------------------------------

_ANALYSIS_TYPES = ("market_analysis", "swot", "pricing_comparison", "feature_comparison")


class CompetitorAnalysisSkill(BaseDomainSkill):
    """あらゆるドメインの競合を分析するスキル."""

    SKILL_MANIFEST: dict[str, Any] = {
        "id": "competitor-analysis",
        "name": {lang: _t("competitor_analysis_name", lang) for lang in ("ja", "en", "zh")},
        "description": {lang: _t("competitor_analysis_desc", lang) for lang in ("ja", "en", "zh")},
        "version": "1.0.0",
        "domain": "analysis",
        "is_system_protected": False,
        "input_schema": {
            "type": "object",
            "required": ["domain", "competitors"],
            "properties": {
                "domain": {"type": "string", "description": "Business domain to analyze"},
                "competitors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of competitor names or identifiers",
                },
                "analysis_type": {
                    "type": "string",
                    "enum": list(_ANALYSIS_TYPES),
                    "description": "Type of analysis to perform",
                },
                "data_sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Data sources to reference",
                },
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "analysis": {"type": "object"},
                "metadata": {"type": "object"},
            },
        },
    }

    @classmethod
    def accepts_artifact_types(cls) -> list[str]:
        return ["trend_report", "performance_report", "market_context", "data", "document"]

    @classmethod
    def produces_artifact_types(cls) -> list[str]:
        return ["competitor_report", "report"]

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        domain = context.get("domain", "")
        competitors = context.get("competitors", [])
        analysis_type = context.get("analysis_type", "market_analysis")
        data_sources = context.get("data_sources", [])

        # Build structure based on analysis type
        if analysis_type == "swot":
            analysis_structure: dict[str, Any] = {
                "competitors": {
                    comp: {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
                    for comp in competitors
                },
            }
        elif analysis_type == "pricing_comparison":
            analysis_structure = {
                "competitors": {
                    comp: {"pricing_tiers": [], "value_proposition": "", "price_range": ""}
                    for comp in competitors
                },
            }
        elif analysis_type == "feature_comparison":
            analysis_structure = {
                "competitors": {
                    comp: {"features": [], "unique_selling_points": [], "gaps": []}
                    for comp in competitors
                },
            }
        else:  # market_analysis
            analysis_structure = {
                "competitors": {
                    comp: {"market_share": "", "positioning": "", "key_differentiators": []}
                    for comp in competitors
                },
                "market_overview": "",
            }

        result = self._base_result(skill_id="competitor-analysis")
        result.update({
            "analysis": {
                "domain": domain,
                "analysis_type": analysis_type,
                **analysis_structure,
            },
            "metadata": {
                "competitor_count": len(competitors),
                "data_sources": data_sources,
            },
            "artifact_types_produced": self.produces_artifact_types(),
        })
        return result


# ---------------------------------------------------------------------------
# 3. TrendAnalysisSkill
# ---------------------------------------------------------------------------

_TREND_CATEGORIES = ("market", "technology", "social_media", "industry")


class TrendAnalysisSkill(BaseDomainSkill):
    """あらゆるドメインのトレンドを分析するスキル."""

    SKILL_MANIFEST: dict[str, Any] = {
        "id": "trend-analysis",
        "name": {lang: _t("trend_analysis_name", lang) for lang in ("ja", "en", "zh")},
        "description": {lang: _t("trend_analysis_desc", lang) for lang in ("ja", "en", "zh")},
        "version": "1.0.0",
        "domain": "analysis",
        "is_system_protected": False,
        "input_schema": {
            "type": "object",
            "required": ["domain"],
            "properties": {
                "domain": {"type": "string", "description": "Domain to analyze trends in"},
                "timeframe": {
                    "type": "string",
                    "description": "Time range (e.g. '30d', '6m', '1y')",
                },
                "data_sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Data sources for trend detection",
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords to track",
                },
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "trends": {"type": "array"},
                "insights": {"type": "array"},
                "recommendations": {"type": "array"},
            },
        },
    }

    @classmethod
    def accepts_artifact_types(cls) -> list[str]:
        return ["performance_report", "competitor_report", "data", "document"]

    @classmethod
    def produces_artifact_types(cls) -> list[str]:
        return ["trend_report", "market_context", "report"]

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        domain = context.get("domain", "")
        timeframe = context.get("timeframe", "30d")
        data_sources = context.get("data_sources", [])
        keywords = context.get("keywords", [])

        result = self._base_result(skill_id="trend-analysis")
        result.update({
            "trends": [],
            "insights": [],
            "recommendations": [],
            "metadata": {
                "domain": domain,
                "timeframe": timeframe,
                "data_sources": data_sources,
                "keywords_tracked": keywords,
                "trend_categories": list(_TREND_CATEGORIES),
            },
            "artifact_types_produced": self.produces_artifact_types(),
        })
        return result


# ---------------------------------------------------------------------------
# 4. PerformanceAnalysisSkill
# ---------------------------------------------------------------------------

_METRIC_TYPES = ("kpi_tracking", "roi_analysis", "conversion_analysis", "engagement_metrics")


class PerformanceAnalysisSkill(BaseDomainSkill):
    """業務パフォーマンスを分析するスキル."""

    SKILL_MANIFEST: dict[str, Any] = {
        "id": "performance-analysis",
        "name": {lang: _t("performance_analysis_name", lang) for lang in ("ja", "en", "zh")},
        "description": {lang: _t("performance_analysis_desc", lang) for lang in ("ja", "en", "zh")},
        "version": "1.0.0",
        "domain": "analytics",
        "is_system_protected": False,
        "input_schema": {
            "type": "object",
            "required": ["domain", "metrics"],
            "properties": {
                "domain": {"type": "string", "description": "Business domain"},
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Metrics to analyze",
                },
                "timeframe": {"type": "string", "description": "Analysis period"},
                "benchmarks": {
                    "type": "object",
                    "description": "Benchmark values for comparison",
                },
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "performance_data": {"type": "object"},
                "visualizations": {"type": "array"},
                "summary": {"type": "string"},
            },
        },
    }

    @classmethod
    def accepts_artifact_types(cls) -> list[str]:
        return ["trend_report", "competitor_report", "data", "document"]

    @classmethod
    def produces_artifact_types(cls) -> list[str]:
        return ["performance_report", "report", "data"]

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        domain = context.get("domain", "")
        metrics = context.get("metrics", [])
        timeframe = context.get("timeframe", "30d")
        benchmarks = context.get("benchmarks", {})

        metric_results: dict[str, dict[str, Any]] = {}
        for metric in metrics:
            metric_results[metric] = {
                "current_value": None,
                "previous_value": None,
                "change_pct": None,
                "benchmark": benchmarks.get(metric),
                "status": "pending",
            }

        result = self._base_result(skill_id="performance-analysis")
        result.update({
            "performance_data": {
                "domain": domain,
                "timeframe": timeframe,
                "metrics": metric_results,
            },
            "visualizations": [],
            "summary": "",
            "metadata": {
                "metric_count": len(metrics),
                "has_benchmarks": bool(benchmarks),
            },
            "artifact_types_produced": self.produces_artifact_types(),
        })
        return result


# ---------------------------------------------------------------------------
# 5. StrategyAdvisorSkill
# ---------------------------------------------------------------------------


class StrategyAdvisorSkill(BaseDomainSkill):
    """クロスドメインの戦略的提言を行うスキル.

    他のスキルの出力成果物（トレンド分析、競合分析、パフォーマンス分析）を
    統合し、優先付きのアクションプランを生成する。
    """

    SKILL_MANIFEST: dict[str, Any] = {
        "id": "strategy-advisor",
        "name": {lang: _t("strategy_advisor_name", lang) for lang in ("ja", "en", "zh")},
        "description": {lang: _t("strategy_advisor_desc", lang) for lang in ("ja", "en", "zh")},
        "version": "1.0.0",
        "domain": "strategy",
        "is_system_protected": False,
        "input_schema": {
            "type": "object",
            "required": ["domain", "current_state", "goals"],
            "properties": {
                "domain": {"type": "string", "description": "Business domain"},
                "current_state": {"type": "string", "description": "Description of current situation"},
                "goals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Strategic goals to achieve",
                },
                "constraints": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Constraints (budget, time, resources, etc.)",
                },
                "artifact_refs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Artifact IDs from other skills (trend, competitor, performance reports)",
                },
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "action_plan": {"type": "array"},
                "risk_assessment": {"type": "array"},
                "opportunities": {"type": "array"},
                "rationale": {"type": "string"},
            },
        },
    }

    @classmethod
    def accepts_artifact_types(cls) -> list[str]:
        return [
            "trend_report",
            "competitor_report",
            "performance_report",
            "market_context",
            "structured_content",
            "document",
            "report",
            "spec",
            "plan",
        ]

    @classmethod
    def produces_artifact_types(cls) -> list[str]:
        return ["strategy_plan", "report"]

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        domain = context.get("domain", "")
        current_state = context.get("current_state", "")
        goals = context.get("goals", [])
        constraints = context.get("constraints", [])
        artifact_refs = context.get("artifact_refs", [])

        result = self._base_result(skill_id="strategy-advisor")
        result.update({
            "action_plan": [],
            "risk_assessment": [],
            "opportunities": [],
            "rationale": "",
            "metadata": {
                "domain": domain,
                "current_state_summary": current_state[:200] if current_state else "",
                "goal_count": len(goals),
                "constraint_count": len(constraints),
                "artifact_refs_used": artifact_refs,
            },
            "artifact_types_produced": self.produces_artifact_types(),
        })
        return result


# ---------------------------------------------------------------------------
# Registry helper -- list all domain skills
# ---------------------------------------------------------------------------

DOMAIN_SKILLS: list[type[BaseDomainSkill]] = [
    ContentCreatorSkill,
    CompetitorAnalysisSkill,
    TrendAnalysisSkill,
    PerformanceAnalysisSkill,
    StrategyAdvisorSkill,
]


def get_domain_skill_manifests() -> list[dict[str, Any]]:
    """全ドメインスキルの SKILL_MANIFEST を返す."""
    return [cls.SKILL_MANIFEST for cls in DOMAIN_SKILLS]


def get_domain_skill_by_id(skill_id: str) -> type[BaseDomainSkill] | None:
    """スキル ID からスキルクラスを取得する."""
    for cls in DOMAIN_SKILLS:
        if cls.SKILL_MANIFEST.get("id") == skill_id:
            return cls
    return None
