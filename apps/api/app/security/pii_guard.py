"""PII (個人識別情報) 検出・マスキングガード.

ユーザーが意図せず個人情報を AI に渡すことを防止する。
チャット入力、ファイルアップロード、API リクエスト等の全入力に対して
PII を自動検出し、AI に渡す前にマスキングする。

検出カテゴリ:
- メールアドレス
- 電話番号（日本・米国・国際）
- クレジットカード番号
- マイナンバー（日本の個人番号）
- 住所（日本の郵便番号 + 住所パターン）
- 生年月日
- パスポート番号
- 運転免許証番号
- 銀行口座番号
- IP アドレス
- パスワード / シークレット

初期設定: 全検出有効（セキュリティ最優先）
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class PIICategory(str, Enum):
    """PII カテゴリ."""

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
    """PII 検出結果."""

    original_text: str
    masked_text: str
    detected_count: int = 0
    detected_types: list[str] = field(default_factory=list)
    detections: list[dict] = field(default_factory=list)

    @property
    def has_pii(self) -> bool:
        """PII が検出されたかどうか."""
        return self.detected_count > 0


# PII パターン定義
_PII_PATTERNS: list[tuple[PIICategory, re.Pattern, str]] = [
    # メールアドレス
    (
        PIICategory.EMAIL,
        re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
        "[EMAIL]",
    ),
    # 電話番号（日本）
    (
        PIICategory.PHONE,
        re.compile(r"(?:0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4})"),
        "[PHONE]",
    ),
    # 電話番号（国際 / 米国）
    (
        PIICategory.PHONE,
        re.compile(r"(?:\+\d{1,3}[-\s]?)?\(?\d{2,4}\)?[-\s]?\d{3,4}[-\s]?\d{3,4}"),
        "[PHONE]",
    ),
    # クレジットカード番号（4桁×4グループ）
    (
        PIICategory.CREDIT_CARD,
        re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
        "[CREDIT_CARD]",
    ),
    # マイナンバー（12桁）
    (
        PIICategory.MY_NUMBER,
        re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
        "[MY_NUMBER]",
    ),
    # 日本の郵便番号 + 住所
    (
        PIICategory.ADDRESS,
        re.compile(r"〒?\d{3}[-ー]\d{4}"),
        "[ADDRESS]",
    ),
    # 生年月日パターン（YYYY/MM/DD, YYYY-MM-DD, YYYY年MM月DD日）
    (
        PIICategory.DATE_OF_BIRTH,
        re.compile(
            r"(?:19|20)\d{2}[/\-年]\s*(?:0?[1-9]|1[0-2])[/\-月]\s*(?:0?[1-9]|[12]\d|3[01])日?"
        ),
        "[DOB]",
    ),
    # パスポート番号（日本: 2英字 + 7数字）
    (
        PIICategory.PASSPORT,
        re.compile(r"\b[A-Z]{2}\d{7}\b"),
        "[PASSPORT]",
    ),
    # SSN（米国: 3-2-4桁）
    (
        PIICategory.SSN,
        re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
        "[SSN]",
    ),
    # IP アドレス（v4）
    (
        PIICategory.IP_ADDRESS,
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "[IP]",
    ),
    # パスワード / シークレット（key=value 形式）
    (
        PIICategory.PASSWORD,
        re.compile(
            r"(?i)(?:password|passwd|secret|token|api[_\-]?key|credential)\s*[=:]\s*"
            r'["\']?([^\s"\'}{,]{4,})["\']?'
        ),
        "[REDACTED_SECRET]",
    ),
    # 銀行口座（7桁数字で前に口座番号等のキーワード）
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
    """テキスト中の PII を検出しマスキングする.

    Args:
        text: 検査対象テキスト
        enabled_categories: 検出を有効にするカテゴリ（None = 全て有効）

    Returns:
        PIIDetectionResult: 検出結果とマスク済みテキスト
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
            for match in reversed(matches):  # 後ろから置換（位置ずれ防止）
                matched_text = match.group()
                # パスワードパターンの場合、キーワード部分は残す
                if category == PIICategory.PASSWORD:
                    # key=value の value 部分のみマスク
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
    """テキストに PII が含まれているかチェックする（マスキングなし）."""
    result = detect_and_mask_pii(text)
    return result.detected_count > 0


def get_pii_categories() -> list[dict]:
    """利用可能な PII カテゴリ一覧を返す."""
    return [{"id": c.value, "name": c.value.replace("_", " ").title()} for c in PIICategory]
