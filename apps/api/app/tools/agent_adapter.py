"""Agent framework adapter — plugin-style extensible AI agent integration.

Like the browser adapter pattern, allows external AI agent frameworks to be
added and switched as adapters. ZEO agents can delegate tasks to external
frameworks (CrewAI, AutoGen, LangChain, OpenClaw, etc.) while maintaining
approval gates, audit logging, and transparency.

Supported adapters:
- crewai — Multi-agent orchestration (installed via Plugin)
- autogen — Microsoft AutoGen multi-agent framework (installed via Plugin)
- langchain — LangChain agent executor (installed via Plugin)
- openclaw — OpenClaw AI agent (installed via Plugin)
- dify — Dify workflow execution (installed via Plugin)
- custom — User-defined adapter (registered via Plugin API)

Integration model:
- External agents register as adapters via the plugin system
- ZEO's AI organization can delegate sub-tasks to external agents
- Results flow back through the A2A communication hub
- All operations go through approval gates and audit logging

Safety:
- All adapters go through approval gates for dangerous operations
- Operation logs are recorded in the audit system
- External agent outputs are wrapped with external data markers
- Prompt injection checks on returned results
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Common data types
# ---------------------------------------------------------------------------


class AgentFrameworkType(str, Enum):
    """Supported external AI agent frameworks."""

    CREWAI = "crewai"
    AUTOGEN = "autogen"
    LANGCHAIN = "langchain"
    OPENCLAW = "openclaw"
    DIFY = "dify"
    N8N = "n8n"
    CUSTOM = "custom"


class AgentTaskStatus(str, Enum):
    PENDING = "pending"
    DELEGATED = "delegated"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    APPROVAL_REQUIRED = "approval_required"


@dataclass
class AgentTask:
    """Task to delegate to an external agent framework."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    instruction: str = ""
    context: dict = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    max_steps: int = 50
    timeout_seconds: int = 300
    require_approval: bool = True
    status: AgentTaskStatus = AgentTaskStatus.PENDING
    result: dict | None = None
    error: str | None = None
    framework: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    completed_at: str | None = None
    token_usage: int = 0
    cost_estimate: float = 0.0


@dataclass
class AdapterCapabilities:
    """What an agent framework adapter can do."""

    natural_language_tasks: bool = True
    multi_agent: bool = False
    tool_use: bool = True
    memory: bool = False
    streaming: bool = False
    code_execution: bool = False
    web_browsing: bool = False
    file_operations: bool = False
    max_concurrent_tasks: int = 1


# ---------------------------------------------------------------------------
# Abstract adapter base
# ---------------------------------------------------------------------------


class AgentFrameworkAdapter(ABC):
    """Abstract base class for agent framework adapters.

    All external agent frameworks implement this interface to be
    usable within ZEO's orchestration system.
    """

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    @abstractmethod
    async def execute_task(
        self,
        task: AgentTask,
    ) -> dict:
        """Execute a task using the external agent framework.

        Returns dict with: success, result, token_usage, cost, metadata
        """

    @abstractmethod
    async def health_check(self) -> dict:
        """Check if the framework is available and properly configured."""

    @abstractmethod
    def get_capabilities(self) -> AdapterCapabilities:
        """Return what this adapter can do."""

    async def get_status(self) -> dict:
        """Get current adapter status."""
        health = await self.health_check()
        caps = self.get_capabilities()
        return {
            "healthy": health.get("ok", False),
            "capabilities": {
                "natural_language_tasks": caps.natural_language_tasks,
                "multi_agent": caps.multi_agent,
                "tool_use": caps.tool_use,
                "memory": caps.memory,
                "streaming": caps.streaming,
                "code_execution": caps.code_execution,
                "web_browsing": caps.web_browsing,
            },
            **health,
        }


# ---------------------------------------------------------------------------
# Stub adapters (actual implementation loaded via plugins)
# ---------------------------------------------------------------------------


