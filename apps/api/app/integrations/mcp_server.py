"""MCP Server — Model Context Protocol サーバー実装.

MCP (Model Context Protocol) を使って、外部のAIエージェントや
ツールからZero-Employee Orchestratorの機能を呼び出せるようにする。

MCP仕様に基づき、ツール・リソース・プロンプトを公開する。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MCPCapability(str, Enum):
    TOOLS = "tools"
    RESOURCES = "resources"
    PROMPTS = "prompts"


@dataclass
class MCPTool:
    """MCP公開ツール."""
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    handler: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


@dataclass
class MCPResource:
    """MCP公開リソース."""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"

    def to_dict(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }


@dataclass
class MCPPrompt:
    """MCP公開プロンプトテンプレート."""
    name: str
    description: str
    arguments: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments,
        }


class MCPServer:
    """Zero-Employee Orchestrator の MCP サーバー.

    外部AIエージェントに以下の機能を公開:
      - チケット管理（作成、一覧、状態更新）
      - タスク管理（実行、監視）
      - スキル管理（一覧、実行）
      - ナレッジ検索（Experience Memory、RAG）
      - 監査ログ閲覧
      - エージェント状態モニタリング
    """

    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}
        self._resources: dict[str, MCPResource] = {}
        self._prompts: dict[str, MCPPrompt] = {}
        self._register_builtin_tools()
        self._register_builtin_resources()
        self._register_builtin_prompts()

    def _register_builtin_tools(self) -> None:
        """組み込みツールを登録."""
        tools = [
            MCPTool(
                name="create_ticket",
                description="新しい業務チケットを作成する",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "チケットのタイトル"},
                        "description": {"type": "string", "description": "詳細説明"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    },
                    "required": ["title"],
                },
            ),
            MCPTool(
                name="list_tickets",
                description="チケット一覧を取得する",
                input_schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "description": "ステータスフィルター"},
                        "limit": {"type": "integer", "default": 20},
                    },
                },
            ),
            MCPTool(
                name="get_agent_status",
                description="エージェントの現在の状態を取得する",
                input_schema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string", "description": "エージェントID"},
                    },
                    "required": ["agent_id"],
                },
            ),
            MCPTool(
                name="search_knowledge",
                description="ナレッジベースを検索する",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "検索クエリ"},
                        "category": {"type": "string", "description": "カテゴリフィルター"},
                    },
                    "required": ["query"],
                },
            ),
            MCPTool(
                name="execute_skill",
                description="登録済みスキルを実行する",
                input_schema={
                    "type": "object",
                    "properties": {
                        "skill_slug": {"type": "string", "description": "スキルのslug"},
                        "inputs": {"type": "object", "description": "入力パラメータ"},
                    },
                    "required": ["skill_slug"],
                },
            ),
            MCPTool(
                name="get_audit_logs",
                description="監査ログを取得する",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 50},
                        "action_type": {"type": "string", "description": "アクションタイプ"},
                    },
                },
            ),
            MCPTool(
                name="monitor_executions",
                description="実行中のタスクを監視する",
                input_schema={
                    "type": "object",
                    "properties": {},
                },
            ),
            MCPTool(
                name="propose_hypothesis",
                description="仮説を提案して並行検証を開始する",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "task_id": {"type": "string"},
                    },
                    "required": ["title", "description"],
                },
            ),
        ]

        for tool in tools:
            self._tools[tool.name] = tool

    def _register_builtin_resources(self) -> None:
        """組み込みリソースを登録."""
        resources = [
            MCPResource(
                uri="zero-employee://dashboard",
                name="ダッシュボード",
                description="システム全体のダッシュボードデータ",
            ),
            MCPResource(
                uri="zero-employee://agents",
                name="エージェント一覧",
                description="登録済みエージェントの一覧と状態",
            ),
            MCPResource(
                uri="zero-employee://skills",
                name="スキル一覧",
                description="利用可能なスキルの一覧",
            ),
            MCPResource(
                uri="zero-employee://knowledge",
                name="ナレッジストア",
                description="永続化されたナレッジの一覧",
            ),
        ]
        for r in resources:
            self._resources[r.uri] = r

    def _register_builtin_prompts(self) -> None:
        """組み込みプロンプトテンプレートを登録."""
        prompts = [
            MCPPrompt(
                name="task_planning",
                description="タスク計画のためのプロンプト",
                arguments=[
                    {"name": "objective", "description": "達成目標", "required": True},
                    {"name": "constraints", "description": "制約条件", "required": False},
                ],
            ),
            MCPPrompt(
                name="code_review",
                description="コードレビューのためのプロンプト",
                arguments=[
                    {"name": "code", "description": "レビュー対象コード", "required": True},
                    {"name": "language", "description": "プログラミング言語", "required": False},
                ],
            ),
        ]
        for p in prompts:
            self._prompts[p.name] = p

    def register_tool(self, tool: MCPTool) -> None:
        """カスタムツールを登録."""
        self._tools[tool.name] = tool
        logger.info("MCP tool registered: %s", tool.name)

    def register_resource(self, resource: MCPResource) -> None:
        self._resources[resource.uri] = resource

    def register_prompt(self, prompt: MCPPrompt) -> None:
        self._prompts[prompt.name] = prompt

    # --- MCP Protocol Handlers ---

    async def handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """MCP initialize ハンドラ."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True},
            },
            "serverInfo": {
                "name": "zero-employee-orchestrator",
                "version": "0.1.0",
            },
        }

    async def handle_list_tools(self) -> dict[str, Any]:
        return {"tools": [t.to_dict() for t in self._tools.values()]}

    async def handle_call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Tool not found: {name}"}
        if tool.handler:
            try:
                result = await tool.handler(arguments)
                return {"content": [{"type": "text", "text": str(result)}]}
            except Exception as exc:
                return {"error": str(exc), "isError": True}
        return {
            "content": [{"type": "text", "text": f"Tool '{name}' called with: {arguments}"}]
        }

    async def handle_list_resources(self) -> dict[str, Any]:
        return {"resources": [r.to_dict() for r in self._resources.values()]}

    async def handle_list_prompts(self) -> dict[str, Any]:
        return {"prompts": [p.to_dict() for p in self._prompts.values()]}

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "tools_count": len(self._tools),
            "resources_count": len(self._resources),
            "prompts_count": len(self._prompts),
            "tools": list(self._tools.keys()),
            "resources": list(self._resources.keys()),
            "prompts": list(self._prompts.keys()),
        }


# Global singleton
mcp_server = MCPServer()
