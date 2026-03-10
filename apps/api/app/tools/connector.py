"""外部ツール接続 — Tool Connection の管理と実行.

Zero-Employee Orchestrator.md §42.1 に基づき、外部ツールとの接続を管理する。
MCP、Webhook、外部 API など多様な接続タイプに対応する。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionType(str, Enum):
    """外部接続のタイプ."""

    REST_API = "rest_api"
    WEBHOOK = "webhook"
    MCP = "mcp"
    OAUTH = "oauth"
    WEBSOCKET = "websocket"
    FILE_SYSTEM = "file_system"
    DATABASE = "database"
    CLI_TOOL = "cli_tool"
    GRPC = "grpc"
    GRAPHQL = "graphql"


class ConnectionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING_AUTH = "pending_auth"


class AuthType(str, Enum):
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    SERVICE_ACCOUNT = "service_account"


@dataclass
class ToolCallResult:
    """ツール呼び出しの結果."""

    tool_name: str
    success: bool
    response: dict | str | None = None
    error: str | None = None
    latency_ms: int = 0
    trace_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass
class ToolConnectionConfig:
    """ツール接続の設定."""

    name: str
    connection_type: ConnectionType
    auth_type: AuthType = AuthType.NONE
    base_url: str | None = None
    config: dict | None = None


class ToolConnector:
    """外部ツールへの接続を管理するコネクタ.

    対応可能な CLI ツール例:
    - gws (Google Workspace CLI) — Google Workspace API 全操作
    - gh (GitHub CLI) — GitHub リポジトリ・Issue・PR 操作
    - aws (AWS CLI) — AWS サービス操作
    - gcloud (Google Cloud CLI) — GCP サービス操作
    - az (Azure CLI) — Azure サービス操作
    """

    def __init__(self) -> None:
        self._connections: dict[str, ToolConnectionConfig] = {}

    def register(self, config: ToolConnectionConfig) -> str:
        """ツール接続を登録する."""
        conn_id = str(uuid.uuid4())
        self._connections[conn_id] = config
        logger.info("Tool connection registered: %s (%s)", config.name, config.connection_type)
        return conn_id

    def get_connection(self, conn_id: str) -> ToolConnectionConfig | None:
        return self._connections.get(conn_id)

    def list_connections(self) -> list[tuple[str, ToolConnectionConfig]]:
        return list(self._connections.items())

    async def execute(
        self,
        conn_id: str,
        method: str,
        payload: dict | None = None,
        trace_id: str | None = None,
    ) -> ToolCallResult:
        """ツールを実行する（サブクラスで具体実装を行う）."""
        config = self._connections.get(conn_id)
        if config is None:
            return ToolCallResult(
                tool_name="unknown",
                success=False,
                error=f"Connection not found: {conn_id}",
                trace_id=trace_id,
            )

        started_at = datetime.now(timezone.utc)
        try:
            # 具体的な実行はサブクラスまたは Provider 別の実装で行う
            result = ToolCallResult(
                tool_name=config.name,
                success=True,
                response={"method": method, "status": "executed"},
                trace_id=trace_id or str(uuid.uuid4()),
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
            )
            latency = (result.finished_at - started_at).total_seconds() * 1000
            result.latency_ms = int(latency)
            return result

        except Exception as exc:
            logger.error("Tool execution failed for %s: %s", config.name, exc)
            return ToolCallResult(
                tool_name=config.name,
                success=False,
                error=str(exc),
                trace_id=trace_id,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
            )


# グローバルインスタンス
tool_connector = ToolConnector()