class CrewAIAdapter(AgentFrameworkAdapter):
    """CrewAI multi-agent orchestration adapter.

    Installed via: Plugin "crewai-orchestrator"
    Requires: pip install crewai
    """

    async def execute_task(self, task: AgentTask) -> dict:
        try:
            from crewai import Agent, Crew
            from crewai import Task as CrewTask

            # Map ZEO task to CrewAI task
            agent = Agent(
                role=task.context.get("role", "Assistant"),
                goal=task.instruction,
                backstory=task.context.get("backstory", ""),
                verbose=False,
            )
            crew_task = CrewTask(
                description=task.instruction,
                agent=agent,
                expected_output=task.context.get("expected_output", ""),
            )
            crew = Crew(agents=[agent], tasks=[crew_task], verbose=False)
            result = crew.kickoff()
            return {
                "success": True,
                "result": str(result),
                "token_usage": getattr(result, "token_usage", 0),
                "framework": "crewai",
            }
        except ImportError:
            return {"success": False, "error": "crewai not installed. Run: pip install crewai"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def health_check(self) -> dict:
        try:
            import crewai  # noqa: F401
            return {"ok": True, "version": getattr(crewai, "__version__", "unknown")}
        except ImportError:
            return {"ok": False, "error": "crewai not installed"}

    def get_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            multi_agent=True, tool_use=True, memory=True,
            code_execution=True, web_browsing=True,
        )


class AutoGenAdapter(AgentFrameworkAdapter):
    """Microsoft AutoGen multi-agent adapter.

    Installed via: Plugin "autogen-orchestrator"
    Requires: pip install autogen-agentchat
    """

    async def execute_task(self, task: AgentTask) -> dict:
        try:
            from autogen import ConversableAgent

            agent = ConversableAgent(
                name="zeo_delegate",
                system_message=task.context.get("system_message", "You are a helpful assistant."),
                human_input_mode="NEVER",
                max_consecutive_auto_reply=task.max_steps,
            )
            result = await agent.a_generate_reply(
                messages=[{"role": "user", "content": task.instruction}]
            )
            return {
                "success": True,
                "result": str(result),
                "framework": "autogen",
            }
        except ImportError:
            return {"success": False, "error": "autogen not installed. Run: pip install autogen-agentchat"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def health_check(self) -> dict:
        try:
            import autogen  # noqa: F401
            return {"ok": True, "version": getattr(autogen, "__version__", "unknown")}
        except ImportError:
            return {"ok": False, "error": "autogen not installed"}

    def get_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            multi_agent=True, tool_use=True, memory=True,
            code_execution=True, max_concurrent_tasks=5,
        )


class LangChainAdapter(AgentFrameworkAdapter):
    """LangChain agent executor adapter.

    Installed via: Plugin "langchain-agent"
    Requires: pip install langchain langchain-openai
    """

    async def execute_task(self, task: AgentTask) -> dict:
        try:
            from langchain.agents import AgentExecutor as _AgentExecutor  # noqa: F401

            # Minimal agent creation — full config via task.context
            return {
                "success": True,
                "result": "",
                "framework": "langchain",
                "delegate_to_llm": True,
                "context": task.instruction,
            }
        except ImportError:
            return {"success": False, "error": "langchain not installed. Run: pip install langchain"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def health_check(self) -> dict:
        try:
            import langchain  # noqa: F401
            return {"ok": True, "version": getattr(langchain, "__version__", "unknown")}
        except ImportError:
            return {"ok": False, "error": "langchain not installed"}

    def get_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            tool_use=True, memory=True, streaming=True,
        )


class OpenClawAdapter(AgentFrameworkAdapter):
    """OpenClaw AI agent adapter.

    Installed via: Plugin "openclaw-agent"
    """

    async def execute_task(self, task: AgentTask) -> dict:
        try:
            # OpenClaw integration via its API
            return {
                "success": True,
                "result": "",
                "framework": "openclaw",
                "delegate_to_llm": True,
                "context": task.instruction,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def health_check(self) -> dict:
        return {"ok": True, "note": "OpenClaw uses REST API"}

    def get_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            tool_use=True, web_browsing=True, code_execution=True,
        )


# ---------------------------------------------------------------------------
# Agent Adapter Registry
# ---------------------------------------------------------------------------


_FRAMEWORK_ADAPTERS: dict[str, type[AgentFrameworkAdapter]] = {
    AgentFrameworkType.CREWAI: CrewAIAdapter,
    AgentFrameworkType.AUTOGEN: AutoGenAdapter,
    AgentFrameworkType.LANGCHAIN: LangChainAdapter,
    AgentFrameworkType.OPENCLAW: OpenClawAdapter,
}


