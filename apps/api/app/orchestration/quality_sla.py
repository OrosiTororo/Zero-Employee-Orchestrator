"""Quality SLA — Quality mode definition + model selection.

Switches models, retry limits, and Judge thresholds based on quality mode.
Managed as SLA policies and applied at the Ticket / Task level.
"""

from dataclasses import dataclass
from enum import Enum


class QualityMode(str, Enum):
    """Quality mode: model selection guideline based on task importance."""

    DRAFT = "draft"  # Fast and low-cost (for drafts)
    STANDARD = "standard"  # Standard quality
    HIGH = "high"  # High quality (multi-model verification)
    CRITICAL = "critical"  # Highest quality (human review required)


@dataclass
class QualitySLAConfig:
    """Configuration values per quality mode."""

    mode: QualityMode
    preferred_models: list[str]
    fallback_models: list[str]
    max_retries: int
    judge_pass_threshold: float  # 0.0 - 1.0
    requires_human_review: bool
    cross_model_verification: bool
    max_tokens: int


# ---------------------------------------------------------------------------
# Default quality mode settings
# Dynamically loads model lists from ModelRegistry (model_catalog.json).
# Uses inline fallback when the catalog is unavailable.
# ---------------------------------------------------------------------------

_SLA_STATIC = {
    QualityMode.DRAFT: {
        "max_retries": 1,
        "judge_pass_threshold": 0.5,
        "requires_human_review": False,
        "cross_model_verification": False,
        "max_tokens": 2000,
    },
    QualityMode.STANDARD: {
        "max_retries": 2,
        "judge_pass_threshold": 0.7,
        "requires_human_review": False,
        "cross_model_verification": False,
        "max_tokens": 4000,
    },
    QualityMode.HIGH: {
        "max_retries": 3,
        "judge_pass_threshold": 0.85,
        "requires_human_review": False,
        "cross_model_verification": True,
        "max_tokens": 8000,
    },
    QualityMode.CRITICAL: {
        "max_retries": 5,
        "judge_pass_threshold": 0.95,
        "requires_human_review": True,
        "cross_model_verification": True,
        "max_tokens": 16000,
    },
}

# Inline fallback model lists (used only when model_catalog.json is missing)
_FALLBACK_SLA_MODELS = {
    QualityMode.DRAFT: {
        "preferred": ["openai/gpt-mini", "anthropic/claude-haiku"],
        "fallback": ["gemini/gemini-flash-lite"],
    },
    QualityMode.STANDARD: {
        "preferred": ["openai/gpt", "anthropic/claude-sonnet"],
        "fallback": ["openai/gpt-mini", "anthropic/claude-haiku"],
    },
    QualityMode.HIGH: {
        "preferred": ["openai/gpt", "anthropic/claude-sonnet"],
        "fallback": ["anthropic/claude-opus", "gemini/gemini-pro"],
    },
    QualityMode.CRITICAL: {
        "preferred": ["anthropic/claude-opus", "openai/gpt"],
        "fallback": ["anthropic/claude-sonnet", "gemini/gemini-pro"],
    },
}


def _load_sla_models(mode: QualityMode) -> dict[str, list[str]]:
    """Load model lists per quality mode from ModelRegistry."""
    mode_key = mode.value  # "draft", "standard", etc.
    try:
        from app.providers.model_registry import get_model_registry

        registry = get_model_registry()
        if registry.model_count > 0:
            return registry.get_sla_models(mode_key)
    except Exception:
        pass
    return _FALLBACK_SLA_MODELS[mode]


def _build_sla_configs() -> dict[QualityMode, QualitySLAConfig]:
    configs: dict[QualityMode, QualitySLAConfig] = {}
    for mode, params in _SLA_STATIC.items():
        models = _load_sla_models(mode)
        configs[mode] = QualitySLAConfig(
            mode=mode,
            preferred_models=models["preferred"],
            fallback_models=models["fallback"],
            **params,
        )
    return configs


DEFAULT_SLA_CONFIGS: dict[QualityMode, QualitySLAConfig] = _build_sla_configs()


def get_sla_config(mode: QualityMode | str) -> QualitySLAConfig:
    """Get SLA config for a quality mode."""
    if isinstance(mode, str):
        mode = QualityMode(mode)
    return DEFAULT_SLA_CONFIGS[mode]


def select_model(
    mode: QualityMode | str,
    available_models: list[str] | None = None,
) -> str:
    """Select the optimal model from quality mode and available models."""
    config = get_sla_config(mode)
    candidates = config.preferred_models + config.fallback_models

    if available_models is None:
        return candidates[0]

    for model in candidates:
        if model in available_models:
            return model

    # If no model is available from candidates, return the first available model
    if available_models:
        return available_models[0]

    return candidates[0]


def should_cross_verify(mode: QualityMode | str) -> bool:
    """Determine whether cross-model verification is required."""
    return get_sla_config(mode).cross_model_verification


def should_human_review(mode: QualityMode | str) -> bool:
    """Determine whether human review is required."""
    return get_sla_config(mode).requires_human_review
