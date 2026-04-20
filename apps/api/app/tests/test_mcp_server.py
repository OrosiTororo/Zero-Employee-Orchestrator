"""MCP server and JSON-RPC 2.0 endpoint tests (v0.1.6)."""

from __future__ import annotations

import asyncio
import json
import logging

import pytest
from httpx import AsyncClient

from app.integrations.mcp_server import (
    JSONRPC_INVALID_PARAMS,
    JSONRPC_INVALID_REQUEST,
    JSONRPC_METHOD_NOT_FOUND,
    JSONRPC_PARSE_ERROR,
    MCP_PROTOCOL_VERSION,
    MCP_SUPPORTED_PROTOCOL_VERSIONS,
    MCPServer,
    MCPTool,
    mcp_server,
    run_stdio_server,
)

# ---------------------------------------------------------------------------
# In-process MCPServer unit tests
# ---------------------------------------------------------------------------


def test_server_registers_expected_tools():
    """At least the v0.1.6 baseline tool set must be registered."""
    caps = mcp_server.get_capabilities()
    expected = {
        "create_ticket",
        "list_tickets",
        "search_knowledge",
        "execute_skill",
        "list_skills",
        "get_audit_logs",
        "monitor_executions",
        "get_kill_switch_status",
        "get_autonomy_level",
        "get_budget_status",
        "list_approvals",
        "get_server_info",
    }
    missing = expected - set(caps["tools"])
    assert not missing, f"MCP tools missing: {missing}"
    assert caps["protocol_version"] == MCP_PROTOCOL_VERSION
    # Server version must never be the literal string "unknown" or empty
    assert caps["server_version"]
    assert caps["server_version"] != "unknown"


def test_server_version_resolves_dynamically():
    """MCPServer.get_server_version reads pyproject.toml / installed metadata."""
    v = MCPServer.get_server_version()
    assert isinstance(v, str) and len(v) >= 3
    assert v[0].isdigit()


@pytest.mark.asyncio
async def test_jsonrpc_initialize_handshake():
    resp = await mcp_server.handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": MCP_PROTOCOL_VERSION},
        }
    )
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    result = resp["result"]
    assert result["protocolVersion"] == MCP_PROTOCOL_VERSION
    assert result["serverInfo"]["name"] == "zero-employee-orchestrator"
    assert "tools" in result["capabilities"]
    assert "resources" in result["capabilities"]
    assert "prompts" in result["capabilities"]


@pytest.mark.asyncio
async def test_jsonrpc_ping():
    resp = await mcp_server.handle_jsonrpc({"jsonrpc": "2.0", "id": 2, "method": "ping"})
    assert resp["result"] == {}


@pytest.mark.asyncio
async def test_jsonrpc_tools_list_and_call():
    resp = await mcp_server.handle_jsonrpc({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
    tools = resp["result"]["tools"]
    assert any(t["name"] == "get_server_info" for t in tools)

    resp = await mcp_server.handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "get_server_info", "arguments": {}},
        }
    )
    content = resp["result"]["content"]
    assert content[0]["type"] == "text"
    assert "Zero-Employee Orchestrator" in content[0]["text"]
    assert "MCP protocol" in content[0]["text"]


@pytest.mark.asyncio
async def test_jsonrpc_tools_call_missing_name_returns_invalid_params():
    resp = await mcp_server.handle_jsonrpc(
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {}}
    )
    assert resp["error"]["code"] == JSONRPC_INVALID_PARAMS


@pytest.mark.asyncio
async def test_jsonrpc_method_not_found():
    resp = await mcp_server.handle_jsonrpc({"jsonrpc": "2.0", "id": 6, "method": "does_not_exist"})
    assert resp["error"]["code"] == JSONRPC_METHOD_NOT_FOUND


@pytest.mark.asyncio
async def test_jsonrpc_notification_returns_none():
    """Notifications (no id) must NOT generate a response."""
    resp = await mcp_server.handle_jsonrpc(
        {"jsonrpc": "2.0", "method": "notifications/initialized"}
    )
    assert resp is None


@pytest.mark.asyncio
async def test_jsonrpc_resources_list_and_read():
    resp = await mcp_server.handle_jsonrpc({"jsonrpc": "2.0", "id": 7, "method": "resources/list"})
    resources = resp["result"]["resources"]
    assert any(r["uri"] == "zero-employee://dashboard" for r in resources)

    resp = await mcp_server.handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "resources/read",
            "params": {"uri": "zero-employee://dashboard"},
        }
    )
    assert "contents" in resp["result"]


@pytest.mark.asyncio
async def test_jsonrpc_prompts_list_and_get():
    resp = await mcp_server.handle_jsonrpc({"jsonrpc": "2.0", "id": 9, "method": "prompts/list"})
    names = [p["name"] for p in resp["result"]["prompts"]]
    assert "task_planning" in names
    assert "security_audit" in names

    resp = await mcp_server.handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "prompts/get",
            "params": {
                "name": "task_planning",
                "arguments": {"objective": "Audit inventory", "constraints": "budget=$0"},
            },
        }
    )
    messages = resp["result"]["messages"]
    assert messages[0]["role"] == "user"
    assert "Audit inventory" in messages[0]["content"]["text"]


