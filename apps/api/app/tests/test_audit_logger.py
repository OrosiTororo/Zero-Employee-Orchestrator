"""Audit Logger tests."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.logger import (
    record_audit_event,
    record_dangerous_operation,
    record_state_change,
)


@pytest.mark.asyncio
async def test_record_audit_event(db_session: AsyncSession):
    """監査イベントが正しく記録されること."""
    company_id = str(uuid.uuid4())
    log = await record_audit_event(
        db=db_session,
        company_id=company_id,
        event_type="test.event",
        target_type="test",
        details={"key": "value"},
    )
    assert log.id is not None
    assert log.event_type == "test.event"
    assert log.target_type == "test"
    assert log.actor_type == "system"
    assert log.details_json == {"key": "value"}


@pytest.mark.asyncio
async def test_record_audit_event_with_actor(db_session: AsyncSession):
    """アクター情報が正しく記録されること."""
    company_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    log = await record_audit_event(
        db=db_session,
        company_id=company_id,
        event_type="user.action",
        target_type="ticket",
        actor_type="user",
        actor_user_id=user_id,
    )
    assert log.actor_type == "user"
    assert str(log.actor_user_id) == user_id


@pytest.mark.asyncio
async def test_record_state_change(db_session: AsyncSession):
    """状態遷移が正しく記録されること."""
    company_id = str(uuid.uuid4())
    target_id = str(uuid.uuid4())
    log = await record_state_change(
        db=db_session,
        company_id=company_id,
        target_type="task",
        target_id=target_id,
        old_status="pending",
        new_status="running",
    )
    assert log.event_type == "task.status_changed"
    assert log.details_json["old_status"] == "pending"
    assert log.details_json["new_status"] == "running"


@pytest.mark.asyncio
async def test_record_dangerous_operation(db_session: AsyncSession):
    """危険操作が正しく記録されること."""
    company_id = str(uuid.uuid4())
    target_id = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())
    log = await record_dangerous_operation(
        db=db_session,
        company_id=company_id,
        operation_type="external_send",
        target_type="task",
        target_id=target_id,
        actor_agent_id=agent_id,
    )
    assert log.event_type == "dangerous_operation.external_send"
    assert log.details_json["operation_type"] == "external_send"


@pytest.mark.asyncio
async def test_record_audit_event_no_auto_commit(db_session: AsyncSession):
    """auto_commit=False でコミットされないこと."""
    company_id = str(uuid.uuid4())
    log = await record_audit_event(
        db=db_session,
        company_id=company_id,
        event_type="test.no_commit",
        target_type="test",
        auto_commit=False,
    )
    assert log.event_type == "test.no_commit"


@pytest.mark.asyncio
async def test_record_accepts_uuid_objects(db_session: AsyncSession):
    """UUID オブジェクトも文字列も受け付けること."""
    company_id = uuid.uuid4()
    target_id = uuid.uuid4()
    log = await record_audit_event(
        db=db_session,
        company_id=company_id,
        event_type="test.uuid",
        target_type="test",
        target_id=target_id,
    )
    assert log.company_id == company_id
    assert log.target_id == target_id
