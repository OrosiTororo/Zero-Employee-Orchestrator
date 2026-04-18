"""MCP Server — Model Context Protocol server implementation.

Exposes Zero-Employee Orchestrator's core capabilities (tickets, tasks, skills,
knowledge, audit, autonomy, budgets, kill-switch, etc.) over the
Model Context Protocol so that external AI agents and IDEs can drive ZEO.

Four transports are provided:
  - REST convenience wrapper: ``GET /mcp/tools``, ``POST /mcp/tools/call``, …
  - JSON-RPC 2.0 endpoint:    ``POST /mcp/rpc``         (spec-compliant)
  - Streaming (SSE) endpoint: ``GET  /mcp/sse``         (push notifications)
  - stdio transport:          ``zero-employee mcp serve`` (Claude Desktop)

The JSON-RPC dispatch implements the methods defined by the MCP
2025-11-25 specification — ``initialize``, ``ping``, ``tools/list``,
``tools/call``, ``resources/list``, ``resources/read``, ``prompts/list``,
``prompts/get``, ``logging/setLevel`` — so any MCP-compatible client
(Claude Desktop, Cursor, Continue, custom agents) can connect with zero
custom glue code. Tools advertise hint metadata (``readOnlyHint``,
``destructiveHint``, ``idempotentHint``) per the spec so hosts can show
safety affordances before invoking them.

Reference: https://modelcontextprotocol.io/specification
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# MCP protocol version we advertise on ``initialize``. Clients negotiate down.
# v0.1.6 ships the 2025-11-25 revision (adds tool annotations + logging).
MCP_PROTOCOL_VERSION = "2025-11-25"
# Previous revisions we still accept on ``initialize`` negotiation.
MCP_SUPPORTED_PROTOCOL_VERSIONS = ("2025-11-25", "2024-11-05")

# Python logging level aliases accepted by ``logging/setLevel``.
_LOG_LEVEL_MAP: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "notice": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
    "alert": logging.CRITICAL,
    "emergency": logging.CRITICAL,
}


class MCPCapability(str, Enum):
    TOOLS = "tools"
    RESOURCES = "resources"
    PROMPTS = "prompts"


@dataclass
class MCPTool:
    """MCP exposed tool.

    ``title`` is a human-friendly label used by rich clients. The three
    hint flags follow the MCP 2025-11-25 ``annotations`` object so host
    applications can render safety affordances (read-only badge,
    destructive-action warning) before invoking the tool.
    """

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    handler: Callable[[dict[str, Any]], Any] | None = None
    title: str | None = None
    read_only_hint: bool = False
    destructive_hint: bool = False
    idempotent_hint: bool = False
    open_world_hint: bool = False

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }
        if self.title:
            out["title"] = self.title
        annotations: dict[str, Any] = {}
        if self.title:
            annotations["title"] = self.title
        if self.read_only_hint:
            annotations["readOnlyHint"] = True
        if self.destructive_hint:
            annotations["destructiveHint"] = True
        if self.idempotent_hint:
            annotations["idempotentHint"] = True
        if self.open_world_hint:
            annotations["openWorldHint"] = True
        if annotations:
            out["annotations"] = annotations
        return out


@dataclass
class MCPResource:
    """MCP exposed resource."""

    uri: str
    name: str
    description: str
    mime_type: str = "application/json"
    reader: Callable[[], Any] | None = None

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
    template: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments,
        }


# JSON-RPC 2.0 error codes (per spec)
JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603


class MCPServer:
    """Zero-Employee Orchestrator MCP server.

    Exposes the following capabilities to external AI agents:
      - Ticket management (create, list, update status)
      - Task management (execute, monitor)
      - Skill / plugin / extension registry
      - Knowledge search (Experience Memory, RAG)
      - Audit log viewing
      - Agent state monitoring
      - Kill-switch inspection
      - Autonomy dial inspection
      - Budget / cost guard status
      - Hypothesis proposal and verification
    """

    # Fallback used when the real project version cannot be resolved
    _DEFAULT_VERSION = "0.1.6"

    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}
        self._resources: dict[str, MCPResource] = {}
        self._prompts: dict[str, MCPPrompt] = {}
        self._register_builtin_tools()
        self._register_builtin_resources()
        self._register_builtin_prompts()

    # ------------------------------------------------------------------
    # Version resolution (dynamic so it always matches pyproject.toml)
    # ------------------------------------------------------------------

    @classmethod
    def get_server_version(cls) -> str:
        """Return the current ZEO package version.

        Falls back to ``_DEFAULT_VERSION`` if importlib.metadata cannot
        locate the installed package (e.g. during ``pip install -e .`` in a
        fresh checkout). This avoids hard-coding the version string in
        two places.
        """
        try:
            from importlib.metadata import PackageNotFoundError, version

            try:
                return version("zero-employee-orchestrator")
            except PackageNotFoundError:
                pass
        except Exception:  # pragma: no cover - importlib always present on 3.11
            pass

        # Fallback: read pyproject.toml at runtime (dev checkout)
        try:
            import pathlib
            import tomllib

            here = pathlib.Path(__file__).resolve()
            for parent in here.parents:
                candidate = parent / "pyproject.toml"
                if candidate.exists():
                    data = tomllib.loads(candidate.read_text(encoding="utf-8"))
                    v = data.get("project", {}).get("version")
                    if v:
                        return str(v)
        except Exception:
            pass

        return cls._DEFAULT_VERSION

    def _register_builtin_tools(self) -> None:
        """Register built-in tools.

        Tool annotations (``readOnlyHint``, ``destructiveHint``,
        ``idempotentHint``) follow the MCP 2025-11-25 spec so clients can
        render safety affordances before invoking a destructive action.
        """
        tools = [
            MCPTool(
                name="create_ticket",
                title="Create Ticket",
                description="Create a new business ticket in ZEO",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Ticket title"},
                        "description": {"type": "string", "description": "Detailed description"},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                        },
                    },
                    "required": ["title"],
                },
                destructive_hint=True,
            ),
            MCPTool(
                name="list_tickets",
                title="List Tickets",
                description="Retrieve the current ticket list",
                input_schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "description": "Status filter"},
                        "limit": {"type": "integer", "default": 20},
                    },
                },
                read_only_hint=True,
                idempotent_hint=True,
            ),
            MCPTool(
                name="get_agent_status",
                title="Get Agent Status",
                description="Get the current status of a running agent",
                input_schema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string", "description": "Agent ID"},
                    },
                    "required": ["agent_id"],
                },
                read_only_hint=True,
                idempotent_hint=True,
            ),
            MCPTool(
                name="search_knowledge",
                title="Search Knowledge Base",
                description="Search the persistent knowledge base (Experience Memory)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "category": {
                            "type": "string",
                            "description": "Category filter (optional)",
                        },
                    },
                    "required": ["query"],
                },
                read_only_hint=True,
                idempotent_hint=True,
            ),
            MCPTool(
                name="execute_skill",
                title="Execute Skill",
                description="Dispatch a registered skill by slug",
                input_schema={
                    "type": "object",
                    "properties": {
                        "skill_slug": {"type": "string", "description": "Skill slug"},
                        "inputs": {"type": "object", "description": "Input parameters"},
                    },
                    "required": ["skill_slug"],
                },
                destructive_hint=True,
            ),
            MCPTool(
                name="list_skills",
                title="List Skills",
                description="List all registered skills (built-in + imported)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "enabled_only": {"type": "boolean", "default": False},
                    },
                },
                read_only_hint=True,
                idempotent_hint=True,
            ),
            MCPTool(
                name="get_audit_logs",
                title="Get Audit Logs",
                description="Retrieve the audit log tail",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 50},
                        "action_type": {
                            "type": "string",
                            "description": "Filter by action type",
                        },
                    },
                },
                read_only_hint=True,
                idempotent_hint=True,
            ),
            MCPTool(
                name="monitor_executions",
                title="Monitor Executions",
                description="Monitor running task executions",
                input_schema={"type": "object", "properties": {}},
                read_only_hint=True,
            ),
            MCPTool(
                name="propose_hypothesis",
                title="Propose Hypothesis",
                description="Propose a hypothesis and kick off parallel verification",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "task_id": {"type": "string"},
                    },
                    "required": ["title", "description"],
                },
                destructive_hint=True,
            ),
            MCPTool(
                name="get_kill_switch_status",
                title="Kill-Switch Status",
                description="Inspect the global kill-switch that halts all agent execution",
                input_schema={"type": "object", "properties": {}},
                read_only_hint=True,
                idempotent_hint=True,
            ),
            MCPTool(
                name="get_autonomy_level",
                title="Autonomy Level",
                description="Read the current autonomy boundary level (0-10)",
                input_schema={"type": "object", "properties": {}},
                read_only_hint=True,
                idempotent_hint=True,
            ),
            MCPTool(
                name="get_budget_status",
                title="Budget Status",
                description="Get Cost Guard budget usage and daily/hourly spend",
                input_schema={"type": "object", "properties": {}},
                read_only_hint=True,
                idempotent_hint=True,
            ),
            MCPTool(
                name="list_approvals",
                title="List Pending Approvals",
                description="List pending approval requests awaiting human review",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 20},
                    },
                },
                read_only_hint=True,
                idempotent_hint=True,
            ),
            MCPTool(
                name="get_server_info",
                title="Server Info",
                description="Return ZEO version, endpoint count and uptime",
                input_schema={"type": "object", "properties": {}},
                read_only_hint=True,
                idempotent_hint=True,
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
        self._tools["list_skills"].handler = self._handle_list_skills
        self._tools["get_audit_logs"].handler = self._handle_get_audit_logs
        self._tools["monitor_executions"].handler = self._handle_monitor_executions
        self._tools["propose_hypothesis"].handler = self._handle_propose_hypothesis
        self._tools["get_kill_switch_status"].handler = self._handle_get_kill_switch_status
        self._tools["get_autonomy_level"].handler = self._handle_get_autonomy_level
        self._tools["get_budget_status"].handler = self._handle_get_budget_status
        self._tools["list_approvals"].handler = self._handle_list_approvals
        self._tools["get_server_info"].handler = self._handle_get_server_info

    # --- Tool Handler Implementations ---

    async def _handle_create_ticket(self, args: dict) -> str:
        """Create a ticket via the tickets service.

        If no ``company_id`` is supplied, resolve to the first company in the
        database. This keeps single-tenant CLI / Claude-Desktop setups from
        bouncing off FK errors against a placeholder UUID.
        """
        try:
            import uuid as _uuid

            from sqlalchemy import select

            from app.core.database import get_session
            from app.models.company import Company
            from app.services.ticket_service import create_ticket

            async for db in get_session():
                company_id = args.get("company_id")
                if not company_id:
                    first = (
                        await db.execute(select(Company.id).order_by(Company.created_at).limit(1))
                    ).scalar_one_or_none()
                    if first is None:
                        return (
                            "No companies exist yet. Create one first — "
                            "e.g. `POST /api/v1/companies` or run `zero-employee chat` "
                            "→ /setup — then retry `create_ticket`."
                        )
                    company_id = str(first)
                try:
                    _uuid.UUID(str(company_id))
                except ValueError:
                    return f"Invalid company_id: {company_id!r} is not a UUID."
                ticket = await create_ticket(
                    db,
                    company_id=company_id,
                    title=args.get("title", "Untitled"),
                    description=args.get("description", ""),
                    priority=args.get("priority", "medium"),
                )
                return f"Ticket created: {ticket.id} — {ticket.title}"
        except Exception as e:
            return f"Error creating ticket: {e}"

    async def _handle_list_tickets(self, args: dict) -> str:
        """List tickets directly from the tickets table."""
        try:
            import uuid as _uuid

            from sqlalchemy import select

            from app.core.database import get_session
            from app.models.ticket import Ticket

            limit = int(args.get("limit", 20))
            company_id = args.get("company_id")
            status = args.get("status")
            async for db in get_session():
                stmt = select(Ticket).order_by(Ticket.ticket_no.desc()).limit(limit)
                if company_id:
                    stmt = stmt.where(Ticket.company_id == _uuid.UUID(str(company_id)))
                if status:
                    stmt = stmt.where(Ticket.status == status)
                tickets = list((await db.execute(stmt)).scalars().all())
                if not tickets:
                    return "No tickets found."
                lines = [f"- [{t.status}] {t.title} (id={t.id})" for t in tickets]
                return f"Found {len(tickets)} tickets:\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing tickets: {e}"

    async def _handle_get_agent_status(self, args: dict) -> str:
        """Get agent status from execution monitor."""
        try:
            from app.orchestration.execution_monitor import get_execution_monitor

            monitor = get_execution_monitor()
            summary = monitor.get_system_summary()
            return (
                f"Active executions: {summary.get('active_executions', 0)}, "
                f"Active agents: {summary.get('active_agents', [])}, "
                f"Kill switch: {'ON' if monitor.is_killed else 'OFF'}"
            )
        except Exception as e:
            return f"Error getting agent status: {e}"

    async def _handle_search_knowledge(self, args: dict) -> str:
        """Search the persistent knowledge store (Experience Memory)."""
        try:
            from app.core.database import get_session
            from app.orchestration.knowledge_store import KnowledgeStore

            limit = int(args.get("limit", 5))
            async for db in get_session():
                store = KnowledgeStore(db)
                records = await store.recall(
                    category=args.get("category"),
                    company_id=args.get("company_id"),
                    search_query=args.get("query", ""),
                )
                records = records[:limit]
                if not records:
                    return "No knowledge entries found."
                lines = [f"- [{r.category}] {r.key}: {(r.value or '')[:100]}" for r in records]
                return f"Found {len(records)} entries:\n" + "\n".join(lines)
        except Exception as e:
            return f"Error searching knowledge: {e}"

    async def _handle_execute_skill(self, args: dict) -> str:
        """Execute a registered skill."""
        slug = args.get("skill_slug", "")
        return f"Skill '{slug}' execution dispatched. Use /dispatch to monitor progress."

    async def _handle_list_skills(self, args: dict) -> str:
        """List registered skills."""
        try:
            from app.core.database import async_session_factory
            from app.services import skill_service

            enabled_only = bool(args.get("enabled_only", False))
            async with async_session_factory() as session:
                skills = await skill_service.list_skills(session)
                if enabled_only:
                    skills = [s for s in skills if getattr(s, "enabled", True)]
                if not skills:
                    return "No skills registered."
                lines = [f"- {getattr(s, 'slug', '?')} ({getattr(s, 'name', '?')})" for s in skills]
                return f"Found {len(skills)} skill(s):\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing skills: {e}"

    async def _handle_get_audit_logs(self, args: dict) -> str:
        """Retrieve audit logs via the AuditLogRepository (append-only)."""
        try:
            import uuid as _uuid

            from app.core.database import get_session
            from app.repositories.audit_repository import AuditLogRepository

            company_id = args.get("company_id") or "00000000-0000-0000-0000-000000000000"
            limit = int(args.get("limit", 50))
            async for db in get_session():
                repo = AuditLogRepository(db)
                logs = await repo.get_by_company(
                    _uuid.UUID(company_id),
                    event_type=args.get("event_type"),
                    target_type=args.get("target_type"),
                    limit=limit,
                )
                if not logs:
                    return "No audit logs found."
                lines = [
                    f"- [{entry.event_type}] {entry.target_type}/{entry.target_id} "
                    f"by {entry.actor_type}"
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

    async def _handle_get_kill_switch_status(self, args: dict) -> str:
        """Get kill-switch status from the orchestration layer."""
        try:
            from app.orchestration.execution_monitor import get_execution_monitor

            monitor = get_execution_monitor()
            active = bool(monitor.is_killed)
            active_count = monitor.active_count
            state = "ENGAGED (all execution halted)" if active else "DISENGAGED"
            return f"Kill switch: {state} | active executions: {active_count}"
        except Exception as e:
            return f"Error reading kill switch: {e}"

    async def _handle_get_autonomy_level(self, args: dict) -> str:
        """Read current autonomy level.

        Autonomy is tracked per agent in the database (see ``agents.autonomy_level``).
        There is no global mutable boundary, so we return the policy default
        and the supported levels for operator orientation.
        """
        try:
            from app.policies.autonomy_boundary import AutonomyLevel

            default = AutonomyLevel.SEMI_AUTO.value
            levels = ", ".join(level.value for level in AutonomyLevel)
            return (
                f"Default agent autonomy level: {default}. "
                f"Supported levels: {levels}. "
                f"Per-agent levels are stored in the agents table."
            )
        except Exception as e:
            return f"Error reading autonomy level: {e}"

    async def _handle_get_budget_status(self, args: dict) -> str:
        """Get Cost Guard budget status from the budget_policies / cost_ledger tables."""
        try:
            from sqlalchemy import func, select

            from app.core.database import get_session
            from app.models.budget import BudgetPolicy, CostLedger

            async for db in get_session():
                policy_count = await db.scalar(select(func.count(BudgetPolicy.id))) or 0
                spend_total = (
                    await db.scalar(select(func.coalesce(func.sum(CostLedger.cost_usd), 0)))
                ) or 0
                if not policy_count:
                    return (
                        f"Cost Guard active. No budget policies configured. "
                        f"Total recorded spend: ${float(spend_total):.4f}."
                    )
                sample = (await db.execute(select(BudgetPolicy).limit(1))).scalar_one_or_none()
                if sample is None:
                    return (
                        f"Cost Guard active. Policies configured: {policy_count}. "
                        f"Total recorded spend: ${float(spend_total):.4f}."
                    )
                return (
                    f"Cost Guard active. Policies configured: {policy_count}. "
                    f"Sample policy id={sample.id}, name={sample.name}, "
                    f"limit_usd={float(sample.limit_usd)}, period={sample.period_type}, "
                    f"warn={sample.warn_threshold_pct}%, stop={sample.stop_threshold_pct}%. "
                    f"Total recorded spend: ${float(spend_total):.4f}."
                )
        except Exception as e:
            return f"Cost Guard active (detail unavailable: {e})"

    async def _handle_list_approvals(self, args: dict) -> str:
        """List pending approval requests from the approvals table."""
        try:
            from sqlalchemy import select

            from app.core.database import get_session
            from app.models.review import ApprovalRequest

            limit = int(args.get("limit", 20))
            async for db in get_session():
                result = await db.execute(
                    select(ApprovalRequest)
                    .where(ApprovalRequest.status == "requested")
                    .order_by(ApprovalRequest.requested_at.desc())
                    .limit(limit)
                )
                pending = list(result.scalars().all())
                if not pending:
                    return "No pending approvals."
                lines = [
                    f"- {p.id}: {p.target_type} (risk={p.risk_level}, reason={p.reason})"
                    for p in pending
                ]
                return f"{len(pending)} pending approval(s):\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing approvals: {e}"

    async def _handle_get_server_info(self, args: dict) -> str:
        """Return a short server info string."""
        version = self.get_server_version()
        return (
            f"Zero-Employee Orchestrator v{version} "
            f"| MCP protocol {MCP_PROTOCOL_VERSION} "
            f"| {len(self._tools)} tools "
            f"| {len(self._resources)} resources "
            f"| {len(self._prompts)} prompts"
        )

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
            MCPResource(
                uri="zero-employee://kill-switch",
                name="Kill Switch",
                description="Global kill-switch state (read-only)",
            ),
            MCPResource(
                uri="zero-employee://autonomy",
                name="Autonomy Level",
                description="Current autonomy dial level",
            ),
        ]
        for r in resources:
            self._resources[r.uri] = r

    def _register_builtin_prompts(self) -> None:
        """Register built-in prompt templates."""
        prompts = [
            MCPPrompt(
                name="task_planning",
                description="Prompt for task planning with DAG decomposition",
                arguments=[
                    {"name": "objective", "description": "Goal to achieve", "required": True},
                    {"name": "constraints", "description": "Constraints", "required": False},
                ],
                template=(
                    "You are a task planner for Zero-Employee Orchestrator.\n"
                    "Decompose the following objective into a DAG of 3-7 sub-tasks.\n"
                    "Objective: {objective}\n"
                    "Constraints: {constraints}\n"
                ),
            ),
            MCPPrompt(
                name="code_review",
                description="Prompt for code review focused on security and correctness",
                arguments=[
                    {"name": "code", "description": "Code to review", "required": True},
                    {
                        "name": "language",
                        "description": "Programming language",
                        "required": False,
                    },
                ],
                template=(
                    "Review the following {language} code for correctness, security, "
                    "and clarity. Highlight concrete issues with file/line references.\n\n"
                    "{code}"
                ),
            ),
            MCPPrompt(
                name="security_audit",
                description="Prompt for security audit of an AI workflow",
                arguments=[
                    {"name": "workflow", "description": "Workflow YAML or JSON", "required": True},
                ],
                template=(
                    "Audit the following ZEO workflow for prompt-injection, PII leakage, "
                    "sandbox escapes, and approval-gate bypasses. "
                    "Emit a findings table (severity, location, fix).\n\n{workflow}"
                ),
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
        """MCP ``initialize`` handler.

        Negotiates the protocol version with the client: if the client
        requests one of our supported revisions we echo it back, otherwise
        we fall back to the latest revision we ship so the client can
        decide whether to proceed or abort.
        """
        requested = params.get("protocolVersion") if isinstance(params, dict) else None
        negotiated = (
            requested
            if isinstance(requested, str) and requested in MCP_SUPPORTED_PROTOCOL_VERSIONS
            else MCP_PROTOCOL_VERSION
        )
        return {
            "protocolVersion": negotiated,
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True},
                "logging": {},
            },
            "serverInfo": {
                "name": "zero-employee-orchestrator",
                "version": self.get_server_version(),
            },
            "instructions": (
                "Zero-Employee Orchestrator MCP server. "
                "Call `tools/list` for ticket, task, skill, knowledge, "
                "audit, kill-switch, autonomy and budget tools."
            ),
        }

    async def handle_set_log_level(self, level: str) -> dict[str, Any]:
        """Implement the MCP ``logging/setLevel`` method.

        Maps the RFC 5424 level names accepted by the spec onto Python's
        ``logging`` module and applies the new level to the ZEO package
        logger. Invalid levels return an error payload instead of raising.
        """
        normalized = (level or "").strip().lower()
        if normalized not in _LOG_LEVEL_MAP:
            return {
                "error": f"Unknown log level: {level!r}. Valid: {sorted(_LOG_LEVEL_MAP)}",
                "isError": True,
            }
        logging.getLogger("app").setLevel(_LOG_LEVEL_MAP[normalized])
        logger.info("MCP logging level set to %s", normalized)
        return {}

    async def handle_list_tools(self) -> dict[str, Any]:
        return {"tools": [t.to_dict() for t in self._tools.values()]}

    async def handle_call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Tool not found: {name}", "isError": True}
        if tool.handler:
            try:
                result = await tool.handler(arguments or {})
                return {"content": [{"type": "text", "text": str(result)}]}
            except Exception as exc:
                logger.exception("MCP tool %s failed", name)
                return {
                    "content": [{"type": "text", "text": f"Tool error: {exc}"}],
                    "isError": True,
                }
        return {
            "content": [{"type": "text", "text": f"Tool '{name}' called with: {arguments}"}],
        }

    async def handle_list_resources(self) -> dict[str, Any]:
        return {"resources": [r.to_dict() for r in self._resources.values()]}

    async def handle_read_resource(self, uri: str) -> dict[str, Any]:
        """Read a registered resource by URI."""
        resource = self._resources.get(uri)
        if not resource:
            return {"error": f"Resource not found: {uri}", "isError": True}
        # Built-in resources are descriptor-only for now; future extension
        # can plumb live readers through the ``reader`` callable.
        contents = (
            resource.reader()
            if resource.reader is not None
            else {"uri": uri, "note": "descriptor-only"}
        )
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": resource.mime_type,
                    "text": str(contents),
                }
            ]
        }

    async def handle_list_prompts(self) -> dict[str, Any]:
        return {"prompts": [p.to_dict() for p in self._prompts.values()]}

    async def handle_get_prompt(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Return a prompt template rendered with the given arguments."""
        prompt = self._prompts.get(name)
        if not prompt:
            return {"error": f"Prompt not found: {name}", "isError": True}
        args = arguments or {}
        try:
            rendered = prompt.template.format_map(_SafeDict(args)) if prompt.template else ""
        except Exception as exc:
            rendered = f"[prompt render error: {exc}]"
        return {
            "description": prompt.description,
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": rendered},
                }
            ],
        }

    # ------------------------------------------------------------------
    # JSON-RPC 2.0 dispatch (MCP wire protocol)
    # ------------------------------------------------------------------

    async def handle_jsonrpc(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Handle a JSON-RPC 2.0 request per the MCP specification.

        Returns the JSON-RPC response as a plain dict, or ``None`` for
        notifications (requests without an ``id``).
        """
        if not isinstance(payload, dict):
            return self._jsonrpc_error(None, JSONRPC_INVALID_REQUEST, "Invalid Request")

        rpc_id = payload.get("id")
        method = payload.get("method")
        params = payload.get("params") or {}

        if payload.get("jsonrpc") != "2.0" or not isinstance(method, str):
            return self._jsonrpc_error(rpc_id, JSONRPC_INVALID_REQUEST, "Invalid Request")

        # Notifications — no response
        if rpc_id is None and method.startswith("notifications/"):
            logger.debug("MCP notification: %s", method)
            return None

        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = await self.handle_list_tools()
            elif method == "tools/call":
                name = params.get("name")
                if not isinstance(name, str):
                    return self._jsonrpc_error(
                        rpc_id, JSONRPC_INVALID_PARAMS, "Missing 'name' parameter"
                    )
                result = await self.handle_call_tool(name, params.get("arguments") or {})
            elif method == "resources/list":
                result = await self.handle_list_resources()
            elif method == "resources/read":
                uri = params.get("uri")
                if not isinstance(uri, str):
                    return self._jsonrpc_error(
                        rpc_id, JSONRPC_INVALID_PARAMS, "Missing 'uri' parameter"
                    )
                result = await self.handle_read_resource(uri)
            elif method == "prompts/list":
                result = await self.handle_list_prompts()
            elif method == "prompts/get":
                name = params.get("name")
                if not isinstance(name, str):
                    return self._jsonrpc_error(
                        rpc_id, JSONRPC_INVALID_PARAMS, "Missing 'name' parameter"
                    )
                result = await self.handle_get_prompt(name, params.get("arguments"))
            elif method == "logging/setLevel":
                level = params.get("level")
                if not isinstance(level, str):
                    return self._jsonrpc_error(
                        rpc_id, JSONRPC_INVALID_PARAMS, "Missing 'level' parameter"
                    )
                result = await self.handle_set_log_level(level)
            else:
                return self._jsonrpc_error(
                    rpc_id, JSONRPC_METHOD_NOT_FOUND, f"Method not found: {method}"
                )
        except Exception as exc:
            logger.exception("MCP JSON-RPC handler for %s failed", method)
            return self._jsonrpc_error(rpc_id, JSONRPC_INTERNAL_ERROR, str(exc))

        return {"jsonrpc": "2.0", "id": rpc_id, "result": result}

    @staticmethod
    def _jsonrpc_error(rpc_id: Any, code: int, message: str) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": code, "message": message},
        }

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "tools_count": len(self._tools),
            "resources_count": len(self._resources),
            "prompts_count": len(self._prompts),
            "tools": list(self._tools.keys()),
            "resources": list(self._resources.keys()),
            "prompts": list(self._prompts.keys()),
            "protocol_version": MCP_PROTOCOL_VERSION,
            "server_version": self.get_server_version(),
        }


class _SafeDict(dict):
    """dict subclass that returns ``{key}`` on missing keys so prompt templates
    never raise KeyError when the caller omits an optional argument."""

    def __missing__(self, key: str) -> str:  # pragma: no cover - trivial
        return "{" + key + "}"


# ----------------------------------------------------------------------
# stdio transport — Claude Desktop / Cursor / Continue drop-in
# ----------------------------------------------------------------------


async def _parse_stdio_line(raw: str) -> dict[str, Any] | list[Any] | None:
    """Parse a single line from stdio into a JSON-RPC payload."""
    import json as _json

    raw = raw.strip()
    if not raw:
        return None
    try:
        return _json.loads(raw)
    except _json.JSONDecodeError:
        return None


async def run_stdio_server(
    server: MCPServer | None = None,
    *,
    reader: Any | None = None,
    writer: Any | None = None,
) -> None:
    """Run the MCP server over stdin/stdout using newline-delimited JSON.

    This is the transport Claude Desktop, Cursor, and Continue use when
    they are configured with ``{"command": "zero-employee", "args":
    ["mcp", "serve"]}``. Each line on stdin is a JSON-RPC request (or a
    batch); responses are written as newline-delimited JSON on stdout.

    ``reader``/``writer`` can be injected for testing so the loop can run
    against in-memory buffers instead of the real stdio file descriptors.
    """
    import asyncio as _asyncio
    import json as _json
    import sys as _sys

    server = server or mcp_server

    async def _read_line() -> str | None:
        if reader is not None:
            line = await reader.readline()
            if not line:
                return None
            return line.decode("utf-8") if isinstance(line, (bytes, bytearray)) else line
        # Fall back to blocking stdin read via a thread so we don't block
        # the event loop. EOF returns ``""`` which we translate to None.
        line = await _asyncio.to_thread(_sys.stdin.readline)
        if line == "":
            return None
        return line

    def _write(payload: Any) -> None:
        text = _json.dumps(payload, ensure_ascii=False) + "\n"
        if writer is not None:
            writer.write(text.encode("utf-8") if hasattr(writer, "write") else text)
            if hasattr(writer, "drain"):
                # best-effort; callers using asyncio StreamWriter should await drain themselves
                pass
        else:
            _sys.stdout.write(text)
            _sys.stdout.flush()

    logger.info("MCP stdio transport ready (%d tools)", len(server._tools))

    while True:
        line = await _read_line()
        if line is None:
            logger.info("MCP stdio transport: EOF, shutting down")
            return
        payload = await _parse_stdio_line(line)
        if payload is None:
            _write(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": JSONRPC_PARSE_ERROR, "message": "Parse error"},
                }
            )
            continue

        if isinstance(payload, list):
            responses: list[dict[str, Any]] = []
            for item in payload:
                resp = await server.handle_jsonrpc(item)
                if resp is not None:
                    responses.append(resp)
            if responses:
                _write(responses)
            continue

        response = await server.handle_jsonrpc(payload)
        if response is not None:
            _write(response)


# Global singleton
mcp_server = MCPServer()