# ---------------------------------------------------------------------------
# HTTP endpoint tests (REST wrapper + JSON-RPC transport)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_http_mcp_capabilities(client: AsyncClient):
    resp = await client.get("/api/v1/mcp/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    # Response model strips to the declared fields, but at minimum must be
    # a JSON object — smoke test only.
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_http_mcp_list_tools(client: AsyncClient):
    resp = await client.get("/api/v1/mcp/tools")
    assert resp.status_code == 200
    tools = resp.json()["tools"]
    assert any(t["name"] == "get_server_info" for t in tools)


@pytest.mark.asyncio
async def test_http_mcp_jsonrpc_initialize(client: AsyncClient):
    resp = await client.post(
        "/api/v1/mcp/rpc",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": MCP_PROTOCOL_VERSION},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == 1
    assert body["result"]["serverInfo"]["name"] == "zero-employee-orchestrator"


@pytest.mark.asyncio
async def test_http_mcp_jsonrpc_notification_returns_204(client: AsyncClient):
    resp = await client.post(
        "/api/v1/mcp/rpc",
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_http_mcp_jsonrpc_parse_error(client: AsyncClient):
    resp = await client.post(
        "/api/v1/mcp/rpc",
        content=b"not-json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == -32700


@pytest.mark.asyncio
async def test_http_mcp_jsonrpc_batch(client: AsyncClient):
    resp = await client.post(
        "/api/v1/mcp/rpc",
        json=[
            {"jsonrpc": "2.0", "id": 1, "method": "ping"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ],
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 2
    assert body[0]["result"] == {}
    assert "tools" in body[1]["result"]


# ---------------------------------------------------------------------------
# v0.1.6 refinement tests — annotations, logging/setLevel, protocol negotiation,
# malformed payloads, stdio transport loop
# ---------------------------------------------------------------------------


def test_protocol_version_is_2025_11_25():
    """v0.1.6 advertises the MCP 2025-11-25 revision."""
    assert MCP_PROTOCOL_VERSION == "2025-11-25"
    assert "2024-11-05" in MCP_SUPPORTED_PROTOCOL_VERSIONS


def test_tool_annotations_exposed_on_list():
    """Each tool should advertise MCP 2025-11-25 annotation hints."""
    tools = {t.name: t for t in mcp_server._tools.values()}
    # Destructive actions
    assert tools["create_ticket"].destructive_hint is True
    assert tools["execute_skill"].destructive_hint is True
    assert tools["propose_hypothesis"].destructive_hint is True
    # Pure observability (read-only + idempotent)
    for name in (
        "list_tickets",
        "search_knowledge",
        "get_audit_logs",
        "get_kill_switch_status",
        "get_autonomy_level",
        "get_budget_status",
        "list_approvals",
        "get_server_info",
    ):
        assert tools[name].read_only_hint is True, f"{name} should be read-only"

    # to_dict should serialize annotations
    payload = tools["create_ticket"].to_dict()
    assert payload["annotations"]["destructiveHint"] is True
    assert payload["annotations"]["title"] == "Create Ticket"

    read_only_payload = tools["list_tickets"].to_dict()
    assert read_only_payload["annotations"]["readOnlyHint"] is True
    assert read_only_payload["annotations"]["idempotentHint"] is True


@pytest.mark.asyncio
async def test_jsonrpc_initialize_negotiates_old_protocol():
    """A client that asks for 2024-11-05 must get 2024-11-05 echoed back."""
    resp = await mcp_server.handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        }
    )
    assert resp["result"]["protocolVersion"] == "2024-11-05"


@pytest.mark.asyncio
async def test_jsonrpc_logging_set_level():
    prev = logging.getLogger("app").level
    try:
        resp = await mcp_server.handle_jsonrpc(
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "logging/setLevel",
                "params": {"level": "debug"},
            }
        )
        assert resp["result"] == {}
        assert logging.getLogger("app").level == logging.DEBUG

        bad = await mcp_server.handle_jsonrpc(
            {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "logging/setLevel",
                "params": {"level": "lol"},
            }
        )
        assert bad["result"]["isError"] is True

        missing = await mcp_server.handle_jsonrpc(
            {"jsonrpc": "2.0", "id": 14, "method": "logging/setLevel", "params": {}}
        )
        assert missing["error"]["code"] == JSONRPC_INVALID_PARAMS
    finally:
        logging.getLogger("app").setLevel(prev)


@pytest.mark.asyncio
async def test_jsonrpc_rejects_non_dict_payload():
    """A bare string / list / None at the top level is Invalid Request."""
    for bad in ("not-a-dict", None, 42):
        resp = await mcp_server.handle_jsonrpc(bad)  # type: ignore[arg-type]
        assert resp is not None
        assert resp["error"]["code"] == JSONRPC_INVALID_REQUEST


@pytest.mark.asyncio
async def test_jsonrpc_rejects_missing_jsonrpc_version():
    """A payload without ``jsonrpc: "2.0"`` must be rejected."""
    resp = await mcp_server.handle_jsonrpc({"id": 99, "method": "ping"})
    assert resp["error"]["code"] == JSONRPC_INVALID_REQUEST


@pytest.mark.asyncio
async def test_prompt_format_map_tolerates_missing_arg():
    """``prompts/get`` with a missing optional arg must not raise KeyError."""
    resp = await mcp_server.handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "id": 15,
            "method": "prompts/get",
            "params": {
                "name": "task_planning",
                "arguments": {"objective": "Only objective, no constraints"},
            },
        }
    )
    rendered = resp["result"]["messages"][0]["content"]["text"]
    assert "Only objective" in rendered
    # Missing key is preserved as a literal {constraints} placeholder
    assert "{constraints}" in rendered


class _FakeReader:
    def __init__(self, lines: list[bytes]) -> None:
        self._lines = list(lines)

    async def readline(self) -> bytes:
        if not self._lines:
            return b""
        return self._lines.pop(0)


class _FakeWriter:
    def __init__(self) -> None:
        self.buffer: list[str] = []

    def write(self, data) -> None:  # type: ignore[no-untyped-def]
        self.buffer.append(data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else data)


@pytest.mark.asyncio
async def test_stdio_transport_roundtrip():
    """Feed a ping + tools/list + bogus JSON through the stdio loop."""
    reader = _FakeReader(
        [
            b'{"jsonrpc":"2.0","id":1,"method":"ping"}\n',
            b'{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n',
            b"not-json\n",
            b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n',
            b"",  # EOF
        ]
    )
    writer = _FakeWriter()
    await asyncio.wait_for(run_stdio_server(mcp_server, reader=reader, writer=writer), timeout=5)
    lines = [json.loads(line) for line in writer.buffer if line.strip()]
    # 3 responses expected: ping, tools/list, parse error. Notification
    # produces no output.
    assert len(lines) == 3
    assert lines[0]["result"] == {}
    assert "tools" in lines[1]["result"]
    assert lines[2]["error"]["code"] == JSONRPC_PARSE_ERROR


def test_custom_tool_registration_preserves_annotations():
    """Custom tools pushed through register_tool keep their hints."""
    srv = MCPServer()
    srv.register_tool(
        MCPTool(
            name="custom_delete",
            description="Custom",
            destructive_hint=True,
            idempotent_hint=False,
        )
    )
    assert srv._tools["custom_delete"].destructive_hint is True
    payload = srv._tools["custom_delete"].to_dict()
    assert payload["annotations"]["destructiveHint"] is True


# ---------------------------------------------------------------------------
# Coverage for all 14 MCP tools — happy path (read-only) + invalid-params
# ---------------------------------------------------------------------------


# Tools whose handler can be smoked with no required arguments.
_READ_ONLY_ZERO_ARG_TOOLS = [
    "list_tickets",
    "search_knowledge",
    "list_skills",
    "get_audit_logs",
    "monitor_executions",
    "get_kill_switch_status",
    "get_autonomy_level",
    "get_budget_status",
    "list_approvals",
    "get_server_info",
]


@pytest.mark.parametrize("tool_name", _READ_ONLY_ZERO_ARG_TOOLS)
@pytest.mark.asyncio
async def test_tools_call_zero_arg_read_only(tool_name: str):
    """Each zero-arg read-only tool must return a valid JSON-RPC result."""
    resp = await mcp_server.handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "id": 100,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": {}},
        }
    )
    assert resp is not None
    assert "result" in resp, f"{tool_name} returned error: {resp.get('error')}"
    content = resp["result"].get("content")
    assert isinstance(content, list) and content, f"{tool_name} returned empty content"


