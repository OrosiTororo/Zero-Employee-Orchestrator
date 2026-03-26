"""MCP Server — Model Context Protocol server implementation.

Uses MCP (Model Context Protocol) to allow external AI agents and tools
to invoke Zero-Employee Orchestrator functionality.

Exposes tools, resources, and prompts based on the MCP specification.
"""

from __future__ import annotations

import logging
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
    """MCP exposed tool."""

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
    """MCP exposed resource."""

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
    """MCP exposed prompt template."""

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
    """Zero-Employee Orchestrator MCP server.

    Exposes the following capabilities to external AI agents:
      - Ticket management (create, list, update status)
      - Task management (execute, monitor)
      - Skill management (list, execute)
      - Knowledge search (Experience Memory, RAG)
      - Audit log viewing
      - Agent state monitoring
    """

    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}
        self._resources: dict[str, MCPResource] = {}
        self._prompts: dict[str, MCPPrompt] = {}
        self._register_builtin_tools()
        self._register_builtin_resources()
        self._register_builtin_prompts()

    def _register_builtin_tools(self) -> None:
        """Register built-in tools."""
        tools = [
            MCPTool(
                name="create_ticket",
                description="Create a new business ticket",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Ticket title",
                        },
                        "description": {"type": "string", "description": "Detailed description"},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                        },
                    },
                    "required": ["title"],
                },
            ),
            MCPTool(
                name="list_tickets",
                description="Retrieve ticket list",
                input_schema={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Status filter",
                        },
                        "limit": {"type": "integer", "default": 20},
                    },
                },
            ),
            MCPTool(
                name="get_agent_status",
                description="Get the current status of an agent",
                input_schema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string", "description": "Agent ID"},
                    },
                    "required": ["agent_id"],
                },
            ),
            MCPTool(
                name="search_knowledge",
                description="Search the knowledge base",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "category": {
                            "type": "string",
                            "description": "Category filter",
                        },
                    },
                    "required": ["query"],
                },
            ),
            MCPTool(
                name="execute_skill",
                description="Execute a registered skill",
                input_schema={
                    "type": "object",
                    "properties": {
                        "skill_slug": {"type": "string", "description": "Skill slug"},
                        "inputs": {"type": "object", "description": "Input parameters"},
                    },
                    "required": ["skill_slug"],
                },
            ),
            MCPTool(
                name="get_audit_logs",
                description="Retrieve audit logs",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 50},
                        "action_type": {
                            "type": "string",
                            "description": "Action type",
                        },
                    },
                },
            ),
            MCPTool(
                name="monitor_executions",
                description="Monitor running tasks",
                input_schema={
                    "type": "object",
                    "properties": {},
                },
            ),
            MCPTool(
                name="propose_hypothesis",
                description="Propose a hypothesis and start parallel verification",
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
        """Register built-in resources."""
        resources = [
            MCPResource(
                uri="zero-employee://dashboard",
                name="Dashboard",
                description="System-wide dashboard data",
            ),
            MCPResource(
                uri="zero-employee://agents",
                name="Agent List",
                description="List and status of registered agents",
            ),
            MCPResource(
                uri="zero-employee://skills",
                name="Skill List",
                description="List of available skills",
            ),
            MCPResource(
                uri="zero-employee://knowledge",
                name="Knowledge Store",
                description="List of persisted knowledge entries",
            ),
        ]
        for r in resources:
            self._resources[r.uri] = r

    def _register_builtin_prompts(self) -> None:
        """Register built-in prompt templates."""
        prompts = [
            MCPPrompt(
                name="task_planning",
                description="Prompt for task planning",
                arguments=[
                    {"name": "objective", "description": "Goal to achieve", "required": True},
                    {
                        "name": "constraints",
                        "description": "Constraints",
                        "required": False,
                    },
                ],
            ),
            MCPPrompt(
                name="code_review",
                description="Prompt for code review",
                arguments=[
                    {
                        "name": "code",
                        "description": "Code to review",
                        "required": True,
                    },
                    {
                        "name": "language",
                        "description": "Programming language",
                        "required": False,
                    },
                ],
            ),
        ]
        for p in prompts:
            self._prompts[p.name] = p

    def register_tool(self, tool: MCPTool) -> None:
        """Register a custom tool."""
        self._tools[tool.name] = tool
        logger.info("MCP tool registered: %s", tool.name)

    def register_resource(self, resource: MCPResource) -> None:
        self._resources[resource.uri] = resource

    def register_prompt(self, prompt: MCPPrompt) -> None:
        self._prompts[prompt.name] = prompt

    # --- MCP Protocol Handlers ---

    async def handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """MCP initialize handler."""
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
        return {"content": [{"type": "text", "text": f"Tool '{name}' called with: {arguments}"}]}

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
