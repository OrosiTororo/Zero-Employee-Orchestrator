"""Tests for language switching via config API and i18n sync."""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestLanguageSwitchingViaConfig:
    """Verify that changing LANGUAGE via config_manager syncs with i18n module."""

    def test_set_language_via_config_updates_i18n(self):
        """set_config_value('LANGUAGE', ...) should call i18n.set_language()."""
        from app.core.config_manager import set_config_value
        from app.core.i18n import get_language, set_language

        # Start with Japanese
        set_language("ja")
        assert get_language() == "ja"

        # Change via config manager (mock file I/O)
        with patch("app.core.config_manager._load_config", return_value={}), \
             patch("app.core.config_manager._save_config"):
            set_config_value("LANGUAGE", "en")

        assert get_language() == "en"

        # Change to Chinese
        with patch("app.core.config_manager._load_config", return_value={}), \
             patch("app.core.config_manager._save_config"):
            set_config_value("LANGUAGE", "zh")

        assert get_language() == "zh"

        # Restore
        set_language("ja")

    def test_set_invalid_language_rejected(self):
        """Invalid language values should raise ValueError."""
        from app.core.config_manager import set_config_value

        with pytest.raises(ValueError, match="Invalid language"):
            with patch("app.core.config_manager._load_config", return_value={}), \
                 patch("app.core.config_manager._save_config"):
                set_config_value("LANGUAGE", "fr")

    def test_translation_changes_after_language_switch(self):
        """t() output should reflect language change made via config manager."""
        from app.core.config_manager import set_config_value
        from app.core.i18n import set_language, t

        set_language("ja")
        ja_text = t("chat_welcome")

        with patch("app.core.config_manager._load_config", return_value={}), \
             patch("app.core.config_manager._save_config"):
            set_config_value("LANGUAGE", "en")

        en_text = t("chat_welcome")
        assert ja_text != en_text
        assert "natural language" in en_text.lower()

        # Restore
        set_language("ja")

    def test_apply_runtime_config_syncs_language(self):
        """apply_runtime_config() should set i18n language from config file."""
        from app.core.config_manager import apply_runtime_config
        from app.core.i18n import get_language, set_language

        set_language("ja")

        with patch("app.core.config_manager._load_config", return_value={"LANGUAGE": "en"}), \
             patch("os.environ.get", return_value=None):
            apply_runtime_config()

        assert get_language() == "en"

        # Restore
        set_language("ja")


class TestI18nAllLanguages:
    """Verify all three languages have consistent translation keys."""

    def test_all_keys_have_three_languages(self):
        """Every translation key should have ja, en, and zh entries."""
        from app.core.i18n import _TRANSLATIONS

        for key, translations in _TRANSLATIONS.items():
            for lang in ("ja", "en", "zh"):
                assert lang in translations, f"Key '{key}' missing '{lang}' translation"

    def test_language_switching_cycle(self):
        """Switching through all languages should work correctly."""
        from app.core.i18n import get_language, set_language, t

        for lang in ("ja", "en", "zh"):
            set_language(lang)
            assert get_language() == lang
            # Every key should return a non-empty string
            result = t("chat_welcome")
            assert len(result) > 0

        # Restore
        set_language("ja")
