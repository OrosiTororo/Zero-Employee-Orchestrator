"""Tests for agent_org_service."""

from __future__ import annotations

from app.services.agent_org_service import (
    AgentRolePreset,
    ROLE_DEFINITIONS,
    interpret_natural_language_request,
)


class TestRoleDefinitions:
    def test_secretary_preset_exists(self):
        assert AgentRolePreset.SECRETARY in ROLE_DEFINITIONS

    def test_all_presets_have_required_fields(self):
        required = {"name", "title", "description", "autonomy_level", "system_prompt"}
        for preset, defn in ROLE_DEFINITIONS.items():
            if preset == AgentRolePreset.CUSTOM:
                continue
            missing = required - defn.keys()
            assert not missing, f"{preset.value} missing: {missing}"

    def test_autonomy_levels_are_known(self):
        allowed = {"supervised", "semi-autonomous", "autonomous"}
        for preset, defn in ROLE_DEFINITIONS.items():
            if preset == AgentRolePreset.CUSTOM:
                continue
            assert defn["autonomy_level"] in allowed


class TestNaturalLanguageInterpretation:
    def test_add_secretary_request(self):
        result = interpret_natural_language_request("秘書を追加してください")
        assert result["action"] == "add"
        assert result["target_role"] == "secretary"
        assert result["confidence"] > 0

    def test_remove_engineer_request(self):
        result = interpret_natural_language_request("エンジニアを削除")
        assert result["action"] == "remove"
        assert result["target_role"] == "engineer"

    def test_ambiguous_input_has_zero_confidence(self):
        result = interpret_natural_language_request("こんにちは")
        assert result["confidence"] == 0.0

    def test_english_keywords_work(self):
        result = interpret_natural_language_request("Please add a researcher")
        assert result["action"] == "add"
        assert result["target_role"] == "researcher"

    def test_original_text_is_preserved(self):
        text = "秘書を呼んで"
        result = interpret_natural_language_request(text)
        assert result["original_text"] == text
