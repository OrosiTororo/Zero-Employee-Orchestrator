"""Direct tests for pii_guard (PII detection and masking)."""

from __future__ import annotations

from app.security.pii_guard import (
    PIICategory,
    check_text_for_pii,
    detect_and_mask_pii,
    get_pii_categories,
)


class TestDetectAndMask:
    def test_email_is_detected_and_masked(self):
        result = detect_and_mask_pii("Contact: alice@example.com for details.")
        assert result.detected_count >= 1
        assert "email" in result.detected_types
        assert "alice@example.com" not in result.masked_text

    def test_clean_text_returns_zero_detections(self):
        result = detect_and_mask_pii("This is a perfectly ordinary sentence.")
        assert result.detected_count == 0
        assert result.has_pii is False
        assert result.masked_text == result.original_text

    def test_credit_card_requires_luhn_validity(self):
        # Invalid checksum — must NOT be flagged.
        invalid = detect_and_mask_pii("card 1234 5678 9012 3456")
        assert "credit_card" not in invalid.detected_types
        # Valid Luhn test number.
        valid = detect_and_mask_pii("card 4532 0151 1283 0366")
        assert "credit_card" in valid.detected_types

    def test_password_value_is_masked_but_keyword_preserved(self):
        result = detect_and_mask_pii("password=hunter2secure")
        assert "hunter2secure" not in result.masked_text
        assert "password" in result.masked_text.lower()

    def test_category_filter_limits_detection(self):
        text = "Email me at bob@example.com or call 555-123-4567."
        only_email = detect_and_mask_pii(text, enabled_categories={PIICategory.EMAIL})
        assert "email" in only_email.detected_types
        # Phone detection is disabled, so it stays in the masked text.
        assert "phone" not in only_email.detected_types

    def test_multiple_emails_all_masked(self):
        text = "Write to a@x.com and b@y.com"
        result = detect_and_mask_pii(text)
        assert result.detected_count >= 2
        assert "a@x.com" not in result.masked_text
        assert "b@y.com" not in result.masked_text


class TestCheckTextForPii:
    def test_positive_case(self):
        assert check_text_for_pii("reach me at alice@example.com") is True

    def test_negative_case(self):
        assert check_text_for_pii("the sky is blue today") is False


class TestGetPiiCategories:
    def test_returns_nonempty_list(self):
        categories = get_pii_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0
        # Every entry should carry at least a category identifier.
        for entry in categories:
            assert isinstance(entry, dict)
