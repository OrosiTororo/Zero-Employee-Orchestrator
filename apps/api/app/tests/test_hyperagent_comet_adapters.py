"""Tests for the v0.1.7 Hyperagent and Comet bridge adapters."""

from __future__ import annotations

import pytest

from app.tools.agent_adapter import (
    _FRAMEWORK_ADAPTERS,
    AgentFrameworkType,
    AgentTask,
    CometAdapter,
    HyperagentAdapter,
)


class TestHyperagentAdapter:
    def test_registered_in_framework_map(self):
        assert _FRAMEWORK_ADAPTERS[AgentFrameworkType.HYPERAGENT] is HyperagentAdapter

    @pytest.mark.asyncio
    async def test_execute_without_endpoint_returns_error(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("HYPERAGENT_ENDPOINT", raising=False)
        adapter = HyperagentAdapter()
        result = await adapter.execute_task(AgentTask(instruction="test"))
        assert result["success"] is False
        assert "HYPERAGENT_ENDPOINT" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_picks_up_per_task_endpoint(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("HYPERAGENT_ENDPOINT", raising=False)
        adapter = HyperagentAdapter()
        task = AgentTask(instruction="test", context={"hyperagent_endpoint": "http://x"})
        # Real httpx call will still fail — but not with the "not configured" error.
        result = await adapter.execute_task(task)
        assert result["success"] is False
        assert "HYPERAGENT_ENDPOINT" not in (result.get("error") or "")

    @pytest.mark.asyncio
    async def test_health_check_reports_false_without_endpoint(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("HYPERAGENT_ENDPOINT", raising=False)
        health = await HyperagentAdapter().health_check()
        assert health["ok"] is False

    def test_capabilities_include_code_execution(self):
        caps = HyperagentAdapter().get_capabilities()
        assert caps.tool_use is True
        assert caps.web_browsing is True
        assert caps.code_execution is True


class TestCometAdapter:
    def test_registered_in_framework_map(self):
        assert _FRAMEWORK_ADAPTERS[AgentFrameworkType.COMET] is CometAdapter

    @pytest.mark.asyncio
    async def test_execute_without_any_endpoint_returns_error(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("COMET_API_ENDPOINT", raising=False)
        monkeypatch.delenv("COMET_WS_ENDPOINT", raising=False)
        adapter = CometAdapter()
        result = await adapter.execute_task(AgentTask(instruction="research"))
        assert result["success"] is False
        assert "Neither" in result["error"]

    @pytest.mark.asyncio
    async def test_api_mode_requires_api_key(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("COMET_API_ENDPOINT", "https://api.example.com")
        monkeypatch.delenv("COMET_API_KEY", raising=False)
        result = await CometAdapter().execute_task(AgentTask(instruction="x"))
        assert result["success"] is False
        assert "API_KEY" in result["error"]

    @pytest.mark.asyncio
    async def test_browser_relay_queues_job_without_external_call(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("COMET_API_ENDPOINT", raising=False)
        monkeypatch.setenv("COMET_WS_ENDPOINT", "ws://localhost:9999/comet")
        task = AgentTask(instruction="find recent OSS news")
        result = await CometAdapter().execute_task(task)
        assert result["success"] is True
        assert result["mode"] == "browser_relay"
        assert result["requires_user_interaction"] is True
        assert result["job_id"] == task.id

    @pytest.mark.asyncio
    async def test_health_distinguishes_api_and_relay(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("COMET_API_ENDPOINT", "https://api.example.com")
        monkeypatch.delenv("COMET_WS_ENDPOINT", raising=False)
        health = await CometAdapter().health_check()
        assert health["ok"] is True
        assert health["api_mode_configured"] is True
        assert health["browser_relay_configured"] is False
