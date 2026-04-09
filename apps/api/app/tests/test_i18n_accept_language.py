"""Tests for t_from_accept_language() and _parse_accept_language() helpers.

Verifies that:
- Accept-Language header is correctly parsed (BCP 47, q-values, normalisation)
- t_from_accept_language() translates HTTP error keys in the caller's language
- The global _current_lang is restored after the call (thread safety)
"""

from __future__ import annotations

import pytest


class TestParseAcceptLanguage:
    """Unit tests for _parse_accept_language()."""

    def test_simple_ja(self) -> None:
        from app.core.i18n import _parse_accept_language

        assert _parse_accept_language("ja") == "ja"

    def test_bcp47_zh_cn(self) -> None:
        """zh-CN should normalise to zh."""
        from app.core.i18n import _parse_accept_language

        assert _parse_accept_language("zh-CN,zh;q=0.9") == "zh"

    def test_q_value_priority(self) -> None:
        """Highest q-value wins."""
        from app.core.i18n import _parse_accept_language

        result = _parse_accept_language("en-US;q=0.8,ja,zh;q=0.9")
        assert result == "ja"

    def test_empty_header_defaults_en(self) -> None:
        from app.core.i18n import _parse_accept_language

        assert _parse_accept_language("") == "en"

    def test_unsupported_language_falls_back_en(self) -> None:
        from app.core.i18n import _parse_accept_language

        assert _parse_accept_language("fr,de;q=0.9") == "en"

    def test_ko_recognised(self) -> None:
        from app.core.i18n import _parse_accept_language

        assert _parse_accept_language("ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7") == "ko"

    def test_pt_recognised(self) -> None:
        from app.core.i18n import _parse_accept_language

        assert _parse_accept_language("pt-BR,pt;q=0.9,en;q=0.8") == "pt"

    def test_tr_recognised(self) -> None:
        from app.core.i18n import _parse_accept_language

        assert _parse_accept_language("tr-TR,tr;q=0.9") == "tr"


class TestTFromAcceptLanguage:
    """Tests for t_from_accept_language() — translation via Accept-Language."""

    def test_ja_404(self) -> None:
        from app.core.i18n import t_from_accept_language

        result = t_from_accept_language("http_404_not_found", "ja")
        assert result != "http_404_not_found"  # key resolved
        assert "見つかりません" in result or len(result) > 5

    def test_en_404(self) -> None:
        from app.core.i18n import t_from_accept_language

        result = t_from_accept_language("http_404_not_found", "en")
        assert "not found" in result.lower()

    def test_zh_401(self) -> None:
        from app.core.i18n import t_from_accept_language

        result = t_from_accept_language("http_401_unauthorized", "zh-CN,zh;q=0.9")
        assert result != "http_401_unauthorized"
        # Chinese text should be returned
        assert any("\u4e00" <= c <= "\u9fff" for c in result)

    def test_format_kwargs(self) -> None:
        """Detail kwarg is formatted into the translated string."""
        from app.core.i18n import t_from_accept_language

        result = t_from_accept_language("http_400_bad_request", "en", detail="missing field X")
        assert "missing field X" in result

    def test_global_lang_restored(self) -> None:
        """The global _current_lang must be unchanged after the call."""
        from app.core.i18n import get_language, set_language, t_from_accept_language

        set_language("en")
        _ = t_from_accept_language("http_404_not_found", "ja")
        assert get_language() == "en"

    def test_unknown_key_returns_key(self) -> None:
        from app.core.i18n import t_from_accept_language

        result = t_from_accept_language("totally_unknown_key_xyz", "ja")
        assert result == "totally_unknown_key_xyz"

    def test_ollama_auto_pull_start_ja(self) -> None:
        from app.core.i18n import t_from_accept_language

        result = t_from_accept_language("ollama_auto_pull_start", "ja", model="qwen3:8b")
        assert "qwen3:8b" in result
        # Japanese characters expected
        assert any("\u3040" <= c <= "\u9fff" for c in result)


class TestHTTPErrorKeys:
    """Verify all HTTP error translation keys are present in all supported languages."""

    HTTP_KEYS = [
        "http_400_bad_request",
        "http_401_unauthorized",
        "http_403_forbidden",
        "http_404_not_found",
        "http_409_conflict",
        "http_422_validation",
        "http_429_rate_limit",
        "http_500_internal",
    ]
    LANGUAGES = ["en", "ja", "zh", "ko", "pt", "tr"]

    @pytest.mark.parametrize("key", HTTP_KEYS)
    @pytest.mark.parametrize("lang", LANGUAGES)
    def test_key_has_translation(self, key: str, lang: str) -> None:
        from app.core.i18n import _TRANSLATIONS, SUPPORTED_LANGUAGES

        assert lang in SUPPORTED_LANGUAGES
        assert key in _TRANSLATIONS, f"Key '{key}' missing from _TRANSLATIONS"
        assert lang in _TRANSLATIONS[key], f"Language '{lang}' missing for key '{key}'"
        assert len(_TRANSLATIONS[key][lang]) > 0, f"Empty translation for {key}/{lang}"
