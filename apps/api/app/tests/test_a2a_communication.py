"""Tests for A2ACommunicationHub inter-agent messaging.

Verifies:
- Agent registration and mailbox creation
- Direct message send/receive
- Channel create/join/leave/broadcast
- Message reply threading
- Negotiation protocol lifecycle
- Unregister agent cleanup
"""

from __future__ import annotations

import pytest


@pytest.fixture
def hub():
    from app.orchestration.a2a_communication import A2ACommunicationHub

    return A2ACommunicationHub()


class TestAgentRegistration:
    def test_register_creates_mailbox(self, hub) -> None:
        mailbox = hub.register_agent("agent-1")
        assert mailbox.agent_id == "agent-1"
        assert mailbox.inbox == []
        assert mailbox.unread_count == 0

    def test_register_twice_returns_same_mailbox(self, hub) -> None:
        m1 = hub.register_agent("agent-1")
        m2 = hub.register_agent("agent-1")
        assert m1 is m2

    def test_unregister_returns_true(self, hub) -> None:
        hub.register_agent("agent-1")
        result = hub.unregister_agent("agent-1")
        assert result is True

    def test_unregister_nonexistent_returns_false(self, hub) -> None:
        result = hub.unregister_agent("nonexistent")
        assert result is False

    def test_unregister_removes_from_channels(self, hub) -> None:
        hub.register_agent("a1")
        hub.register_agent("a2")
        hub.create_channel("general", "a1")
        hub.join_channel("general", "a2")
        hub.unregister_agent("a2")
        # a2 should no longer be in the channel
        assert "a2" not in hub._channels.get("general", [])


class TestDirectMessaging:
    def test_send_delivers_to_inbox(self, hub) -> None:
        hub.register_agent("sender")
        hub.register_agent("receiver")
        msg = hub.send_message("sender", "receiver", "Hello!")
        inbox = hub.receive_messages("receiver")
        assert len(inbox) == 1
        assert inbox[0].content == "Hello!"
        assert inbox[0].id == msg.id

    def test_send_populates_outbox(self, hub) -> None:
        hub.register_agent("s")
        hub.register_agent("r")
        hub.send_message("s", "r", "test")
        outbox = hub._mailboxes["s"].outbox
        assert len(outbox) == 1

    def test_receive_marks_as_read(self, hub) -> None:
        hub.register_agent("s")
        hub.register_agent("r")
        hub.send_message("s", "r", "read me")
        hub.receive_messages("r")
        assert hub._mailboxes["r"].unread_count == 0

    def test_unread_only_filter(self, hub) -> None:
        hub.register_agent("s")
        hub.register_agent("r")
        hub.send_message("s", "r", "msg1")
        hub.send_message("s", "r", "msg2")
        # Read first message
        hub.receive_messages("r")
        # Both now read — unread_only should return empty
        unread = hub.receive_messages("r", unread_only=True)
        assert unread == []

    def test_send_to_unregistered_auto_registers(self, hub) -> None:
        hub.register_agent("s")
        # receiver not registered — should still work (auto-register)
        msg = hub.send_message("s", "new-receiver", "auto-register test")
        assert msg is not None

    def test_receive_from_unregistered_returns_empty(self, hub) -> None:
        result = hub.receive_messages("nobody")
        assert result == []


class TestReply:
    def test_reply_creates_thread(self, hub) -> None:
        hub.register_agent("a1")
        hub.register_agent("a2")
        original = hub.send_message("a1", "a2", "Question?")
        reply = hub.reply("a2", original.id, "Answer!")
        assert reply is not None
        assert reply.reply_to == original.id
        assert reply.receiver_id == "a1"

    def test_reply_to_nonexistent_returns_none(self, hub) -> None:
        hub.register_agent("a1")
        result = hub.reply("a1", "fake-id-xyz", "Reply")
        assert result is None


