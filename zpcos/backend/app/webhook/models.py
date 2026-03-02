"""Webhook データモデル"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class WebhookEvent(str, Enum):
    """送信可能なイベント種別"""
    ORCHESTRATION_STARTED = "orchestration.started"
    ORCHESTRATION_COMPLETED = "orchestration.completed"
    ORCHESTRATION_FAILED = "orchestration.failed"
    SKILL_GENERATED = "skill.generated"
    SKILL_EXECUTED = "skill.executed"
    HEAL_ATTEMPT = "heal.attempt"
    JUDGE_COMPLETED = "judge.completed"
    INTERVIEW_COMPLETED = "interview.completed"
    TASK_TRANSITION = "task.transition"


class WebhookConfig(BaseModel):
    """Webhook 登録設定"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    url: str
    secret: str = Field(default_factory=lambda: uuid.uuid4().hex)
    events: list[WebhookEvent] = Field(default_factory=lambda: list(WebhookEvent))
    active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_triggered: str | None = None
    failure_count: int = 0
    max_retries: int = 3


class WebhookDelivery(BaseModel):
    """配信ログ"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    webhook_id: str
    event: WebhookEvent
    payload: dict
    status_code: int | None = None
    response_body: str | None = None
    success: bool = False
    attempt: int = 1
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WebhookPayload(BaseModel):
    """n8n互換ペイロード"""
    event: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "zpcos"
    data: dict = Field(default_factory=dict)
