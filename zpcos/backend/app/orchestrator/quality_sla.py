"""Quality SLA Selector — 品質モードに基づくモデル・Judge 設定。"""

from enum import Enum


class QualityMode(str, Enum):
    FASTEST = "fastest"
    BALANCED = "balanced"
    HIGH_QUALITY = "high_quality"


def get_model_for_mode(mode: QualityMode, task_complexity: str = "normal") -> str:
    """品質モードとタスク複雑度からモデルグループを決定。"""
    if mode == QualityMode.FASTEST:
        return "fast"
    elif mode == QualityMode.BALANCED:
        return "quality" if task_complexity == "complex" else "fast"
    else:  # HIGH_QUALITY
        return "reason" if task_complexity == "complex" else "quality"


def should_run_judge(mode: QualityMode) -> bool:
    """品質モードに基づいて Judge を実行するか。"""
    return mode != QualityMode.FASTEST


def get_judge_config(mode: QualityMode) -> dict:
    """品質モードに基づく Judge 設定。"""
    if mode == QualityMode.FASTEST:
        return {"enabled": False}
    elif mode == QualityMode.BALANCED:
        return {"enabled": True, "two_stage": True, "runs": 1}
    else:
        return {"enabled": True, "two_stage": True, "runs": 2}
