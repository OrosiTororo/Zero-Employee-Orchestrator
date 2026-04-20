"""Tests for approval_service."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import approval_service


class TestRequiresForcedApproval:
    def test_external_send_requires_approval(self):
        assert approval_service.requires_forced_approval("external_send") is True

    def test_delete_requires_approval(self):
        assert approval_service.requires_forced_approval("delete") is True

    def test_git_push_requires_approval(self):
        assert approval_service.requires_forced_approval("git_push") is True

    def test_benign_operation_does_not_require_approval(self):
        assert approval_service.requires_forced_approval("read_profile") is False


class TestApprovalTransitions:
    def test_requested_can_become_approved(self):
        assert "approved" in approval_service.APPROVAL_TRANSITIONS["requested"]

    def test_approved_can_become_executed(self):
        assert approval_service.APPROVAL_TRANSITIONS["approved"] == ["executed"]

    def test_terminal_states_have_no_transitions(self):
        assert approval_service.APPROVAL_TRANSITIONS["cancelled"] == []
        assert approval_service.APPROVAL_TRANSITIONS["executed"] == []
        assert approval_service.APPROVAL_TRANSITIONS["superseded"] == []


@pytest.mark.asyncio
async def test_create_approval_request_persists_payload(db_session: AsyncSession):
    company_id = str(uuid.uuid4())
    target_id = str(uuid.uuid4())
    req = await approval_service.create_approval_request(
        db=db_session,
        company_id=company_id,
        target_type="task",
        target_id=target_id,
        reason="testing",
        risk_level="high",
        payload_json={"amount": 42},
    )
    assert req.status == "requested"
    assert str(req.company_id) == company_id
    assert req.reason == "testing"
    assert req.risk_level == "high"
    assert req.payload_json == {"amount": 42}


@pytest.mark.asyncio
async def test_decide_approval_flips_status(db_session: AsyncSession):
    company_id = str(uuid.uuid4())
    target_id = str(uuid.uuid4())
    approver_id = str(uuid.uuid4())
    req = await approval_service.create_approval_request(
        db=db_session,
        company_id=company_id,
        target_type="task",
        target_id=target_id,
        reason="testing",
    )
    decided = await approval_service.decide_approval(
        db=db_session,
        approval=req,
        decision="approved",
        approver_user_id=approver_id,
        reason="looks fine",
    )
    assert decided.status == "approved"
    assert str(decided.approver_user_id) == approver_id
    assert decided.decided_at is not None


@pytest.mark.asyncio
async def test_decide_approval_rejects_non_requested(db_session: AsyncSession):
    company_id = str(uuid.uuid4())
    target_id = str(uuid.uuid4())
    approver_id = str(uuid.uuid4())
    req = await approval_service.create_approval_request(
        db=db_session,
        company_id=company_id,
        target_type="task",
        target_id=target_id,
        reason="testing",
    )
    await approval_service.decide_approval(
        db=db_session,
        approval=req,
        decision="approved",
        approver_user_id=approver_id,
    )
    # Re-deciding the same approval must fail.
    with pytest.raises(ValueError):
        await approval_service.decide_approval(
            db=db_session,
            approval=req,
            decision="rejected",
            approver_user_id=approver_id,
        )
