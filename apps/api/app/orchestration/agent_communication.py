"""Agent Communication Log — Multi-agent communication recording and visualization.

Records all message exchanges, delegations, and feedback during multi-agent
collaboration, preventing black-box behavior.

Recorded events:
  - Task delegation (delegation)
  - Artifact handoff (artifact_handoff)
  - Feedback / questions (feedback)
  - Approval request / result (approval_exchange)
  - Escalation (escalation)
  - Broadcast (broadcast)

Usage:
  log = comm_log.record(
      msg_type=MessageType.DELEGATION,
      sender_agent_id="agent-A",
      receiver_agent_id="agent-B",
      content="Delegate code generation for task #42",
      context={"task_id": "42", "reason": "Skill shortage"},
  )
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of inter-agent messages."""

    # Task-related
    DELEGATION = "delegation"  # Task delegation
    DELEGATION_ACCEPT = "delegation_accept"  # Delegation accepted
    DELEGATION_REJECT = "delegation_reject"  # Delegation rejected
    TASK_UPDATE = "task_update"  # Task progress report

    # Artifact-related
    ARTIFACT_HANDOFF = "artifact_handoff"  # Artifact handoff
    ARTIFACT_REQUEST = "artifact_request"  # Artifact request

    # Communication
    FEEDBACK = "feedback"  # Feedback / improvement suggestion
    QUESTION = "question"  # Question
    ANSWER = "answer"  # Answer
    INSTRUCTION = "instruction"  # Instruction

    # Quality / Governance
    QUALITY_REVIEW = "quality_review"  # Quality review result
    APPROVAL_REQUEST = "approval_request"  # Approval request
    APPROVAL_RESPONSE = "approval_response"  # Approval result

    # Exception handling
    ESCALATION = "escalation"  # Escalation
    ERROR_REPORT = "error_report"  # Error report
    HELP_REQUEST = "help_request"  # Help request

    # System
    BROADCAST = "broadcast"  # Broadcast notification
    HEARTBEAT_PING = "heartbeat_ping"  # Heartbeat check


class MessagePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class AgentMessage:
    """A single inter-agent message."""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    msg_type: MessageType = MessageType.TASK_UPDATE
    sender_agent_id: str | None = None  # None = system message
    receiver_agent_id: str | None = None  # None = broadcast message
    company_id: str | None = None
    task_id: str | None = None
    ticket_id: str | None = None

    content: str = ""  # Human-readable message body
    structured_data: dict[str, Any] = field(default_factory=dict)

    priority: MessagePriority = MessagePriority.NORMAL
    in_reply_to: str | None = None  # Reply-to message ID
    thread_id: str | None = None  # Thread ID (conversation grouping)

    timestamp: float = field(default_factory=time.time)
    acknowledged: bool = False  # Acknowledged by receiver
    acknowledged_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "msg_type": self.msg_type.value,
            "sender_agent_id": self.sender_agent_id,
            "receiver_agent_id": self.receiver_agent_id,
            "company_id": self.company_id,
            "task_id": self.task_id,
            "ticket_id": self.ticket_id,
            "content": self.content,
            "structured_data": self.structured_data,
            "priority": self.priority.value,
            "in_reply_to": self.in_reply_to,
            "thread_id": self.thread_id,
            "timestamp": self.timestamp,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at,
        }


@dataclass
class ConversationThread:
    """Conversation thread between agents."""

    thread_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str | None = None
    participants: list[str] = field(default_factory=list)  # agent_ids
    subject: str = ""
    messages: list[AgentMessage] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    closed_at: float | None = None

    def add_message(self, msg: AgentMessage) -> None:
        msg.thread_id = self.thread_id
        self.messages.append(msg)
        # Auto-add participants
        for agent_id in (msg.sender_agent_id, msg.receiver_agent_id):
            if agent_id and agent_id not in self.participants:
                self.participants.append(agent_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "task_id": self.task_id,
            "participants": self.participants,
            "subject": self.subject,
            "message_count": len(self.messages),
            "messages": [m.to_dict() for m in self.messages],
            "started_at": self.started_at,
            "closed_at": self.closed_at,
        }


