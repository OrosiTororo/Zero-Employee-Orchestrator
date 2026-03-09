"""情報サニタイズ — 保存・共有時の機密情報除去.

Zero-Employee Orchestrator.md §8.4 に基づき、保存・共有・公開の各段階で
情報をそのまま扱わず、サニタイズ処理を行う。

処理方針:
- API キー、OAuth トークン、シークレット値はマスキングまたは参照 ID 化
- 個人名、住所、決済情報などの個人情報は共有時に除去または匿名化
- 社外秘資料、未公開情報、契約情報は公開対象から除外
- 会話ログや改善ログを学習や共有に使う場合はユーザーが範囲を制御可能
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SanitizeResult:
    """サニタイズ処理の結果."""

    sanitized_text: str
    redacted_count: int
    redacted_types: list[str]


# シークレット値のパターン
_SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("api_key", re.compile(r"(sk-[a-zA-Z0-9]{20,})")),
    ("api_key", re.compile(r"(sk-or-v1-[a-zA-Z0-9]{20,})")),
    ("bearer_token", re.compile(r"(Bearer\s+[a-zA-Z0-9._\-]{20,})")),
    ("oauth_token", re.compile(r"(ya29\.[a-zA-Z0-9._\-]{20,})")),
    ("password", re.compile(r'(?i)(password|passwd|secret)\s*[=:]\s*["\']?([^"\'}\s]+)')),
    ("email", re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
]


def sanitize_text(text: str) -> SanitizeResult:
    """テキストからシークレット値・個人情報をマスキングする."""
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
    """辞書からセンシティブなキーの値をマスキングする."""
    default_sensitive = {
        "password", "secret", "token", "api_key", "apikey",
        "authorization", "credential", "private_key",
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
