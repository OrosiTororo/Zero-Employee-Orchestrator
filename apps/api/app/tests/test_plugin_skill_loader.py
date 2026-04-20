"""Tests for the plugin-skill YAML loader."""

from __future__ import annotations

import pytest
import yaml

from app.services.plugin_skill_loader import (
    PluginSkillValidationError,
    _validate_skill_dict,
    list_plugin_skill_drift,
    load_plugin_manifest_skills,
    load_plugin_skills,
)

# ---------------------------------------------------------------------------
# ai-ceo plugin — realistic end-to-end load
# ---------------------------------------------------------------------------


def test_ai_ceo_loads_five_skills():
    skills = load_plugin_skills("ai-ceo")
    assert len(skills) == 5


def test_ai_ceo_manifest_matches_yaml_files():
    declared, loaded = load_plugin_manifest_skills("ai-ceo")
    assert set(declared) == set(loaded)


def test_ai_ceo_drift_is_zero():
    drift = list_plugin_skill_drift("ai-ceo")
    assert drift["missing_yaml"] == []
    assert drift["extra_yaml"] == []


@pytest.mark.parametrize(
    "slug",
    [
        "ceo-directive-interpreter",
        "ceo-weekly-planner",
        "ceo-delegation-router",
        "ceo-board-briefing",
        "ceo-post-mortem",
    ],
)
def test_each_ai_ceo_skill_has_required_fields(slug: str):
    skills = {s["slug"]: s for s in load_plugin_skills("ai-ceo")}
    skill = skills[slug]
    assert skill["plugin"] == "ai-ceo"
    assert skill["role"] in ("CEO", "CMO", "CTO", "COO")
    assert skill["preferred_model"].startswith("anthropic/")
    assert "system" in skill["prompts"]
    assert skill["security"]["wrap_external_data"] is True


# ---------------------------------------------------------------------------
# Loader / validator behaviour
# ---------------------------------------------------------------------------


def test_missing_plugin_returns_empty_list():
    assert load_plugin_skills("nonexistent-plugin") == []


def test_validate_rejects_missing_required_fields():
    with pytest.raises(PluginSkillValidationError):
        _validate_skill_dict(
            "x",
            {
                "slug": "broken",
                # missing name + version + description
                "security": {
                    "wrap_external_data": True,
                    "pii_guard": True,
                    "sandbox": "none",
                },
            },
        )


def test_validate_rejects_plugin_mismatch():
    with pytest.raises(PluginSkillValidationError):
        _validate_skill_dict(
            "ai-ceo",
            {
                "slug": "foo",
                "name": "Foo",
                "version": "0.1.0",
                "description": "desc",
                "plugin": "different-plugin",
                "security": {
                    "wrap_external_data": True,
                    "pii_guard": False,
                    "sandbox": "none",
                },
            },
        )


def test_validate_rejects_missing_security_block():
    with pytest.raises(PluginSkillValidationError):
        _validate_skill_dict(
            "x",
            {"slug": "no-sec", "name": "N", "version": "0.1.0", "description": "d"},
        )


def test_loader_skips_invalid_yaml_file(tmp_path, monkeypatch):
    """A broken YAML file is logged and skipped; valid siblings still load."""
    from app.services import plugin_skill_loader

    # Stand up a fake plugin layout under tmp_path
    plugins_root = tmp_path / "plugins"
    skills_dir = plugins_root / "demo" / "skills"
    skills_dir.mkdir(parents=True)
    # A valid skill
    (skills_dir / "good.yaml").write_text(
        yaml.safe_dump(
            {
                "slug": "good",
                "name": "Good Skill",
                "version": "0.1.0",
                "description": "ok",
                "plugin": "demo",
                "security": {
                    "wrap_external_data": True,
                    "pii_guard": True,
                    "sandbox": "none",
                },
            }
        ),
        encoding="utf-8",
    )
    # Broken YAML
    (skills_dir / "broken.yaml").write_text("key: [unclosed", encoding="utf-8")

    monkeypatch.setattr(plugin_skill_loader, "_PLUGINS_ROOT", plugins_root)
    skills = load_plugin_skills("demo")
    assert [s["slug"] for s in skills] == ["good"]
