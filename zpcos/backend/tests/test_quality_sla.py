"""Quality SLA テスト"""

from app.orchestrator.quality_sla import (
    QualityMode,
    get_model_for_mode,
    should_run_judge,
    get_judge_config,
)


def test_fastest_model():
    model = get_model_for_mode(QualityMode.FASTEST)
    assert model in ("fast", "free")


def test_high_quality_model():
    model = get_model_for_mode(QualityMode.HIGH_QUALITY)
    assert model in ("quality", "think")


def test_judge_not_run_for_fastest():
    assert not should_run_judge(QualityMode.FASTEST)


def test_judge_runs_for_high_quality():
    assert should_run_judge(QualityMode.HIGH_QUALITY)


def test_judge_config_fastest_disabled():
    config = get_judge_config(QualityMode.FASTEST)
    assert config["enabled"] is False


def test_judge_config_high_quality_enabled():
    config = get_judge_config(QualityMode.HIGH_QUALITY)
    assert config["enabled"] is True
    assert "runs" in config
    assert config["runs"] >= 1
