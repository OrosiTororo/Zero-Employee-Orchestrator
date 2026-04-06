"""PII (Personally Identifiable Information) detection and masking guard.

Prevents users from unintentionally passing personal information to AI.
Automatically detects PII in all inputs such as chat messages, file uploads,
and API requests, and masks them before passing to AI.

Detection categories:
- Email addresses
- Phone numbers (Japan, US, international)
- Credit card numbers (with Luhn validation)
- My Number (Japan's individual number)
- Addresses (Japanese postal code + address patterns)
- Dates of birth
- Passport numbers
- Driver's license numbers
- Bank account numbers
- IP addresses (with octet range validation)
- Passwords / secrets
- Social Security Numbers (US)
- Driver's license numbers (Japan, US)
- Japanese full names (with keyword context)

Default: All detection enabled (security first)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class PIICategory(str, Enum):
    """PII category."""

    EMAIL = "email"
    PHONE = "phone"
    CREDIT_CARD = "credit_card"
    MY_NUMBER = "my_number"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    BANK_ACCOUNT = "bank_account"
    IP_ADDRESS = "ip_address"
    PASSWORD = "password"
    SSN = "ssn"
    NAME_JP = "name_jp"


@dataclass
class PIIDetectionResult:
    """PII detection result."""

    original_text: str
    masked_text: str
    detected_count: int = 0
    detected_types: list[str] = field(default_factory=list)
    detections: list[dict] = field(default_factory=list)

    @property
    def has_pii(self) -> bool:
        """Whether PII was detected."""
        return self.detected_count > 0


def _luhn_check(number_str: str) -> bool:
    """Validate a credit card number using the Luhn algorithm."""
    digits = [int(d) for d in number_str if d.isdigit()]
    if len(digits) != 16:
        return False
    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _is_valid_ipv4(ip_str: str) -> bool:
    """Validate that all octets are in the 0-255 range."""
    parts = ip_str.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


# PII pattern definitions
_PII_PATTERNS: list[tuple[PIICategory, re.Pattern, str]] = [
    # Email address
    (
        PIICategory.EMAIL,
        re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
        "[EMAIL]",
    ),
    # Credit card number (4-digit x 4 groups) -- evaluated before phone numbers
    (
        PIICategory.CREDIT_CARD,
        re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
        "[CREDIT_CARD]",
    ),
    # Phone number (Japan)
    (
        PIICategory.PHONE,
        re.compile(r"(?:0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4})"),
        "[PHONE]",
    ),
    # Phone number (international / US)
    (
        PIICategory.PHONE,
        re.compile(r"(?:\+\d{1,3}[-\s]?)?\(?\d{2,4}\)?[-\s]?\d{3,4}[-\s]?\d{3,4}"),
        "[PHONE]",
    ),
    # My Number (12 digits) — require keyword context to reduce false positives
    (
        PIICategory.MY_NUMBER,
        re.compile(
            r"(?:マイナンバー|個人番号|my\s*number)\s*[:：]?\s*(\d{4}[-\s]?\d{4}[-\s]?\d{4})\b",
            re.IGNORECASE,
        ),
        "[MY_NUMBER]",
    ),
    # Japanese postal code + address
    (
        PIICategory.ADDRESS,
        re.compile(r"〒?\d{3}[-ー]\d{4}"),
        "[ADDRESS]",
    ),
    # Date of birth pattern (YYYY/MM/DD, YYYY-MM-DD, YYYY年MM月DD日)
    (
        PIICategory.DATE_OF_BIRTH,
        re.compile(
            r"(?:19|20)\d{2}[/\-年]\s*(?:0?[1-9]|1[0-2])[/\-月]\s*(?:0?[1-9]|[12]\d|3[01])日?"
        ),
        "[DOB]",
    ),
    # Passport number (Japan: 2 letters + 7 digits)
    (
        PIICategory.PASSPORT,
        re.compile(r"\b[A-Z]{2}\d{7}\b"),
        "[PASSPORT]",
    ),
    # SSN (US: 3-2-4 digits) — keyword context required to reduce false positives
    (
        PIICategory.SSN,
        re.compile(
            r"(?:ssn|social\s*security(?:\s*number)?|社会保障番号)\s*[:=]?\s*"
            r"(\d{3}[-\s]?\d{2}[-\s]?\d{4})\b",
            re.IGNORECASE,
        ),
        "[SSN]",
    ),
    # IP address (v4) — validated post-match by _is_valid_ipv4
    (
        PIICategory.IP_ADDRESS,
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "[IP]",
    ),
    # Password / secret (key=value format)
    (
        PIICategory.PASSWORD,
        re.compile(
            r"(?i)(?:password|passwd|secret|token|api[_\-]?key|credential)\s*[=:]\s*"
            r'["\']?([^\s"\'}{,]{4,})["\']?'
        ),
        "[REDACTED_SECRET]",
    ),
    # Bank account (7+ digit number preceded by account number keywords)
    (
        PIICategory.BANK_ACCOUNT,
        re.compile(r"(?:口座番号|account)\s*[:：]?\s*\d{7,}", re.IGNORECASE),
        "[BANK_ACCOUNT]",
    ),
    # Driver's license number (Japan: 12 digits; US: state-dependent alphanumeric)
    (
        PIICategory.DRIVERS_LICENSE,
        re.compile(
            r"(?:運転免許|免許証|driver'?s?\s*licen[cs]e)\s*[:：]?\s*"
            r"(?:\d{12}|[A-Z]\d{7,14})",
            re.IGNORECASE,
        ),
        "[DRIVERS_LICENSE]",
    ),
    # Japanese full name (family + given name in kanji/katakana)
    (
        PIICategory.NAME_JP,
        re.compile(
            r"(?:氏名|名前|フルネーム)\s*[:：]?\s*"
            r"[\u4e00-\u9fff\u30a0-\u30ff]{1,6}\s*[\u4e00-\u9fff\u30a0-\u30ff]{1,6}"
        ),
        "[NAME]",
    ),
]


def detect_and_mask_pii(
    text: str,
    enabled_categories: set[PIICategory] | None = None,
) -> PIIDetectionResult:
    """Detect and mask PII in text.

    Args:
        text: Text to inspect
        enabled_categories: Categories to enable for detection (None = all enabled)

    Returns:
        PIIDetectionResult: Detection results and masked text
    """
    masked = text
    detected_count = 0
    detected_types: list[str] = []
    detections: list[dict] = []

    for category, pattern, mask in _PII_PATTERNS:
        if enabled_categories and category not in enabled_categories:
            continue

        matches = list(pattern.finditer(masked))
        # Post-match validation for patterns that need extra checks
        if category == PIICategory.CREDIT_CARD:
            matches = [m for m in matches if _luhn_check(m.group())]
        elif category == PIICategory.IP_ADDRESS:
            matches = [m for m in matches if _is_valid_ipv4(m.group())]
        if matches:
            for match in reversed(matches):  # Replace from end to avoid position shift
                matched_text = match.group()
                # For password patterns, keep the keyword part
                if category == PIICategory.PASSWORD:
                    # Mask only the value part of key=value
                    full = match.group()
                    try:
                        val = match.group(1)
                        replacement = full.replace(val, mask)
                    except IndexError:
                        replacement = mask
                else:
                    replacement = mask

                masked = masked[: match.start()] + replacement + masked[match.end() :]

                detected_count += 1
                detections.append(
                    {
                        "category": category.value,
                        "position": match.start(),
                        "length": len(matched_text),
                    }
                )

            if category.value not in detected_types:
                detected_types.append(category.value)

    return PIIDetectionResult(
        original_text=text,
        masked_text=masked,
        detected_count=detected_count,
        detected_types=detected_types,
        detections=detections,
    )


def check_text_for_pii(text: str) -> bool:
    """Check whether text contains PII (without masking)."""
    result = detect_and_mask_pii(text)
    return result.detected_count > 0


def get_pii_categories() -> list[dict]:
    """Return a list of available PII categories."""
    return [{"id": c.value, "name": c.value.replace("_", " ").title()} for c in PIICategory]