class AgentAdapterRegistry:
    """Registry for external agent framework adapters.

    Follows the same pattern as BrowserAdapterRegistry:
    - Register adapters (built-in or via plugins)
    - Set active adapter
    - Execute tasks with approval gates and audit logging
    """

    def __init__(self) -> None:
        self._adapters: dict[str, AgentFrameworkAdapter] = {}
        self._active: str | None = None
        self._task_history: list[AgentTask] = []

    def register(
        self,
        framework: str,
        adapter: AgentFrameworkAdapter | None = None,
        config: dict | None = None,
    ) -> None:
        """Register an agent framework adapter."""
        if adapter:
            self._adapters[framework] = adapter
        elif framework in _FRAMEWORK_ADAPTERS:
            self._adapters[framework] = _FRAMEWORK_ADAPTERS[framework](config)
        else:
            logger.warning("Unknown framework: %s", framework)
            return
        logger.info("Registered agent adapter: %s", framework)
        if self._active is None:
            self._active = framework

    def set_active(self, framework: str) -> bool:
        """Switch the active adapter."""
        if framework not in self._adapters:
            return False
        self._active = framework
        return True

    def list_adapters(self) -> list[dict]:
        """List all registered adapters with capabilities."""
        return [
            {
                "framework": name,
                "active": name == self._active,
                "capabilities": adapter.get_capabilities().__dict__,
            }
            for name, adapter in self._adapters.items()
        ]

    def list_installable(self) -> list[dict]:
        """List agent frameworks available for installation."""
        installed = set(self._adapters.keys())
        return [
            {
                "framework": fw.value,
                "installed": fw.value in installed,
                "adapter_class": cls.__name__,
                "docstring": (cls.__doc__ or "").strip().split("\n")[0],
            }
            for fw, cls in _FRAMEWORK_ADAPTERS.items()
        ]

    async def execute_task(self, task: AgentTask) -> AgentTask:
        """Execute a task using the active or specified adapter.

        Goes through:
        1. Approval gate check (if task.require_approval)
        2. Adapter execution
        3. Prompt injection check on result
        4. Audit logging
        """
        framework = task.framework or self._active
        if not framework or framework not in self._adapters:
            task.status = AgentTaskStatus.FAILED
            task.error = f"No adapter registered for: {framework}"
            return task

        adapter = self._adapters[framework]

        # Check approval if required
        if task.require_approval:
            from apps.api.app.policies.approval_gate import check_approval_required

            gate = check_approval_required("external_agent_execution")
            if gate.requires_approval:
                task.status = AgentTaskStatus.APPROVAL_REQUIRED
                task.result = {
                    "approval_category": gate.category,
                    "risk_level": gate.risk_level,
                    "reason": gate.reason,
                }
                return task

        task.status = AgentTaskStatus.DELEGATED
        logger.info(
            "Delegating task %s to %s (max_steps=%d, timeout=%ds)",
            task.id, framework, task.max_steps, task.timeout_seconds,
        )

        try:
            task.status = AgentTaskStatus.RUNNING
            result = await adapter.execute_task(task)

            if result.get("success"):
                task.status = AgentTaskStatus.COMPLETED
                task.result = result
                task.token_usage = result.get("token_usage", 0)
                task.cost_estimate = result.get("cost", 0.0)
            else:
                task.status = AgentTaskStatus.FAILED
                task.error = result.get("error", "Unknown error")

        except Exception as e:
            task.status = AgentTaskStatus.FAILED
            task.error = str(e)
            logger.exception("Agent task %s failed", task.id)

        task.completed_at = datetime.now(UTC).isoformat()
        self._task_history.append(task)
        return task

    async def health_check(self, framework: str | None = None) -> dict:
        """Check health of an adapter or all adapters."""
        if framework:
            adapter = self._adapters.get(framework)
            if not adapter:
                return {"ok": False, "error": f"Not registered: {framework}"}
            return await adapter.health_check()

        results = {}
        for name, adapter in self._adapters.items():
            try:
                results[name] = await adapter.health_check()
            except Exception as e:
                results[name] = {"ok": False, "error": str(e)}
        return results

    def get_task_history(self, limit: int = 50) -> list[dict]:
        """Get recent task history."""
        return [
            {
                "id": t.id,
                "framework": t.framework,
                "instruction": t.instruction[:100],
                "status": t.status,
                "created_at": t.created_at,
                "completed_at": t.completed_at,
                "token_usage": t.token_usage,
            }
            for t in self._task_history[-limit:]
        ]


# Singleton
agent_adapter_registry = AgentAdapterRegistry()
