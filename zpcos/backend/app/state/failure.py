"""Failure Taxonomy — 失敗分類と復旧策。"""

from enum import Enum
from pydantic import BaseModel


class FailureType(str, Enum):
    AUTH_ERROR = "auth_error"
    RATE_LIMIT = "rate_limit"
    SPEC_CHANGE = "spec_change"
    INPUT_MISSING = "input_missing"
    EVIDENCE_WEAK = "evidence_weak"
    CONTRADICTION = "contradiction"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class FailureRecord(BaseModel):
    failure_type: FailureType
    original_error: str = ""
    message: str = ""
    recoverable: bool = False
    suggested_action: str = ""


class RecoveryStrategy(BaseModel):
    strategy: str  # retry | skip | escalate | modify_input
    description: str
    auto_applicable: bool


async def classify_failure(error: Exception | str) -> FailureRecord:
    """エラーを分類。"""
    msg = str(error)
    if "401" in msg or "auth" in msg.lower():
        return FailureRecord(
            failure_type=FailureType.AUTH_ERROR, message=msg, original_error=msg,
            recoverable=True, suggested_action="再認証してください",
        )
    if "429" in msg or "rate" in msg.lower():
        return FailureRecord(
            failure_type=FailureType.RATE_LIMIT, message=msg, original_error=msg,
            recoverable=True, suggested_action="30秒待って再試行",
        )
    if "timeout" in msg.lower():
        return FailureRecord(
            failure_type=FailureType.TIMEOUT, message=msg, original_error=msg,
            recoverable=True, suggested_action="再試行またはタイムアウト延長",
        )
    return FailureRecord(
        failure_type=FailureType.UNKNOWN, message=msg, original_error=msg,
        recoverable=False, suggested_action="エラー詳細を確認してください",
    )


async def suggest_recovery(failure: FailureRecord) -> RecoveryStrategy:
    """復旧策を提案。"""
    if failure.failure_type == FailureType.RATE_LIMIT:
        return RecoveryStrategy(
            strategy="retry", description="30秒後に自動再試行", auto_applicable=True,
        )
    if failure.failure_type == FailureType.AUTH_ERROR:
        return RecoveryStrategy(
            strategy="escalate", description="再認証が必要です", auto_applicable=False,
        )
    return RecoveryStrategy(
        strategy="escalate", description="手動確認が必要です", auto_applicable=False,
    )
