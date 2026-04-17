"""Tests for the 5 competitive-parity enhancements shipped in v0.1.7-final.

Each test targets one competitor-inspired surface:
- DAG node-result cache        (LangGraph)
- Workflow template library    (Dify)
- Generic HTTP connector       (n8n)
- One-shot crew spawn          (CrewAI)
- Microsoft Graph (M365) app   (Microsoft Agent Framework)
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.integrations.app_connector import app_connector_hub
from app.orchestration.dag import TaskNode
from app.orchestration.executor import NodeResultCache, TaskExecutor

async def _auth_headers(client: AsyncClient, _email: str) -> dict:
    """conftest overrides get_current_user to a stub, so any header works."""
    return {"Authorization": "Bearer test-token"}


# --------------------------- LangGraph-style cache --------------------------- #


def test_node_cache_stores_and_retrieves():
    cache = NodeResultCache(maxsize=4)
    key = NodeResultCache.make_key("Summarize", "p", "ctx", "quality")
    from app.orchestration.executor import ExecutionResult

    res = ExecutionResult(node_id="n1", success=True, content="ok")
    assert cache.get(key) is None
    cache.put(key, res)
    hit = cache.get(key)
    assert hit is not None
    assert hit.content == "ok"
    stats = cache.stats()
    assert stats["hits"] == 1 and stats["misses"] == 1


def test_node_cache_is_bounded():
    cache = NodeResultCache(maxsize=2)
    from app.orchestration.executor import ExecutionResult

    for i in range(3):
        cache.put(f"k{i}", ExecutionResult(node_id=f"n{i}", success=True, content=str(i)))
    assert cache.stats()["size"] == 2
    assert cache.get("k0") is None  # evicted
    assert cache.get("k2") is not None


def test_executor_cache_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ZEO_DAG_CACHE", raising=False)
    ex = TaskExecutor()
    assert ex._cache_enabled is False


def test_executor_cache_enabled_via_env(monkeypatch):
    monkeypatch.setenv("ZEO_DAG_CACHE", "1")
    ex = TaskExecutor()
    assert ex._cache_enabled is True


# ----------------------- Dify-style workflow templates ----------------------- #


@pytest.mark.asyncio
async def test_workflow_templates_builtin_list(client: AsyncClient):
    headers = await _auth_headers(client, "tmpl_list@example.com")
    resp = await client.get("/api/v1/workflow-templates", headers=headers)
    assert resp.status_code == 200
    slugs = {t["slug"] for t in resp.json()["templates"]}
    assert {"research-brief", "weekly-report", "customer-onboarding"}.issubset(slugs)


@pytest.mark.asyncio
async def test_workflow_template_instantiate(client: AsyncClient):
    headers = await _auth_headers(client, "tmpl_inst@example.com")
    resp = await client.post(
        "/api/v1/workflow-templates/research-brief/instantiate",
        json={"ticket_title": "Market scan for Q2", "variables": {}},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["template_slug"] == "research-brief"
    assert len(body["nodes"]) == 3
    # Dependency chain: n1 -> n2 -> n3
    titles = [n["title"] for n in body["nodes"]]
    assert "Gather primary sources" in titles[0]


@pytest.mark.asyncio
async def test_workflow_template_save_reject_reserved_slug(client: AsyncClient):
    headers = await _auth_headers(client, "tmpl_save@example.com")
    resp = await client.post(
        "/api/v1/workflow-templates",
        json={
            "slug": "research-brief",
            "name": "Clobber attempt",
            "nodes": [{"id": "n1", "title": "noop"}],
        },
        headers=headers,
    )
    assert resp.status_code == 409


# ---------------------- n8n-style generic HTTP connector --------------------- #


def test_generic_http_app_registered():
    apps = {a.id for a in app_connector_hub.list_apps()}
    assert "generic_http" in apps
    assert "microsoft_graph" in apps


def test_generic_http_handler_resolves():
    # Even without a real HTTP call, the handler must be wired for dispatch.
    handler = app_connector_hub._get_sync_handler("generic_http")
    assert handler is not None
    graph = app_connector_hub._get_sync_handler("microsoft_graph")
    assert graph is not None


# ------------------------- CrewAI-style crew spawn --------------------------- #


@pytest.mark.asyncio
async def test_crew_presets_surface(client: AsyncClient):
    headers = await _auth_headers(client, "crew_presets@example.com")
    resp = await client.get("/api/v1/crews/presets", headers=headers)
    assert resp.status_code == 200
    presets = resp.json()["presets"]
    assert "startup-founding-team" in presets
    assert {r["name"] for r in presets["startup-founding-team"]} == {"CEO", "CTO", "CMO", "COO"}


@pytest.mark.asyncio
async def test_crew_spawn_from_preset(client: AsyncClient):
    headers = await _auth_headers(client, "crew_spawn@example.com")
    resp = await client.post(
        "/api/v1/crews",
        json={"name": "ACME launch squad", "preset": "startup-founding-team"},
        headers=headers,
    )
    assert resp.status_code == 200
    crew = resp.json()["crew"]
    assert len(crew["members"]) == 4
    assert crew["execution_mode"] == "parallel"


@pytest.mark.asyncio
async def test_crew_spawn_requires_roles(client: AsyncClient):
    headers = await _auth_headers(client, "crew_norole@example.com")
    resp = await client.post(
        "/api/v1/crews",
        json={"name": "Empty crew"},
        headers=headers,
    )
    assert resp.status_code == 400


# --- Lightweight sanity check that TaskNode still constructs for cache key --- #


def test_task_node_roundtrip():
    node = TaskNode(id="n1", title="t")
    key = NodeResultCache.make_key(node.title, "prompt", "ctx", "quality")
    assert len(key) == 64  # sha256 hex
