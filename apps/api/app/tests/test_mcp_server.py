"""MCP server and JSON-RPC 2.0 endpoint tests (v0.1.6)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.integrations.mcp_server import (
    JSONRPC_INVALID_PARAMS,
    JSONRPC_METHOD_NOT_FOUND,
    MCP_PROTOCOL_VERSION,
    MCPServer,
    mcp_server,
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
    resp = await mcp_server.handle_jsonrpc(
        {"jsonrpc": "2.0", "id": 6, "method": "does_not_exist"}
    )
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
    resp = await mcp_server.handle_jsonrpc(
        {"jsonrpc": "2.0", "id": 7, "method": "resources/list"}
    )
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
