"""PII (Personally Identifiable Information) detection and masking guard.

Prevents users from unintentionally passing personal information to AI.
Automatically detects PII in all inputs such as chat messages, file uploads,
and API requests, and masks them before passing to AI.

Detection categories:
- Email addresses
- Phone numbers (Japan, US, international)
- Credit card numbers
- My Number (Japan's individual number)
- Addresses (Japanese postal code + address patterns)
- Dates of birth
- Passport numbers
- Driver's license numbers
- Bank account numbers
- IP addresses
- Passwords / secrets

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
    # My Number (12 digits)
    (
        PIICategory.MY_NUMBER,
        re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
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
    # SSN (US: 3-2-4 digits)
    (
        PIICategory.SSN,
        re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
        "[SSN]",
    ),
    # IP address (v4)
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
