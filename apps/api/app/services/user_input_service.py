"""User input request management service during task execution.

Used when AI tasks require additional information from the user during execution.
Supports multiple input types including text input, file attachments, choices,
and confirmation dialogs, with timeout and cancellation management.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


class InputRequestType(str, Enum):
    """入力リクエストの種別."""

    TEXT = "text"
    FILE = "file"
    CHOICE = "choice"
    CONFIRMATION = "confirmation"
    MULTI_FILE = "multi_file"


class InputRequestStatus(str, Enum):
    """入力リクエストのステータス."""

    PENDING = "pending"
    ANSWERED = "answered"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class InputRequest:
    """ユーザー入力リクエストを表すデータクラス."""

    id: str
    task_id: str
    request_type: InputRequestType
    prompt_text: str
    options: list[str] | None = None
    timeout_seconds: int = 300
    status: InputRequestStatus = InputRequestStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    answered_at: datetime | None = None
    response: str | list[str] | bool | None = None


class UserInputService:
    """タスク実行中のユーザー入力リクエストを管理するサービス.

    AIタスクがユーザーから追加情報を必要とする場合に、
    リクエストの作成・回答・期限切れ管理を行う。
    """

    def __init__(self) -> None:
        """サービスを初期化する."""
        self._requests: dict[str, InputRequest] = {}

    async def request_input(
        self,
        task_id: str,
        request_type: InputRequestType,
        prompt_text: str,
        *,
        options: list[str] | None = None,
        timeout_seconds: int = 300,
    ) -> str:
        """入力リクエストを作成して保存する.

        Args:
            task_id: 対象タスクのID
            request_type: 入力の種別
            prompt_text: ユーザーに表示するプロンプト
            options: CHOICE タイプの場合の選択肢リスト
            timeout_seconds: タイムアウト秒数（デフォルト300秒）

        Returns:
            作成されたリクエストのID

        Raises:
            ValueError: CHOICE タイプで options が未指定の場合
        """
        if request_type == InputRequestType.CHOICE and not options:
            raise ValueError("CHOICE タイプのリクエストには options が必要です")

        request_id = str(uuid.uuid4())
        request = InputRequest(
            id=request_id,
            task_id=task_id,
            request_type=request_type,
            prompt_text=prompt_text,
            options=options,
            timeout_seconds=timeout_seconds,
        )
        self._requests[request_id] = request
        logger.info(
            "入力リクエスト作成: id=%s, task=%s, type=%s",
            request_id,
            task_id,
            request_type.value,
        )
        return request_id

    async def answer_input(
        self,
        request_id: str,
        response: str | list[str] | bool,
    ) -> InputRequest:
        """入力リクエストに回答する.

        Args:
            request_id: リクエストID
            response: ユーザーの回答

        Returns:
            更新されたリクエスト

        Raises:
            KeyError: リクエストが見つからない場合
            ValueError: 既に回答済み・期限切れ・キャンセル済みの場合
        """
        request = self._requests.get(request_id)
        if request is None:
            raise KeyError(f"入力リクエストが見つかりません: {request_id}")

        if request.status != InputRequestStatus.PENDING:
            raise ValueError(f"リクエストは回答できない状態です: {request.status.value}")

        # CHOICE タイプの場合、回答が選択肢に含まれるか検証
        if (
            request.request_type == InputRequestType.CHOICE
            and request.options
            and isinstance(response, str)
            and response not in request.options
        ):
            raise ValueError(f"無効な選択肢です: {response} (有効: {request.options})")

        request.status = InputRequestStatus.ANSWERED
        request.answered_at = datetime.now(UTC)
        request.response = response
        logger.info("入力リクエスト回答: id=%s", request_id)
        return request

    async def get_pending_requests(self, task_id: str) -> list[InputRequest]:
        """指定タスクの未回答リクエスト一覧を取得する.

        Args:
            task_id: タスクID

        Returns:
            未回答リクエストのリスト
        """
        return [
            r
            for r in self._requests.values()
            if r.task_id == task_id and r.status == InputRequestStatus.PENDING
        ]

    async def cancel_request(self, request_id: str) -> InputRequest:
        """入力リクエストをキャンセルする.

        Args:
            request_id: リクエストID

        Returns:
            キャンセルされたリクエスト

        Raises:
            KeyError: リクエストが見つからない場合
            ValueError: 既に回答済みの場合
        """
        request = self._requests.get(request_id)
        if request is None:
            raise KeyError(f"入力リクエストが見つかりません: {request_id}")

        if request.status == InputRequestStatus.ANSWERED:
            raise ValueError("回答済みのリクエストはキャンセルできません")

        request.status = InputRequestStatus.CANCELLED
        logger.info("入力リクエストキャンセル: id=%s", request_id)
        return request

    async def expire_stale_requests(self) -> list[str]:
        """タイムアウトした未回答リクエストを期限切れにする.

        Returns:
            期限切れにしたリクエストIDのリスト
        """
        now = datetime.now(UTC)
        expired_ids: list[str] = []

        for request in self._requests.values():
            if request.status != InputRequestStatus.PENDING:
                continue
            elapsed = (now - request.created_at).total_seconds()
            if elapsed >= request.timeout_seconds:
                request.status = InputRequestStatus.EXPIRED
                expired_ids.append(request.id)
                logger.info(
                    "入力リクエスト期限切れ: id=%s (elapsed=%.0fs)",
                    request.id,
                    elapsed,
                )

        return expired_ids

    async def wait_for_answer(
        self,
        request_id: str,
        poll_interval: float = 1.0,
    ) -> InputRequest:
        """回答が来るまで非同期で待機する.

        Args:
            request_id: リクエストID
            poll_interval: ポーリング間隔（秒）

        Returns:
            回答済みまたは期限切れのリクエスト

        Raises:
            KeyError: リクエストが見つからない場合
            TimeoutError: タイムアウトした場合
        """
        request = self._requests.get(request_id)
        if request is None:
            raise KeyError(f"入力リクエストが見つかりません: {request_id}")

        deadline = request.created_at.timestamp() + request.timeout_seconds

        while request.status == InputRequestStatus.PENDING:
            now = datetime.now(UTC).timestamp()
            if now >= deadline:
                request.status = InputRequestStatus.EXPIRED
                logger.info("入力リクエスト待機タイムアウト: id=%s", request_id)
                raise TimeoutError(f"入力リクエストがタイムアウトしました: {request_id}")
            await asyncio.sleep(poll_interval)

        return request

    def get_request(self, request_id: str) -> InputRequest | None:
        """リクエストをIDで取得する.

        Args:
            request_id: リクエストID

        Returns:
            リクエスト（存在しない場合は None）
        """
        return self._requests.get(request_id)


# ---------------------------------------------------------------------------
# グローバルインスタンス
# ---------------------------------------------------------------------------
user_input_service = UserInputService()
