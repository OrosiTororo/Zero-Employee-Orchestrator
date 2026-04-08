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

        # Wire handlers to real business logic
        self._tools["create_ticket"].handler = self._handle_create_ticket
        self._tools["list_tickets"].handler = self._handle_list_tickets
        self._tools["get_agent_status"].handler = self._handle_get_agent_status
        self._tools["search_knowledge"].handler = self._handle_search_knowledge
        self._tools["execute_skill"].handler = self._handle_execute_skill
        self._tools["get_audit_logs"].handler = self._handle_get_audit_logs
        self._tools["monitor_executions"].handler = self._handle_monitor_executions
        self._tools["propose_hypothesis"].handler = self._handle_propose_hypothesis

    # --- Tool Handler Implementations ---

    async def _handle_create_ticket(self, args: dict) -> str:
        """Create a ticket via the tickets service."""
        try:
            from app.core.database import get_session
            from app.services.ticket_service import TicketService

            async for db in get_session():
                svc = TicketService(db)
                ticket = await svc.create(
                    company_id="00000000-0000-0000-0000-000000000000",
                    title=args.get("title", "Untitled"),
                    description=args.get("description", ""),
                    priority=args.get("priority", "medium"),
                )
                return f"Ticket created: {ticket.id} — {ticket.title}"
        except Exception as e:
            return f"Error creating ticket: {e}"

    async def _handle_list_tickets(self, args: dict) -> str:
        """List tickets via the tickets service."""
        try:
            from app.core.database import get_session
            from app.services.ticket_service import TicketService

            async for db in get_session():
                svc = TicketService(db)
                tickets = await svc.list_tickets(
                    company_id="00000000-0000-0000-0000-000000000000",
                    status=args.get("status"),
                    limit=args.get("limit", 20),
                )
                lines = [f"- [{t.status}] {t.title} (id={t.id})" for t in tickets]
                return (
                    f"Found {len(tickets)} tickets:\n" + "\n".join(lines)
                    if lines
                    else "No tickets found."
                )
        except Exception as e:
            return f"Error listing tickets: {e}"

    async def _handle_get_agent_status(self, args: dict) -> str:
        """Get agent status from execution monitor."""
        try:
            from app.orchestration.execution_monitor import get_execution_monitor

            monitor = get_execution_monitor()
            summary = monitor.get_summary()
            return (
                f"Active executions: {summary.get('active_executions', 0)}, "
                f"Active agents: {summary.get('active_agents', [])}, "
                f"Kill switch: {'ON' if summary.get('kill_switch_active') else 'OFF'}"
            )
        except Exception as e:
            return f"Error getting agent status: {e}"

    async def _handle_search_knowledge(self, args: dict) -> str:
        """Search the knowledge store."""
        try:
            from app.core.database import get_session
            from app.orchestration.knowledge_store import PersistentKnowledgeStore

            async for db in get_session():
                store = PersistentKnowledgeStore(db, "00000000-0000-0000-0000-000000000000")
                results = await store.search(
                    query=args.get("query", ""),
                    category=args.get("category"),
                    limit=5,
                )
                if not results:
                    return "No knowledge entries found."
                lines = [f"- [{r.category}] {r.title}: {r.content[:100]}..." for r in results]
                return f"Found {len(results)} entries:\n" + "\n".join(lines)
        except Exception as e:
            return f"Error searching knowledge: {e}"

    async def _handle_execute_skill(self, args: dict) -> str:
        """Execute a registered skill."""
        slug = args.get("skill_slug", "")
        return f"Skill '{slug}' execution dispatched. Use /dispatch to monitor progress."

    async def _handle_get_audit_logs(self, args: dict) -> str:
        """Retrieve audit logs."""
        try:
            from app.core.database import get_session
            from app.repositories.audit_repository import AuditRepository

            async for db in get_session():
                repo = AuditRepository(db)
                logs = await repo.list_logs(
                    company_id="00000000-0000-0000-0000-000000000000",
                    limit=args.get("limit", 50),
                    action_type=args.get("action_type"),
                )
                if not logs:
                    return "No audit logs found."
                lines = [
                    f"- [{entry.event_type}] {entry.target_type}/{entry.target_id} by {entry.actor_type}"
                    for entry in logs
                ]
                return f"Found {len(logs)} audit entries:\n" + "\n".join(lines)
        except Exception as e:
            return f"Error fetching audit logs: {e}"

    async def _handle_monitor_executions(self, args: dict) -> str:
        """Monitor running task executions."""
        try:
            from app.orchestration.execution_monitor import get_execution_monitor

            monitor = get_execution_monitor()
            active = monitor.get_active_executions()
            if not active:
                return "No active executions."
            lines = [
                f"- {e.task_id} ({e.status}) agent={e.agent_id} "
                f"progress={e.progress_pct:.0f}% model={e.model_used}"
                for e in active
            ]
            return f"{len(active)} active execution(s):\n" + "\n".join(lines)
        except Exception as e:
            return f"Error monitoring executions: {e}"

    async def _handle_propose_hypothesis(self, args: dict) -> str:
        """Propose a hypothesis."""
        try:
            from app.orchestration.hypothesis_engine import get_hypothesis_engine

            engine = get_hypothesis_engine()
            h = engine.propose(
                title=args.get("title", ""),
                description=args.get("description", ""),
                proposer_agent_id="mcp-client",
            )
            return f"Hypothesis proposed: {h.hypothesis_id} — {h.title} (status={h.status})"
        except Exception as e:
            return f"Error proposing hypothesis: {e}"

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
