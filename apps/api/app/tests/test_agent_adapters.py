"""Tests for the /agent-adapters endpoints and the underlying registry.

Covers the meta-orchestrator sub-worker surface: CrewAI, AutoGen, LangChain,
OpenClaw, Dify, n8n.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.policies.approval_gate import ApprovalCategory, check_approval_required
from app.tools.agent_adapter import (
    AgentFrameworkType,
    AgentTask,
    AgentTaskStatus,
    agent_adapter_registry,
)


def _fresh_registry() -> None:
    """Drop any adapters registered by prior tests in the same session."""
    agent_adapter_registry._adapters.clear()
    agent_adapter_registry._active = None
    agent_adapter_registry._task_history.clear()


async def _auth_headers(client: AsyncClient, email: str) -> dict:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPassword123!", "display_name": "Agent Tester"},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_installable_frameworks_listed(client: AsyncClient):
    """All six competitor frameworks surface via /installable."""
    _fresh_registry()
    headers = await _auth_headers(client, "adapter_installable@example.com")
    resp = await client.get("/api/v1/agent-adapters/installable", headers=headers)
    assert resp.status_code == 200
    frameworks = {row["framework"] for row in resp.json()["installable"]}
    assert {"crewai", "autogen", "langchain", "openclaw", "dify", "n8n"}.issubset(frameworks)


@pytest.mark.asyncio
async def test_register_and_activate(client: AsyncClient):
    """Register a built-in framework, then make it the active adapter."""
    _fresh_registry()
    headers = await _auth_headers(client, "adapter_register@example.com")

    reg = await client.post(
        "/api/v1/agent-adapters/register",
        json={"framework": "crewai"},
        headers=headers,
    )
    assert reg.status_code == 200
    assert reg.json()["registered"] == "crewai"

    listed = await client.get("/api/v1/agent-adapters", headers=headers)
    assert listed.status_code == 200
    names = {row["framework"] for row in listed.json()["adapters"]}
    assert "crewai" in names

    act = await client.post("/api/v1/agent-adapters/autogen/activate", headers=headers)
    assert act.status_code == 404  # not yet registered

    await client.post(
        "/api/v1/agent-adapters/register",
        json={"framework": "autogen"},
        headers=headers,
    )
    act = await client.post("/api/v1/agent-adapters/autogen/activate", headers=headers)
    assert act.status_code == 200
    assert act.json()["active"] == "autogen"


@pytest.mark.asyncio
async def test_register_rejects_unknown_framework(client: AsyncClient):
    _fresh_registry()
    headers = await _auth_headers(client, "adapter_unknown@example.com")
    resp = await client.post(
        "/api/v1/agent-adapters/register",
        json={"framework": "nonexistent-framework"},
        headers=headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_execute_without_adapter_returns_failed(client: AsyncClient):
    """No registered framework → task completes with FAILED status, not 500."""
    _fresh_registry()
    headers = await _auth_headers(client, "adapter_noadapter@example.com")
    resp = await client.post(
        "/api/v1/agent-adapters/execute",
        json={"instruction": "hello", "require_approval": False},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == AgentTaskStatus.FAILED.value
    assert "No adapter registered" in (body["error"] or "")


@pytest.mark.asyncio
async def test_execute_with_approval_required_blocks(client: AsyncClient):
    """require_approval=True + dangerous op → APPROVAL_REQUIRED, not executed."""
    _fresh_registry()
    agent_adapter_registry.register(AgentFrameworkType.CREWAI.value)
    headers = await _auth_headers(client, "adapter_gated@example.com")
    resp = await client.post(
        "/api/v1/agent-adapters/execute",
        json={"instruction": "run a crew", "framework": "crewai", "require_approval": True},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == AgentTaskStatus.APPROVAL_REQUIRED.value
    assert body["result"]["approval_category"] == ApprovalCategory.EXTERNAL_AGENT.value


def test_external_agent_execution_is_dangerous():
    """The adapter's approval_gate wiring actually triggers."""
    gate = check_approval_required("external_agent_execution")
    assert gate.requires_approval is True
    assert gate.category == ApprovalCategory.EXTERNAL_AGENT


@pytest.mark.asyncio
async def test_registry_execute_task_smoke():
    """Happy path at the registry level: no network, approval skipped."""
    _fresh_registry()
    agent_adapter_registry.register(AgentFrameworkType.N8N.value)

    task = AgentTask(
        instruction="ping",
        framework="n8n",
        require_approval=False,
    )
    result = await agent_adapter_registry.execute_task(task)
    # n8n adapter will fail cleanly because N8N_AGENT_WEBHOOK_URL is not set;
    # what matters is the registry returned a terminal status, not raised.
    assert result.status in (AgentTaskStatus.FAILED, AgentTaskStatus.COMPLETED)
    assert result.completed_at is not None
