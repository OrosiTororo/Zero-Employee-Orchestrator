"""Agent Communication Log — マルチエージェント間通信の記録と可視化.

マルチエージェント協調時のメッセージ交換・委譲・フィードバックを
すべて記録し、ブラックボックス化を防ぐ。

記録されるイベント:
  - タスク委譲（delegation）
  - 成果物の受け渡し（artifact_handoff）
  - フィードバック・質問（feedback）
  - 承認要求・結果（approval_exchange）
  - エスカレーション（escalation）
  - ブロードキャスト（broadcast）

使い方:
  log = comm_log.record(
      msg_type=MessageType.DELEGATION,
      sender_agent_id="agent-A",
      receiver_agent_id="agent-B",
      content="タスク #42 のコード生成を委譲",
      context={"task_id": "42", "reason": "Skill不足"},
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
    """エージェント間メッセージの種類."""

    # タスク関連
    DELEGATION = "delegation"  # タスクの委譲
    DELEGATION_ACCEPT = "delegation_accept"  # 委譲の受諾
    DELEGATION_REJECT = "delegation_reject"  # 委譲の拒否
    TASK_UPDATE = "task_update"  # タスク進捗報告

    # 成果物関連
    ARTIFACT_HANDOFF = "artifact_handoff"  # 成果物の受け渡し
    ARTIFACT_REQUEST = "artifact_request"  # 成果物の要求

    # コミュニケーション
    FEEDBACK = "feedback"  # フィードバック・改善提案
    QUESTION = "question"  # 質問
    ANSWER = "answer"  # 回答
    INSTRUCTION = "instruction"  # 指示

    # 品質・ガバナンス
    QUALITY_REVIEW = "quality_review"  # 品質レビュー結果
    APPROVAL_REQUEST = "approval_request"  # 承認要求
    APPROVAL_RESPONSE = "approval_response"  # 承認結果

    # 異常系
    ESCALATION = "escalation"  # エスカレーション
    ERROR_REPORT = "error_report"  # エラー報告
    HELP_REQUEST = "help_request"  # 支援要求

    # システム
    BROADCAST = "broadcast"  # 全体通知
    HEARTBEAT_PING = "heartbeat_ping"  # 死活確認


class MessagePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class AgentMessage:
    """エージェント間の1メッセージ."""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    msg_type: MessageType = MessageType.TASK_UPDATE
    sender_agent_id: str | None = None  # None = system
    receiver_agent_id: str | None = None  # None = broadcast
    company_id: str | None = None
    task_id: str | None = None
    ticket_id: str | None = None

    content: str = ""  # 人間が読めるメッセージ本文
    structured_data: dict[str, Any] = field(default_factory=dict)

    priority: MessagePriority = MessagePriority.NORMAL
    in_reply_to: str | None = None  # 返信先メッセージID
    thread_id: str | None = None  # スレッドID（会話のグループ化）

    timestamp: float = field(default_factory=time.time)
    acknowledged: bool = False  # 受信確認済み
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
    """エージェント間の会話スレッド."""

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
        # 参加者を自動追加
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
    """エージェント間通信の記録・検索."""

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
        """メッセージを記録."""
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

        # 容量制限
        if len(self._messages) >= self._max_messages:
            self._messages = self._messages[-(self._max_messages // 2) :]

        self._messages.append(msg)

        # スレッドに追加
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
        """タスク委譲を記録（ショートカット）."""
        return self.record(
            msg_type=MessageType.DELEGATION,
            content=f"タスク委譲: {reason}",
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
        """エスカレーションを記録（ショートカット）."""
        return self.record(
            msg_type=MessageType.ESCALATION,
            content=f"エスカレーション [{severity}]: {reason}",
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
        """新しい会話スレッドを作成."""
        thread = ConversationThread(
            task_id=task_id,
            participants=participants or [],
            subject=subject,
        )
        self._threads[thread.thread_id] = thread
        return thread

    def acknowledge(self, message_id: str) -> bool:
        """メッセージの受信を確認."""
        for msg in reversed(self._messages):
            if msg.message_id == message_id:
                msg.acknowledged = True
                msg.acknowledged_at = time.time()
                return True
        return False

    # ------------------------------------------------------------------
    # 検索
    # ------------------------------------------------------------------

    def get_messages(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        msg_type: MessageType | None = None,
        company_id: str | None = None,
        limit: int = 50,
    ) -> list[AgentMessage]:
        """条件に合うメッセージを取得."""
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
        """特定エージェントの通信相手別メッセージ数を取得."""
        interactions: dict[str, int] = {}
        for msg in self._messages:
            if msg.sender_agent_id == agent_id and msg.receiver_agent_id:
                interactions[msg.receiver_agent_id] = (
                    interactions.get(msg.receiver_agent_id, 0) + 1
                )
            elif msg.receiver_agent_id == agent_id and msg.sender_agent_id:
                interactions[msg.sender_agent_id] = (
                    interactions.get(msg.sender_agent_id, 0) + 1
                )
        return interactions

    def get_unacknowledged(self, receiver_agent_id: str) -> list[AgentMessage]:
        """未確認メッセージを取得."""
        return [
            m
            for m in self._messages
            if m.receiver_agent_id == receiver_agent_id and not m.acknowledged
        ]

    def get_escalations(
        self, company_id: str | None = None, limit: int = 20
    ) -> list[AgentMessage]:
        """エスカレーション一覧を取得."""
        result = [m for m in self._messages if m.msg_type == MessageType.ESCALATION]
        if company_id:
            result = [m for m in result if m.company_id == company_id]
        return result[-limit:]

    def get_recent(
        self, company_id: str | None = None, limit: int = 100
    ) -> list[AgentMessage]:
        """最近のメッセージを取得."""
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