class AgentCommunicationLog:
    """Inter-agent communication recording and search."""

    def __init__(self, max_messages: int = 5000) -> None:
        self._messages: list[AgentMessage] = []
        self._threads: dict[str, ConversationThread] = {}
        self._max_messages = max_messages

    def record(
        self,
        msg_type: MessageType,
        content: str,
        *,
        sender_agent_id: str | None = None,
        receiver_agent_id: str | None = None,
        company_id: str | None = None,
        task_id: str | None = None,
        ticket_id: str | None = None,
        structured_data: dict[str, Any] | None = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        in_reply_to: str | None = None,
        thread_id: str | None = None,
    ) -> AgentMessage:
        """Record a message."""
        msg = AgentMessage(
            msg_type=msg_type,
            sender_agent_id=sender_agent_id,
            receiver_agent_id=receiver_agent_id,
            company_id=company_id,
            task_id=task_id,
            ticket_id=ticket_id,
            content=content,
            structured_data=structured_data or {},
            priority=priority,
            in_reply_to=in_reply_to,
            thread_id=thread_id,
        )

        # Capacity limit
        if len(self._messages) >= self._max_messages:
            self._messages = self._messages[-(self._max_messages // 2) :]

        self._messages.append(msg)

        # Add to thread
        if thread_id and thread_id in self._threads:
            self._threads[thread_id].add_message(msg)

        logger.debug(
            "Agent comm: %s → %s [%s] %s",
            sender_agent_id or "system",
            receiver_agent_id or "broadcast",
            msg_type.value,
            content[:80],
        )
        return msg

    def record_delegation(
        self,
        sender_agent_id: str,
        receiver_agent_id: str,
        task_id: str,
        reason: str,
        **kwargs: Any,
    ) -> AgentMessage:
        """Record a task delegation (shortcut)."""
        return self.record(
            msg_type=MessageType.DELEGATION,
            content=f"Task delegation: {reason}",
            sender_agent_id=sender_agent_id,
            receiver_agent_id=receiver_agent_id,
            task_id=task_id,
            structured_data={"reason": reason, **kwargs},
            priority=MessagePriority.HIGH,
        )

    def record_escalation(
        self,
        sender_agent_id: str,
        reason: str,
        severity: str = "high",
        task_id: str | None = None,
        **kwargs: Any,
    ) -> AgentMessage:
        """Record an escalation (shortcut)."""
        return self.record(
            msg_type=MessageType.ESCALATION,
            content=f"Escalation [{severity}]: {reason}",
            sender_agent_id=sender_agent_id,
            task_id=task_id,
            structured_data={"reason": reason, "severity": severity, **kwargs},
            priority=MessagePriority.URGENT,
        )

    def create_thread(
        self,
        subject: str,
        task_id: str | None = None,
        participants: list[str] | None = None,
    ) -> ConversationThread:
        """Create a new conversation thread."""
        thread = ConversationThread(
            task_id=task_id,
            participants=participants or [],
            subject=subject,
        )
        self._threads[thread.thread_id] = thread
        return thread

    def acknowledge(self, message_id: str) -> bool:
        """Acknowledge message receipt."""
        for msg in reversed(self._messages):
            if msg.message_id == message_id:
                msg.acknowledged = True
                msg.acknowledged_at = time.time()
                return True
        return False

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def get_messages(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        msg_type: MessageType | None = None,
        company_id: str | None = None,
        limit: int = 50,
    ) -> list[AgentMessage]:
        """Retrieve messages matching the given conditions."""
        result = self._messages
        if company_id:
            result = [m for m in result if m.company_id == company_id]
        if agent_id:
            result = [
                m
                for m in result
                if m.sender_agent_id == agent_id or m.receiver_agent_id == agent_id
            ]
        if task_id:
            result = [m for m in result if m.task_id == task_id]
        if msg_type:
            result = [m for m in result if m.msg_type == msg_type]
        return result[-limit:]

    def get_thread(self, thread_id: str) -> ConversationThread | None:
        return self._threads.get(thread_id)

    def get_threads_for_task(self, task_id: str) -> list[ConversationThread]:
        return [t for t in self._threads.values() if t.task_id == task_id]

    def get_agent_interactions(self, agent_id: str) -> dict[str, int]:
        """Get per-counterpart message counts for a specific agent."""
        interactions: dict[str, int] = {}
        for msg in self._messages:
            if msg.sender_agent_id == agent_id and msg.receiver_agent_id:
                interactions[msg.receiver_agent_id] = interactions.get(msg.receiver_agent_id, 0) + 1
            elif msg.receiver_agent_id == agent_id and msg.sender_agent_id:
                interactions[msg.sender_agent_id] = interactions.get(msg.sender_agent_id, 0) + 1
        return interactions

    def get_unacknowledged(self, receiver_agent_id: str) -> list[AgentMessage]:
        """Get unacknowledged messages."""
        return [
            m
            for m in self._messages
            if m.receiver_agent_id == receiver_agent_id and not m.acknowledged
        ]

    def get_escalations(self, company_id: str | None = None, limit: int = 20) -> list[AgentMessage]:
        """Get list of escalations."""
        result = [m for m in self._messages if m.msg_type == MessageType.ESCALATION]
        if company_id:
            result = [m for m in result if m.company_id == company_id]
        return result[-limit:]

    def get_recent(self, company_id: str | None = None, limit: int = 100) -> list[AgentMessage]:
        """Get recent messages."""
        result = self._messages
        if company_id:
            result = [m for m in result if m.company_id == company_id]
        return result[-limit:]

    @property
    def total_messages(self) -> int:
        return len(self._messages)

    @property
    def total_threads(self) -> int:
        return len(self._threads)


# Global singleton
comm_log = AgentCommunicationLog()
