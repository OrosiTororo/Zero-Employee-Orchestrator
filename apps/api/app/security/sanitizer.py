"""Information sanitization -- Remove sensitive data during storage and sharing.

Based on Zero-Employee Orchestrator.md section 8.4, sanitization is performed
at each stage of storage, sharing, and publication rather than handling data as-is.

Processing policy:
- API keys, OAuth tokens, and secret values are masked or replaced with reference IDs
- Personal information such as names, addresses, and payment details are removed or anonymized during sharing
- Confidential documents, unpublished information, and contract data are excluded from publication
- When using conversation logs or improvement logs for learning or sharing, users control the scope
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SanitizeResult:
    """Sanitization result."""

    sanitized_text: str
    redacted_count: int
    redacted_types: list[str]


# Secret value patterns
_SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("api_key", re.compile(r"(sk-[a-zA-Z0-9]{20,})")),
    ("api_key", re.compile(r"(sk-or-v1-[a-zA-Z0-9]{20,})")),
    ("bearer_token", re.compile(r"(Bearer\s+[a-zA-Z0-9._\-]{20,})")),
    ("oauth_token", re.compile(r"(ya29\.[a-zA-Z0-9._\-]{20,})")),
    (
        "password",
        re.compile(r'(?i)(password|passwd|secret)\s*[=:]\s*["\']?([^"\'}\s]+)'),
    ),
    ("email", re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
]


def sanitize_text(text: str) -> SanitizeResult:
    """Mask secret values and personal information from text."""
    sanitized = text
    redacted_count = 0
    redacted_types: list[str] = []

    for secret_type, pattern in _SECRET_PATTERNS:
        matches = pattern.findall(sanitized)
        if matches:
            redacted_count += len(matches)
            if secret_type not in redacted_types:
                redacted_types.append(secret_type)
            for match in matches:
                match_str = match if isinstance(match, str) else match[0]
                sanitized = sanitized.replace(match_str, f"[REDACTED:{secret_type}]")

    return SanitizeResult(
        sanitized_text=sanitized,
        redacted_count=redacted_count,
        redacted_types=redacted_types,
    )


def sanitize_dict(data: dict, sensitive_keys: set[str] | None = None) -> dict:
    """Mask values of sensitive keys in a dictionary."""
    default_sensitive = {
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "authorization",
        "credential",
        "private_key",
    }
    keys_to_mask = sensitive_keys or default_sensitive
    result = {}

    for key, value in data.items():
        key_lower = key.lower()
        if any(s in key_lower for s in keys_to_mask):
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value, keys_to_mask)
        elif isinstance(value, str):
            sr = sanitize_text(value)
            result[key] = sr.sanitized_text
        else:
            result[key] = value

    return result
