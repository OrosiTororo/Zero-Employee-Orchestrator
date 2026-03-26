"""外部ツール接続 — Tool Connection の管理と実行.

Zero-Employee Orchestrator.md §42.1 に基づき、外部ツールとの接続を管理する。
MCP、Webhook、外部 API、CLI ツールなど多様な接続タイプに対応し、
接続タイプごとに適切なディスパッチを行う。
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

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
    """接続のステータス."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING_AUTH = "pending_auth"


class AuthType(str, Enum):
    """認証タイプ."""

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
    config: dict[str, Any] | None = None
    credentials: dict[str, str] = field(default_factory=dict)
    status: ConnectionStatus = ConnectionStatus.ACTIVE
    timeout_seconds: int = 30


class ToolConnector:
    """外部ツールへの接続を管理するコネクタ.

    対応する接続タイプごとに適切なディスパッチを行い、
    REST API / GraphQL / CLI / Webhook / MCP など多様な外部システムと通信する。

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
        """接続設定を取得する."""
        return self._connections.get(conn_id)

    def list_connections(self) -> list[tuple[str, ToolConnectionConfig]]:
        """登録済みの全接続を返す."""
        return list(self._connections.items())

    def remove(self, conn_id: str) -> bool:
        """接続を削除する."""
        if conn_id in self._connections:
            config = self._connections.pop(conn_id)
            logger.info("Tool connection removed: %s", config.name)
            return True
        return False

    def update_credentials(self, conn_id: str, credentials: dict[str, str]) -> bool:
        """接続の認証情報を更新する."""
        config = self._connections.get(conn_id)
        if config is None:
            return False
        config.credentials = credentials
        config.status = ConnectionStatus.ACTIVE
        logger.info("Credentials updated for connection: %s", config.name)
        return True

    async def execute(
        self,
        conn_id: str,
        method: str,
        payload: dict | None = None,
        trace_id: str | None = None,
    ) -> ToolCallResult:
        """ツールを実行する — 接続タイプに応じてディスパッチ."""
        config = self._connections.get(conn_id)
        if config is None:
            return ToolCallResult(
                tool_name="unknown",
                success=False,
                error=f"Connection not found: {conn_id}",
                trace_id=trace_id,
            )

        if config.status != ConnectionStatus.ACTIVE:
            return ToolCallResult(
                tool_name=config.name,
                success=False,
                error=f"Connection is not active: {config.status.value}",
                trace_id=trace_id,
            )

        resolved_trace = trace_id or str(uuid.uuid4())
        started_at = datetime.now(UTC)

        try:
            dispatch_map = {
                ConnectionType.REST_API: self._execute_rest_api,
                ConnectionType.GRAPHQL: self._execute_graphql,
                ConnectionType.CLI_TOOL: self._execute_cli,
                ConnectionType.WEBHOOK: self._execute_webhook,
                ConnectionType.MCP: self._execute_mcp,
                ConnectionType.WEBSOCKET: self._execute_websocket,
                ConnectionType.FILE_SYSTEM: self._execute_file_system,
                ConnectionType.DATABASE: self._execute_database,
                ConnectionType.GRPC: self._execute_grpc,
                ConnectionType.OAUTH: self._execute_oauth,
            }

            handler = dispatch_map.get(config.connection_type)
            if handler is None:
                return ToolCallResult(
                    tool_name=config.name,
                    success=False,
                    error=f"Unsupported connection type: {config.connection_type}",
                    trace_id=resolved_trace,
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                )

            response = await handler(config, method, payload or {})
            finished_at = datetime.now(UTC)
            latency = int((finished_at - started_at).total_seconds() * 1000)

            result = ToolCallResult(
                tool_name=config.name,
                success=True,
                response=response,
                trace_id=resolved_trace,
                started_at=started_at,
                finished_at=finished_at,
                latency_ms=latency,
            )
            logger.info(
                "Tool executed: %s (%s) in %dms",
                config.name,
                config.connection_type.value,
                latency,
            )
            return result

        except Exception as exc:
            logger.error("Tool execution failed for %s: %s", config.name, exc)
            config.status = ConnectionStatus.ERROR
            return ToolCallResult(
                tool_name=config.name,
                success=False,
                error=str(exc),
                trace_id=resolved_trace,
                started_at=started_at,
                finished_at=datetime.now(UTC),
            )

    async def execute_batch(
        self,
        conn_id: str,
        calls: list[dict[str, Any]],
        trace_id: str | None = None,
    ) -> list[ToolCallResult]:
        """複数のツール呼び出しをバッチ実行する.

        Parameters
        ----------
        conn_id: 接続 ID
        calls: ``[{"method": str, "payload": dict}, ...]`` 形式のリスト
        trace_id: 親トレース ID（各呼び出しに引き継がれる）
        """
        results: list[ToolCallResult] = []
        for call in calls:
            result = await self.execute(
                conn_id=conn_id,
                method=call.get("method", ""),
                payload=call.get("payload"),
                trace_id=trace_id,
            )
            results.append(result)
        return results

    async def health_check(self, conn_id: str) -> ToolCallResult:
        """接続のヘルスチェックを実行する."""
        config = self._connections.get(conn_id)
        if config is None:
            return ToolCallResult(
                tool_name="unknown",
                success=False,
                error=f"Connection not found: {conn_id}",
            )

        started_at = datetime.now(UTC)
        try:
            if config.connection_type in (
                ConnectionType.REST_API,
                ConnectionType.GRAPHQL,
                ConnectionType.WEBHOOK,
                ConnectionType.OAUTH,
            ):
                result = await self._http_health_check(config)
            elif config.connection_type == ConnectionType.CLI_TOOL:
                result = await self._cli_health_check(config)
            elif config.connection_type == ConnectionType.MCP:
                result = {"status": "ok", "type": "mcp"}
            else:
                result = {"status": "ok", "type": config.connection_type.value}

            finished_at = datetime.now(UTC)
            config.status = ConnectionStatus.ACTIVE
            return ToolCallResult(
                tool_name=config.name,
                success=True,
                response=result,
                started_at=started_at,
                finished_at=finished_at,
                latency_ms=int((finished_at - started_at).total_seconds() * 1000),
            )

        except Exception as exc:
            config.status = ConnectionStatus.ERROR
            return ToolCallResult(
                tool_name=config.name,
                success=False,
                error=f"Health check failed: {exc}",
                started_at=started_at,
                finished_at=datetime.now(UTC),
            )

    # ------------------------------------------------------------------ #
    #  接続タイプ別の実行メソッド
    # ------------------------------------------------------------------ #

    async def _execute_rest_api(
        self,
        config: ToolConnectionConfig,
        method: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """REST API を呼び出す."""
        import httpx

        url = self._build_url(config, payload.pop("path", ""))
        headers = self._build_auth_headers(config)
        headers.update(payload.pop("headers", {}))
        http_method = method.upper() if method else "GET"
        timeout = config.timeout_seconds

        async with httpx.AsyncClient(timeout=timeout) as client:
            if http_method == "GET":
                resp = await client.get(url, headers=headers, params=payload.get("params"))
            elif http_method == "POST":
                resp = await client.post(url, headers=headers, json=payload.get("body", payload))
            elif http_method == "PUT":
                resp = await client.put(url, headers=headers, json=payload.get("body", payload))
            elif http_method == "PATCH":
                resp = await client.patch(url, headers=headers, json=payload.get("body", payload))
            elif http_method == "DELETE":
                resp = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {http_method}")

            resp.raise_for_status()
            try:
                return {"status_code": resp.status_code, "body": resp.json()}
            except Exception:
                return {
                    "status_code": resp.status_code,
                    "body": resp.text,
                }

    async def _execute_graphql(
        self,
        config: ToolConnectionConfig,
        method: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """GraphQL エンドポイントにクエリを送信する."""
        import httpx

        url = self._build_url(config, payload.pop("path", ""))
        headers = self._build_auth_headers(config)
        headers["Content-Type"] = "application/json"

        graphql_body = {
            "query": payload.get("query", method),
            "variables": payload.get("variables", {}),
        }
        operation = payload.get("operation_name")
        if operation:
            graphql_body["operationName"] = operation

        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            resp = await client.post(url, headers=headers, json=graphql_body)
            resp.raise_for_status()
            return resp.json()

    async def _execute_cli(
        self,
        config: ToolConnectionConfig,
        method: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """CLI ツールをサブプロセスで実行する."""
        command_parts: list[str] = []

        # config.config にベースコマンドが含まれる場合
        base_cmd = (config.config or {}).get("command", "")
        if base_cmd:
            command_parts.append(base_cmd)

        # method をサブコマンドとして追加
        if method:
            command_parts.extend(method.split())

        # payload の args をコマンド引数として追加
        args = payload.get("args", [])
        if isinstance(args, list):
            command_parts.extend(str(a) for a in args)
        elif isinstance(args, str):
            command_parts.extend(args.split())

        if not command_parts:
            raise ValueError("No command specified for CLI execution")

        logger.info("Executing CLI: %s", " ".join(command_parts))

        proc = await asyncio.create_subprocess_exec(
            *command_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=payload.get("env"),
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=config.timeout_seconds
            )
        except TimeoutError:
            proc.kill()
            raise TimeoutError(f"CLI command timed out after {config.timeout_seconds}s")

        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }

    async def _execute_webhook(
        self,
        config: ToolConnectionConfig,
        method: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Webhook に POST を送信する."""
        import httpx

        url = config.base_url or ""
        if not url:
            raise ValueError("Webhook URL is not configured")

        headers = self._build_auth_headers(config)
        headers["Content-Type"] = "application/json"

        webhook_body = {
            "event": method,
            "payload": payload,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            resp = await client.post(url, headers=headers, json=webhook_body)
            resp.raise_for_status()
            try:
                return {"status_code": resp.status_code, "body": resp.json()}
            except Exception:
                return {
                    "status_code": resp.status_code,
                    "body": resp.text,
                }

    async def _execute_mcp(
        self,
        config: ToolConnectionConfig,
        method: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """MCP サーバーにツール呼び出しを委譲する."""
        from app.integrations.mcp_server import mcp_server

        result = await mcp_server.handle_call_tool(method, payload)
        return result

    async def _execute_websocket(
        self,
        config: ToolConnectionConfig,
        method: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """WebSocket で単一メッセージを送受信する."""
        url = config.base_url or ""
        if not url:
            raise ValueError("WebSocket URL is not configured")

        # httpx は WebSocket を直接サポートしないため、
        # 送信データの構造のみ返す（実際の WS 接続は専用クライアントで行う）
        return {
            "status": "delegated",
            "message": (
                "WebSocket connections should use the dedicated WS handler. "
                f"Target: {url}, method: {method}"
            ),
        }

    async def _execute_file_system(
        self,
        config: ToolConnectionConfig,
        method: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """ファイルシステム操作を実行する（サンドボックス経由）."""
        from app.security.sandbox import sandbox_guard

        path = payload.get("path", "")
        check = sandbox_guard.check_path(path)
        if not check.allowed:
            raise PermissionError(f"Sandbox denied access: {check.reason}")

        return {
            "status": "ok",
            "method": method,
            "path": path,
            "message": "File system operation delegated to sandbox-aware handler",
        }

    async def _execute_database(
        self,
        config: ToolConnectionConfig,
        method: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """データベース操作のプレースホルダ."""
        return {
            "status": "delegated",
            "method": method,
            "message": "Database operations should use the repository layer",
        }

    async def _execute_grpc(
        self,
        config: ToolConnectionConfig,
        method: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """gRPC 呼び出しのプレースホルダ."""
        return {
            "status": "delegated",
            "method": method,
            "target": config.base_url,
            "message": "gRPC calls require grpcio. Configure the service stub.",
        }

    async def _execute_oauth(
        self,
        config: ToolConnectionConfig,
        method: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """OAuth 保護リソースへのアクセス."""
        import httpx

        url = self._build_url(config, payload.pop("path", ""))
        headers = self._build_auth_headers(config)

        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            resp = await client.request(
                method.upper() or "GET",
                url,
                headers=headers,
                json=payload.get("body") if method.upper() != "GET" else None,
                params=payload.get("params") if method.upper() == "GET" else None,
            )
            resp.raise_for_status()
            try:
                return {"status_code": resp.status_code, "body": resp.json()}
            except Exception:
                return {"status_code": resp.status_code, "body": resp.text}

    # ------------------------------------------------------------------ #
    #  ヘルスチェック内部メソッド
    # ------------------------------------------------------------------ #

    async def _http_health_check(self, config: ToolConnectionConfig) -> dict[str, Any]:
        """HTTP ベースの接続ヘルスチェック."""
        import httpx

        url = config.base_url or ""
        if not url:
            return {"status": "no_url", "healthy": False}

        headers = self._build_auth_headers(config)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
            return {
                "status": "ok" if resp.is_success else "error",
                "status_code": resp.status_code,
                "healthy": resp.is_success,
            }

    async def _cli_health_check(self, config: ToolConnectionConfig) -> dict[str, Any]:
        """CLI ツールの存在確認."""
        base_cmd = (config.config or {}).get("command", "")
        if not base_cmd:
            return {"status": "no_command", "healthy": False}

        proc = await asyncio.create_subprocess_exec(
            "which",
            base_cmd.split()[0],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        found = proc.returncode == 0
        return {
            "status": "ok" if found else "not_found",
            "command": base_cmd,
            "path": stdout.decode().strip() if found else "",
            "healthy": found,
        }

    # ------------------------------------------------------------------ #
    #  ユーティリティ
    # ------------------------------------------------------------------ #

    def _build_url(self, config: ToolConnectionConfig, path: str = "") -> str:
        """ベース URL とパスを結合する."""
        base = (config.base_url or "").rstrip("/")
        if path:
            return f"{base}/{path.lstrip('/')}"
        return base

    def _build_auth_headers(self, config: ToolConnectionConfig) -> dict[str, str]:
        """認証タイプに基づいてヘッダーを構築する."""
        headers: dict[str, str] = {}
        creds = config.credentials

        if config.auth_type == AuthType.BEARER_TOKEN:
            token = creds.get("token", "")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif config.auth_type == AuthType.API_KEY:
            key = creds.get("api_key", "")
            header_name = creds.get("header_name", "X-API-Key")
            if key:
                headers[header_name] = key
        elif config.auth_type == AuthType.BASIC:
            import base64

            username = creds.get("username", "")
            password = creds.get("password", "")
            encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        elif config.auth_type == AuthType.OAUTH2:
            token = creds.get("access_token", "")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif config.auth_type == AuthType.SERVICE_ACCOUNT:
            token = creds.get("token", "")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        return headers


# Global instance
tool_connector = ToolConnector()