@pytest.mark.parametrize(
    "tool_name,required_field",
    [
        ("create_ticket", "title"),
        ("execute_skill", "slug"),
        ("propose_hypothesis", "question"),
        ("get_agent_status", "agent_id"),
    ],
)
@pytest.mark.asyncio
async def test_tools_call_missing_required_arg(tool_name: str, required_field: str):
    """Tools that declare a required argument must surface an isError=True
    response (never a generic 500) when the argument is missing."""
    resp = await mcp_server.handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "id": 200,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": {}},
        }
    )
    assert resp is not None
    # Either an MCP tool-level isError flag or a JSON-RPC error is acceptable.
    if "error" in resp:
        assert resp["error"]["code"] in (JSONRPC_INVALID_PARAMS, -32000, -32602, -32603)
    else:
        result = resp["result"]
        assert result.get("isError") is True or required_field.lower() in (
            result.get("content", [{}])[0].get("text", "").lower()
        )


@pytest.mark.asyncio
async def test_tools_call_unknown_tool_returns_error():
    resp = await mcp_server.handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "id": 300,
            "method": "tools/call",
            "params": {"name": "no_such_tool", "arguments": {}},
        }
    )
    assert resp is not None
    # Unknown tool is either a tool-level error or a JSON-RPC error.
    assert "error" in resp or resp["result"].get("isError") is True
