"""A2A Bidirectional Communication — Inter-agent bidirectional communication hub.

Supports not only parent-to-child sub-agent instructions, but also peer-to-peer
communication, negotiation, and channel-based broadcasting.

Key features:
  - Direct message send/receive
  - Group communication via named channels
  - Message thread tracking
  - Inter-agent negotiation protocol
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MessagePriority(str, Enum):
    """Message priority."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageType(str, Enum):
    """Message type."""

    REQUEST = "request"  # Request
    RESPONSE = "response"  # Response
    BROADCAST = "broadcast"  # Broadcast
    NOTIFICATION = "notification"  # Notification
    NEGOTIATION = "negotiation"  # Negotiation


class NegotiationStatus(str, Enum):
    """Negotiation status."""

    PROPOSED = "proposed"
    COUNTER_PROPOSED = "counter_proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"


@dataclass
class AgentMessage:
    """A single message between agents."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    receiver_id: str = ""  # Empty string means broadcast
    message_type: MessageType = MessageType.NOTIFICATION
    priority: MessagePriority = MessagePriority.NORMAL
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    read_at: datetime | None = None
    reply_to: str | None = None  # Reply-to message ID

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation."""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "reply_to": self.reply_to,
        }


@dataclass
class AgentMailbox:
    """Agent mailbox."""

    agent_id: str = ""
    inbox: list[AgentMessage] = field(default_factory=list)
    outbox: list[AgentMessage] = field(default_factory=list)
    unread_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation."""
        return {
            "agent_id": self.agent_id,
            "inbox_count": len(self.inbox),
            "outbox_count": len(self.outbox),
            "unread_count": self.unread_count,
        }


@dataclass
class Negotiation:
    """Inter-agent negotiation session."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    participants: list[str] = field(default_factory=list)
    initial_proposal: str = ""
    proposals: list[dict[str, Any]] = field(default_factory=list)
    status: NegotiationStatus = NegotiationStatus.PROPOSED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation."""
        return {
            "id": self.id,
            "topic": self.topic,
            "participants": self.participants,
            "initial_proposal": self.initial_proposal,
            "proposals": self.proposals,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": (self.resolved_at.isoformat() if self.resolved_at else None),
        }


# ---------------------------------------------------------------------------
# A2A Communication Hub
# ---------------------------------------------------------------------------

_MAX_MAILBOX_SIZE = 2000
_MAX_TOTAL_MESSAGES = 50_000


class A2ACommunicationHub:
    """Inter-agent bidirectional communication hub.

    Assigns a mailbox to each agent and provides direct messaging,
    channel broadcasting, and negotiation protocol.
    """

    def __init__(self) -> None:
        self._mailboxes: dict[str, AgentMailbox] = {}
        self._channels: dict[str, list[str]] = {}  # channel_name -> [agent_ids]
        self._negotiations: dict[str, Negotiation] = {}
        self._all_messages: list[AgentMessage] = []
        self._message_index: dict[str, AgentMessage] = {}  # O(1) lookup by ID

    # ------------------------------------------------------------------
    # Agent registration
    # ------------------------------------------------------------------

    def register_agent(self, agent_id: str) -> AgentMailbox:
        """Register an agent and create a mailbox."""
        if agent_id in self._mailboxes:
            logger.debug("Agent '%s' already registered", agent_id)
            return self._mailboxes[agent_id]

        mailbox = AgentMailbox(agent_id=agent_id)
        self._mailboxes[agent_id] = mailbox
        logger.info("A2A: Agent '%s' registered", agent_id)
        return mailbox

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id not in self._mailboxes:
            return False

        del self._mailboxes[agent_id]

        # Remove from channels as well
        for subscribers in self._channels.values():
            if agent_id in subscribers:
                subscribers.remove(agent_id)

        logger.info("A2A: Agent '%s' unregistered", agent_id)
        return True

    # ------------------------------------------------------------------
    # Message send/receive
    # ------------------------------------------------------------------

    def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        content: str,
        msg_type: MessageType = MessageType.REQUEST,
        priority: MessagePriority = MessagePriority.NORMAL,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> AgentMessage:
        """Send a direct message.

        Args:
            sender_id: Sender agent ID.
            receiver_id: Receiver agent ID.
            content: Message body.
            msg_type: Message type.
            priority: Priority level.
            metadata: Additional metadata.

        Returns:
            The sent message.
        """
        # Auto-register unregistered agents
        if sender_id not in self._mailboxes:
            self.register_agent(sender_id)
        if receiver_id not in self._mailboxes:
            self.register_agent(receiver_id)

        msg = AgentMessage(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=msg_type,
            priority=priority,
            content=content,
            metadata=metadata or {},
        )

        # Deliver to mailboxes
        sender_mb = self._mailboxes[sender_id]
        receiver_mb = self._mailboxes[receiver_id]

        sender_mb.outbox.append(msg)
        receiver_mb.inbox.append(msg)
        receiver_mb.unread_count += 1

        # Capacity limit
        self._trim_mailbox(sender_mb)
        self._trim_mailbox(receiver_mb)

        self._all_messages.append(msg)
        self._message_index[msg.id] = msg

        # Prevent unbounded memory growth
        if len(self._all_messages) > _MAX_TOTAL_MESSAGES:
            removed = self._all_messages[: len(self._all_messages) - _MAX_TOTAL_MESSAGES]
            self._all_messages = self._all_messages[-_MAX_TOTAL_MESSAGES:]
            for old_msg in removed:
                self._message_index.pop(old_msg.id, None)

        logger.debug(
            "A2A: %s -> %s [%s] %s",
            sender_id,
            receiver_id,
            msg_type.value,
            content[:60],
        )
        return msg

    def broadcast(
        self,
        sender_id: str,
        channel: str,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> list[AgentMessage]:
        """Broadcast to all subscribed agents in a channel.

        Args:
            sender_id: Sender agent ID.
            channel: Channel name.
            content: Message body.
            metadata: Additional metadata.

        Returns:
            List of sent messages.
        """
        subscribers = self._channels.get(channel, [])
        if not subscribers:
            logger.warning("A2A broadcast: channel '%s' has no subscribers", channel)
            return []

        messages: list[AgentMessage] = []
        for subscriber_id in subscribers:
            if subscriber_id == sender_id:
                continue  # Don't send to self
            msg = self.send_message(
                sender_id=sender_id,
                receiver_id=subscriber_id,
                content=content,
                msg_type=MessageType.BROADCAST,
                priority=MessagePriority.NORMAL,
                metadata={"channel": channel, **(metadata or {})},
            )
            messages.append(msg)

        logger.info(
            "A2A broadcast: %s -> channel '%s' (%d recipients)",
            sender_id,
            channel,
            len(messages),
        )
        return messages

    def receive_messages(
        self,
        agent_id: str,
        unread_only: bool = False,
    ) -> list[AgentMessage]:
        """Retrieve received messages for an agent.

        Args:
            agent_id: Agent ID.
            unread_only: If True, return only unread messages.

        Returns:
            List of messages.
        """
        mailbox = self._mailboxes.get(agent_id)
        if not mailbox:
            return []

        if unread_only:
            messages = [m for m in mailbox.inbox if m.read_at is None]
        else:
            messages = list(mailbox.inbox)

        # Mark as read
        now = datetime.now(UTC)
        for msg in messages:
            if msg.read_at is None:
                msg.read_at = now
        mailbox.unread_count = max(
            0,
            mailbox.unread_count - len([m for m in messages if m.read_at == now]),
        )

        return messages

    def reply(
        self,
        agent_id: str,
        original_msg_id: str,
        content: str,
    ) -> AgentMessage | None:
        """Reply to a message.

        Args:
            agent_id: Replier's agent ID.
            original_msg_id: Original message ID to reply to.
            content: Reply content.

        Returns:
            The reply message. None if the original message is not found.
        """
        # O(1) lookup via message index instead of linear scan
        original = self._message_index.get(original_msg_id)

        if original is None:
            logger.warning("A2A reply: original message '%s' not found", original_msg_id)
            return None

        reply_msg = self.send_message(
            sender_id=agent_id,
            receiver_id=original.sender_id,
            content=content,
            msg_type=MessageType.RESPONSE,
            priority=original.priority,
            metadata={"reply_to": original_msg_id},
        )
        reply_msg.reply_to = original_msg_id
        return reply_msg

    # ------------------------------------------------------------------
    # Channel management
    # ------------------------------------------------------------------

    def create_channel(self, name: str, creator_id: str) -> bool:
        """Create a named channel.

        Args:
            name: Channel name.
            creator_id: Creator agent ID (auto-subscribed).

        Returns:
            True if created successfully, False if already exists.
        """
        if name in self._channels:
            logger.debug("A2A: channel '%s' already exists", name)
            return False

        self._channels[name] = [creator_id]
        if creator_id not in self._mailboxes:
            self.register_agent(creator_id)

        logger.info("A2A: channel '%s' created by '%s'", name, creator_id)
        return True

    def join_channel(self, channel: str, agent_id: str) -> bool:
        """Join a channel."""
        if channel not in self._channels:
            logger.warning("A2A: channel '%s' does not exist", channel)
            return False

        subscribers = self._channels[channel]
        if agent_id in subscribers:
            return True  # Already joined

        subscribers.append(agent_id)
        if agent_id not in self._mailboxes:
            self.register_agent(agent_id)

        logger.debug("A2A: '%s' joined channel '%s'", agent_id, channel)
        return True

    def leave_channel(self, channel: str, agent_id: str) -> bool:
        """Leave a channel."""
        if channel not in self._channels:
            return False

        subscribers = self._channels[channel]
        if agent_id not in subscribers:
            return False

        subscribers.remove(agent_id)
        logger.debug("A2A: '%s' left channel '%s'", agent_id, channel)
        return True

    # ------------------------------------------------------------------
    # Negotiation protocol
    # ------------------------------------------------------------------

    def negotiate(
        self,
        agent_ids: list[str],
        topic: str,
        initial_proposal: str,
    ) -> Negotiation:
        """Start a negotiation session between agents.

        Args:
            agent_ids: List of participating agent IDs.
            topic: Negotiation topic.
            initial_proposal: Initial proposal.

        Returns:
            The created negotiation session.
        """
        negotiation = Negotiation(
            topic=topic,
            participants=list(agent_ids),
            initial_proposal=initial_proposal,
            proposals=[
                {
                    "proposer": agent_ids[0] if agent_ids else "system",
                    "content": initial_proposal,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ],
        )
        self._negotiations[negotiation.id] = negotiation

        # Notify all participants of negotiation start
        initiator = agent_ids[0] if agent_ids else "system"
        for agent_id in agent_ids:
            if agent_id not in self._mailboxes:
                self.register_agent(agent_id)
            if agent_id != initiator:
                self.send_message(
                    sender_id=initiator,
                    receiver_id=agent_id,
                    content=f"Negotiation started: {topic} — Proposal: {initial_proposal}",
                    msg_type=MessageType.NEGOTIATION,
                    priority=MessagePriority.HIGH,
                    metadata={
                        "negotiation_id": negotiation.id,
                        "action": "start",
                    },
                )

        logger.info(
            "A2A negotiation started: '%s' with %d participants",
            topic,
            len(agent_ids),
        )
        return negotiation

    def counter_propose(
        self,
        negotiation_id: str,
        agent_id: str,
        proposal: str,
    ) -> bool:
        """Submit a counter-proposal for a negotiation."""
        neg = self._negotiations.get(negotiation_id)
        if not neg or agent_id not in neg.participants:
            return False

        neg.proposals.append(
            {
                "proposer": agent_id,
                "content": proposal,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        neg.status = NegotiationStatus.COUNTER_PROPOSED

        # Notify other participants
        for pid in neg.participants:
            if pid != agent_id:
                self.send_message(
                    sender_id=agent_id,
                    receiver_id=pid,
                    content=f"Counter-proposal: {proposal}",
                    msg_type=MessageType.NEGOTIATION,
                    priority=MessagePriority.HIGH,
                    metadata={
                        "negotiation_id": negotiation_id,
                        "action": "counter_propose",
                    },
                )
        return True

    def resolve_negotiation(
        self,
        negotiation_id: str,
        accepted: bool,
    ) -> bool:
        """Resolve a negotiation."""
        neg = self._negotiations.get(negotiation_id)
        if not neg:
            return False

        neg.status = NegotiationStatus.ACCEPTED if accepted else NegotiationStatus.REJECTED
        neg.resolved_at = datetime.now(UTC)
        return True

    # ------------------------------------------------------------------
    # Thread tracking
    # ------------------------------------------------------------------

    def get_conversation_thread(self, message_id: str) -> list[AgentMessage]:
        """Retrieve a conversation thread starting from a message ID.

        Returns the specified message and all its reply chains in chronological order.
        """
        # Find root message
        root_id = message_id
        visited: set[str] = set()
        while True:
            if root_id in visited:
                break
            visited.add(root_id)
            parent = None
            for msg in self._all_messages:
                if msg.id == root_id and msg.reply_to:
                    parent = msg.reply_to
                    break
            if parent is None:
                break
            root_id = parent

        # Collect all descendants from root
        thread: list[AgentMessage] = []
        queue = [root_id]
        seen: set[str] = set()

        while queue:
            current_id = queue.pop(0)
            if current_id in seen:
                continue
            seen.add(current_id)

            for msg in self._all_messages:
                if msg.id == current_id:
                    thread.append(msg)
                if msg.reply_to == current_id and msg.id not in seen:
                    queue.append(msg.id)

        # Sort chronologically
        thread.sort(key=lambda m: m.created_at)
        return thread

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _trim_mailbox(self, mailbox: AgentMailbox) -> None:
        """Apply mailbox capacity limits."""
        if len(mailbox.inbox) > _MAX_MAILBOX_SIZE:
            mailbox.inbox = mailbox.inbox[-_MAX_MAILBOX_SIZE:]
        if len(mailbox.outbox) > _MAX_MAILBOX_SIZE:
            mailbox.outbox = mailbox.outbox[-_MAX_MAILBOX_SIZE:]

    def get_mailbox(self, agent_id: str) -> AgentMailbox | None:
        """Get an agent's mailbox."""
        return self._mailboxes.get(agent_id)

    def list_channels(self) -> dict[str, int]:
        """Return all channels and their subscriber counts."""
        return {name: len(subs) for name, subs in self._channels.items()}

    def get_negotiation(self, negotiation_id: str) -> Negotiation | None:
        """Get a negotiation session."""
        return self._negotiations.get(negotiation_id)

    @property
    def total_agents(self) -> int:
        """Number of registered agents."""
        return len(self._mailboxes)

    @property
    def total_messages(self) -> int:
        """Total number of messages."""
        return len(self._all_messages)


# Global instance
a2a_hub = A2ACommunicationHub()
