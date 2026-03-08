"""State Machine tests — TicketStateMachine, TaskStateMachine, ApprovalStateMachine."""

import pytest

from app.orchestration.state_machine import (
    AgentStateMachine,
    ApprovalStateMachine,
    BaseStateMachine,
    StateMachineError,
    TaskStateMachine,
    TicketStateMachine,
)


class TestBaseStateMachine:
    def test_invalid_initial_state_raises(self):
        with pytest.raises(StateMachineError, match="不明な初期状態"):
            TaskStateMachine("nonexistent")

    def test_state_property(self):
        sm = TaskStateMachine("pending")
        assert sm.state == "pending"

    def test_history_starts_empty(self):
        sm = TaskStateMachine("pending")
        assert sm.history == []


class TestTicketStateMachine:
    def test_valid_transitions(self):
        sm = TicketStateMachine("draft")
        sm.transition("open")
        assert sm.state == "open"
        sm.transition("planning")
        assert sm.state == "planning"
        sm.transition("ready")
        assert sm.state == "ready"

    def test_invalid_transition_raises(self):
        sm = TicketStateMachine("draft")
        with pytest.raises(StateMachineError, match="遷移不可"):
            sm.transition("done")

    def test_cancelled_is_terminal(self):
        sm = TicketStateMachine("draft")
        sm.transition("cancelled")
        assert sm.available_transitions() == []

    def test_can_transition_check(self):
        sm = TicketStateMachine("draft")
        assert sm.can_transition("open") is True
        assert sm.can_transition("done") is False

    def test_history_is_recorded(self):
        sm = TicketStateMachine("draft")
        sm.transition("open", reason="テスト")
        assert len(sm.history) == 1
        assert sm.history[0]["from"] == "draft"
        assert sm.history[0]["to"] == "open"
        assert sm.history[0]["reason"] == "テスト"

    def test_full_lifecycle(self):
        sm = TicketStateMachine("draft")
        sm.transition("open")
        sm.transition("interviewing")
        sm.transition("planning")
        sm.transition("ready")
        sm.transition("in_progress")
        sm.transition("review")
        sm.transition("done")
        sm.transition("closed")
        assert sm.state == "closed"
        assert len(sm.history) == 8


class TestTaskStateMachine:
    def test_pending_to_ready(self):
        sm = TaskStateMachine("pending")
        sm.transition("ready")
        assert sm.state == "ready"

    def test_running_to_succeeded(self):
        sm = TaskStateMachine("running")
        sm.transition("succeeded")
        assert sm.state == "succeeded"

    def test_running_to_awaiting_approval(self):
        sm = TaskStateMachine("running")
        sm.transition("awaiting_approval")
        assert sm.state == "awaiting_approval"

    def test_failed_retry_cycle(self):
        sm = TaskStateMachine("running")
        sm.transition("failed")
        sm.transition("retrying")
        sm.transition("running")
        sm.transition("succeeded")
        assert sm.state == "succeeded"

    def test_archived_is_terminal(self):
        sm = TaskStateMachine("archived")
        assert sm.available_transitions() == []

    def test_rework_requested(self):
        sm = TaskStateMachine("verified")
        sm.transition("rework_requested")
        sm.transition("ready")
        assert sm.state == "ready"


class TestApprovalStateMachine:
    def test_requested_to_approved(self):
        sm = ApprovalStateMachine("requested")
        sm.transition("approved")
        assert sm.state == "approved"

    def test_approved_to_executed(self):
        sm = ApprovalStateMachine("approved")
        sm.transition("executed")
        assert sm.state == "executed"

    def test_rejected_to_superseded(self):
        sm = ApprovalStateMachine("rejected")
        sm.transition("superseded")
        assert sm.state == "superseded"

    def test_expired_can_retry(self):
        sm = ApprovalStateMachine("expired")
        sm.transition("requested")
        assert sm.state == "requested"

    def test_executed_is_terminal(self):
        sm = ApprovalStateMachine("executed")
        assert sm.available_transitions() == []


class TestAgentStateMachine:
    def test_provisioning_to_idle(self):
        sm = AgentStateMachine("provisioning")
        sm.transition("idle")
        assert sm.state == "idle"

    def test_idle_to_busy_and_back(self):
        sm = AgentStateMachine("idle")
        sm.transition("busy")
        sm.transition("idle")
        assert sm.state == "idle"

    def test_decommissioned_is_terminal(self):
        sm = AgentStateMachine("decommissioned")
        assert sm.available_transitions() == []

    def test_error_recovery(self):
        sm = AgentStateMachine("busy")
        sm.transition("error")
        sm.transition("idle")
        assert sm.state == "idle"
