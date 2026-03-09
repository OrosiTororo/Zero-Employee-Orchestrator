"""Quality SLA — 品質モード定義＋モデル選択.

品質モードに応じて使用するモデルやリトライ上限、
Judge 閾値を切り替える。SLA ポリシーとして管理し、
Ticket / Task レベルで適用する。
"""

from dataclasses import dataclass
from enum import Enum


class QualityMode(str, Enum):
    """品質モード: タスクの重要度に応じたモデル選択指針."""

    DRAFT = "draft"          # 高速・低コスト (下書き向き)
    STANDARD = "standard"    # 標準品質
    HIGH = "high"            # 高品質 (複数モデル検証)
    CRITICAL = "critical"    # 最高品質 (人間レビュー必須)


@dataclass
class QualitySLAConfig:
    """品質モード別の設定値."""

    mode: QualityMode
    preferred_models: list[str]
    fallback_models: list[str]
    max_retries: int
    judge_pass_threshold: float  # 0.0 - 1.0
    requires_human_review: bool
    cross_model_verification: bool
    max_tokens: int


# デフォルト品質モード設定
DEFAULT_SLA_CONFIGS: dict[QualityMode, QualitySLAConfig] = {
    QualityMode.DRAFT: QualitySLAConfig(
        mode=QualityMode.DRAFT,
        preferred_models=["gpt-5-mini", "claude-haiku-4-5"],
        fallback_models=["gemini-2.5-flash-lite"],
        max_retries=1,
        judge_pass_threshold=0.5,
        requires_human_review=False,
        cross_model_verification=False,
        max_tokens=2000,
    ),
    QualityMode.STANDARD: QualitySLAConfig(
        mode=QualityMode.STANDARD,
        preferred_models=["gpt-5.4", "claude-sonnet-4-6"],
        fallback_models=["gpt-5-mini", "claude-haiku-4-5"],
        max_retries=2,
        judge_pass_threshold=0.7,
        requires_human_review=False,
        cross_model_verification=False,
        max_tokens=4000,
    ),
    QualityMode.HIGH: QualitySLAConfig(
        mode=QualityMode.HIGH,
        preferred_models=["gpt-5.4", "claude-sonnet-4-6"],
        fallback_models=["claude-opus-4-6", "gemini-2.5-pro"],
        max_retries=3,
        judge_pass_threshold=0.85,
        requires_human_review=False,
        cross_model_verification=True,
        max_tokens=8000,
    ),
    QualityMode.CRITICAL: QualitySLAConfig(
        mode=QualityMode.CRITICAL,
        preferred_models=["claude-opus-4-6", "gpt-5.4"],
        fallback_models=["claude-sonnet-4-6", "gemini-2.5-pro"],
        max_retries=5,
        judge_pass_threshold=0.95,
        requires_human_review=True,
        cross_model_verification=True,
        max_tokens=16000,
    ),
}


def get_sla_config(mode: QualityMode | str) -> QualitySLAConfig:
    """品質モードに対応する SLA 設定を取得."""
    if isinstance(mode, str):
        mode = QualityMode(mode)
    return DEFAULT_SLA_CONFIGS[mode]


def select_model(
    mode: QualityMode | str,
    available_models: list[str] | None = None,
) -> str:
    """品質モードと利用可能モデル一覧から最適モデルを選択."""
    config = get_sla_config(mode)
    candidates = config.preferred_models + config.fallback_models

    if available_models is None:
        return candidates[0]

    for model in candidates:
        if model in available_models:
            return model

    # どのモデルも利用不可の場合、利用可能な最初のモデルを返す
    if available_models:
        return available_models[0]

    return candidates[0]


def should_cross_verify(mode: QualityMode | str) -> bool:
    """クロスモデル検証が必要かどうかを判定."""
    return get_sla_config(mode).cross_model_verification


def should_human_review(mode: QualityMode | str) -> bool:
    """人間レビューが必要かどうかを判定."""
    return get_sla_config(mode).requires_human_review