class TestChannels:
    def test_create_channel(self, hub) -> None:
        hub.register_agent("creator")
        result = hub.create_channel("engineering", "creator")
        assert result is True
        assert "engineering" in hub._channels

    def test_create_existing_channel_returns_false(self, hub) -> None:
        hub.register_agent("c")
        hub.create_channel("ch", "c")
        result = hub.create_channel("ch", "c")
        assert result is False

    def test_join_channel(self, hub) -> None:
        hub.register_agent("creator")
        hub.register_agent("joiner")
        hub.create_channel("public", "creator")
        result = hub.join_channel("public", "joiner")
        assert result is True
        assert "joiner" in hub._channels["public"]

    def test_join_nonexistent_channel_returns_false(self, hub) -> None:
        hub.register_agent("a")
        result = hub.join_channel("nonexistent", "a")
        assert result is False

    def test_leave_channel(self, hub) -> None:
        hub.register_agent("a1")
        hub.register_agent("a2")
        hub.create_channel("ch", "a1")
        hub.join_channel("ch", "a2")
        result = hub.leave_channel("ch", "a2")
        assert result is True
        assert "a2" not in hub._channels["ch"]

    def test_broadcast_delivers_to_all_subscribers(self, hub) -> None:
        hub.register_agent("broadcaster")
        hub.register_agent("sub1")
        hub.register_agent("sub2")
        hub.create_channel("announcements", "broadcaster")
        hub.join_channel("announcements", "sub1")
        hub.join_channel("announcements", "sub2")
        msgs = hub.broadcast("broadcaster", "announcements", "Hello everyone!")
        assert len(msgs) == 2
        # sub1 and sub2 should have received the message
        sub1_inbox = hub.receive_messages("sub1")
        sub2_inbox = hub.receive_messages("sub2")
        assert any("Hello everyone!" in m.content for m in sub1_inbox)
        assert any("Hello everyone!" in m.content for m in sub2_inbox)

    def test_broadcast_does_not_send_to_self(self, hub) -> None:
        hub.register_agent("broadcaster")
        hub.register_agent("sub")
        hub.create_channel("ch", "broadcaster")
        hub.join_channel("ch", "sub")
        hub.broadcast("broadcaster", "ch", "msg")
        broadcaster_inbox = hub.receive_messages("broadcaster")
        assert len(broadcaster_inbox) == 0

    def test_broadcast_empty_channel_returns_empty(self, hub) -> None:
        hub.register_agent("sender")
        hub.create_channel("empty", "sender")
        msgs = hub.broadcast("sender", "empty", "nobody to hear this")
        assert msgs == []


class TestNegotiation:
    def test_negotiate_creates_session(self, hub) -> None:
        from app.orchestration.a2a_communication import NegotiationStatus

        hub.register_agent("a1")
        hub.register_agent("a2")
        neg = hub.negotiate(["a1", "a2"], "Deadline extension?", "Extend by 2 weeks")
        assert neg.topic == "Deadline extension?"
        assert neg.status == NegotiationStatus.PROPOSED
        assert "a1" in neg.participants
        assert "a2" in neg.participants

    def test_negotiate_has_initial_proposal(self, hub) -> None:
        neg = hub.negotiate(["x", "y"], "Budget", "Allocate $10k")
        assert neg.initial_proposal == "Allocate $10k"
        assert len(neg.proposals) >= 1
        assert neg.proposals[0]["content"] == "Allocate $10k"

    def test_negotiation_to_dict(self, hub) -> None:
        neg = hub.negotiate(["a", "b"], "topic", "proposal")
        d = neg.to_dict()
        assert "id" in d
        assert "status" in d
        assert d["status"] == "proposed"


class TestMailboxToDict:
    def test_mailbox_to_dict_shape(self, hub) -> None:
        mailbox = hub.register_agent("agent-x")
        d = mailbox.to_dict()
        assert d["agent_id"] == "agent-x"
        assert "inbox_count" in d
        assert "outbox_count" in d
        assert "unread_count" in d
