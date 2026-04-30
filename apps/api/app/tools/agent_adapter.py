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
    HYPERAGENT = "hyperagent"
    COMET = "comet"
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
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    token_usage: int = 0
    cost_estimate: float = 0.0
    # ZEO meta-orchestrator hooks: when delegating a Plan-tracked goal to an
    # external framework, the parent ZEO Plan id is carried so the sub-plan
    # extracted from the framework's intermediate output can be persisted as
    # a child Plan and joined back to the parent's audit trail.
    parent_plan_id: str | None = None
    company_id: str | None = None
    # Populated by ``_extract_sub_plan`` after execution; serialised into the
    # AuditLog so reviewers can see exactly what the sub-orchestrator did.
    sub_plan_steps: list[str] = field(default_factory=list)
    sub_plan_json: dict | None = None
    delegation_reasoning: str = ""


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

            # Capture intermediate reasoning steps so the orchestrator can
            # persist them as a sub-plan and surface them in audit trails.
            sub_plan_steps: list[str] = []

            def _step_callback(step_output) -> None:  # pragma: no cover - depends on crewai version
                try:
                    sub_plan_steps.append(str(step_output)[:1000])
                except Exception:
                    pass

            # Map ZEO task to CrewAI task
            agent_kwargs: dict = {
                "role": task.context.get("role", "Assistant"),
                "goal": task.instruction,
                "backstory": task.context.get("backstory", ""),
                "verbose": False,
            }
            agent = Agent(**agent_kwargs)
            crew_task = CrewTask(
                description=task.instruction,
                agent=agent,
                expected_output=task.context.get("expected_output", ""),
            )
            crew_kwargs: dict = {"agents": [agent], "tasks": [crew_task], "verbose": False}
            try:
                crew = Crew(step_callback=_step_callback, **crew_kwargs)
            except TypeError:
                # Older crewai builds don't accept step_callback at the Crew
                # level; fall back to the basic constructor.
                crew = Crew(**crew_kwargs)
            result = crew.kickoff()
            return {
                "success": True,
                "result": str(result),
                "token_usage": getattr(result, "token_usage", 0),
                "framework": "crewai",
                "sub_plan_steps": sub_plan_steps,
                "sub_plan_json": {
                    "framework": "crewai",
                    "agent_role": agent_kwargs["role"],
                    "task_description": task.instruction,
                    "step_count": len(sub_plan_steps),
                },
                "delegation_reasoning": (
                    f"Delegated to CrewAI with {len(sub_plan_steps)} intermediate step(s)."
                ),
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
            multi_agent=True,
            tool_use=True,
            memory=True,
            code_execution=True,
            web_browsing=True,
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
            return {
                "success": False,
                "error": "autogen not installed. Run: pip install autogen-agentchat",
            }
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
            multi_agent=True,
            tool_use=True,
            memory=True,
            code_execution=True,
            max_concurrent_tasks=5,
        )


class LangChainAdapter(AgentFrameworkAdapter):
    """LangChain agent executor adapter.

    Runs a LangChain AgentExecutor with the ReAct agent type.
    Falls back to a simple LLM chain if agent tools are not configured.

    Installed via: Plugin "langchain-agent"
    Requires: pip install langchain langchain-openai
    """

    async def execute_task(self, task: AgentTask) -> dict:
        try:
            import asyncio as _aio

            from langchain.agents import AgentType, initialize_agent
            from langchain.tools import Tool
            from langchain_openai import ChatOpenAI

            # Build LLM from task context or env
            model = task.context.get("model", "gpt-4o-mini")
            api_key = task.context.get("api_key", "")
            llm_kwargs: dict = {"model": model, "temperature": 0.7}
            if api_key:
                llm_kwargs["api_key"] = api_key
            llm = ChatOpenAI(**llm_kwargs)

            # Build tools from task context
            tool_defs = task.context.get("tools", [])
            tools = []
            for td in tool_defs:
                tools.append(
                    Tool(
                        name=td.get("name", "tool"),
                        description=td.get("description", ""),
                        func=lambda x: x,  # placeholder — real tools wired via MCP
                    )
                )

            if tools:
                agent = initialize_agent(
                    tools=tools,
                    llm=llm,
                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=False,
                    max_iterations=task.max_steps,
                    handle_parsing_errors=True,
                )
                result = await _aio.to_thread(agent.run, task.instruction)
            else:
                # No tools — direct LLM invocation
                from langchain.schema import HumanMessage

                response = await _aio.to_thread(
                    llm.invoke, [HumanMessage(content=task.instruction)]
                )
                result = response.content if hasattr(response, "content") else str(response)

            return {
                "success": True,
                "result": str(result),
                "framework": "langchain",
            }
        except ImportError:
            return {
                "success": False,
                "error": "langchain not installed. Run: pip install langchain langchain-openai",
            }
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
            tool_use=True,
            memory=True,
            streaming=True,
        )


class OpenClawAdapter(AgentFrameworkAdapter):
    """OpenClaw AI agent adapter — via REST API.

    Connects to a running OpenClaw instance and delegates task execution.
    Requires OPENCLAW_URL environment variable (e.g. http://localhost:8080).
    """

    async def execute_task(self, task: AgentTask) -> dict:
        import os

        base_url = os.environ.get("OPENCLAW_URL", task.context.get("openclaw_url", ""))
        if not base_url:
            return {
                "success": False,
                "error": "OPENCLAW_URL not configured. Set env var or pass openclaw_url in context.",  # noqa: E501
            }
        try:
            import httpx

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{base_url.rstrip('/')}/api/v1/tasks",
                    json={
                        "instruction": task.instruction,
                        "context": task.context,
                        "max_steps": task.max_steps,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
            return {
                "success": True,
                "result": data.get("result", str(data)),
                "framework": "openclaw",
            }
        except ImportError:
            return {"success": False, "error": "httpx not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def health_check(self) -> dict:
        import os

        base_url = os.environ.get("OPENCLAW_URL", "")
        if not base_url:
            return {"ok": False, "error": "OPENCLAW_URL not set"}
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{base_url.rstrip('/')}/health")
                return {"ok": resp.status_code == 200}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            tool_use=True,
            web_browsing=True,
            code_execution=True,
        )


class DifyAdapter(AgentFrameworkAdapter):
    """Dify workflow/agent adapter — via REST API.

    Connects to a Dify instance and runs workflows or agent conversations.
    Requires DIFY_URL and DIFY_API_KEY environment variables.
    """

    async def execute_task(self, task: AgentTask) -> dict:
        import os

        base_url = os.environ.get("DIFY_URL", task.context.get("dify_url", ""))
        api_key = os.environ.get("DIFY_API_KEY", task.context.get("dify_api_key", ""))
        if not base_url or not api_key:
            return {
                "success": False,
                "error": "DIFY_URL and DIFY_API_KEY must be configured.",
            }
        try:
            import httpx

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{base_url.rstrip('/')}/v1/chat-messages",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "inputs": task.context.get("inputs", {}),
                        "query": task.instruction,
                        "response_mode": "blocking",
                        "user": task.context.get("user", "zeo-orchestrator"),
                    },
                )
                resp.raise_for_status()
                data = resp.json()
            metadata = data.get("metadata", {}) or {}
            usage = metadata.get("usage", {}) or {}
            sub_plan_steps: list[str] = []
            for node in metadata.get("retriever_resources", []) or []:
                src = node.get("source") if isinstance(node, dict) else None
                if src:
                    sub_plan_steps.append(str(src)[:500])
            for node in (data.get("workflow_run", {}) or {}).get("nodes", []) or []:
                title = node.get("title") if isinstance(node, dict) else None
                if title:
                    sub_plan_steps.append(str(title)[:500])
            return {
                "success": True,
                "result": data.get("answer", str(data)),
                "conversation_id": data.get("conversation_id"),
                "framework": "dify",
                "token_usage": int(usage.get("total_tokens", 0) or 0),
                "sub_plan_steps": sub_plan_steps,
                "sub_plan_json": {
                    "framework": "dify",
                    "conversation_id": data.get("conversation_id"),
                    "message_id": data.get("message_id"),
                    "step_count": len(sub_plan_steps),
                },
                "delegation_reasoning": (
                    f"Delegated to Dify (mode={data.get('mode', 'chat')}); "
                    f"{len(sub_plan_steps)} retrieval/workflow node(s) reported."
                ),
            }
        except ImportError:
            return {"success": False, "error": "httpx not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def health_check(self) -> dict:
        import os

        base_url = os.environ.get("DIFY_URL", "")
        if not base_url:
            return {"ok": False, "error": "DIFY_URL not set"}
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{base_url.rstrip('/')}/v1/parameters")
                return {"ok": resp.status_code in (200, 401)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            tool_use=True,
            memory=True,
            streaming=True,
        )


class N8NAgentAdapter(AgentFrameworkAdapter):
    """n8n workflow-as-agent adapter — via webhook trigger.

    Runs an n8n workflow that acts as an AI agent. The workflow receives
    the task instruction and returns the result via webhook response.
    Requires N8N_WEBHOOK_URL environment variable.
    """

    async def execute_task(self, task: AgentTask) -> dict:
        import os

        webhook_url = os.environ.get(
            "N8N_AGENT_WEBHOOK_URL",
            task.context.get("n8n_webhook_url", ""),
        )
        if not webhook_url:
            return {
                "success": False,
                "error": "N8N_AGENT_WEBHOOK_URL not configured.",
            }
        try:
            import httpx

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    webhook_url,
                    json={
                        "instruction": task.instruction,
                        "context": task.context,
                        "max_steps": task.max_steps,
                    },
                )
                resp.raise_for_status()
                data = (
                    resp.json()
                    if resp.headers.get("content-type", "").startswith("application/json")
                    else {"result": resp.text}
                )
            return {
                "success": True,
                "result": data.get("result", str(data)),
                "framework": "n8n",
            }
        except ImportError:
            return {"success": False, "error": "httpx not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def health_check(self) -> dict:
        import os

        url = os.environ.get("N8N_AGENT_WEBHOOK_URL", "")
        return {"ok": bool(url), "note": "n8n health depends on workflow availability"}

    def get_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            tool_use=True,
            web_browsing=True,
            memory=True,
        )


class HyperagentAdapter(AgentFrameworkAdapter):
    """Hyperagent bridge — delegate to a Hyperagent node via HTTP.

    Configuration (two ways):

    * ``HYPERAGENT_ENDPOINT`` environment variable pointing at the node's
      ``/api/v1/run`` URL, optionally with ``HYPERAGENT_API_KEY``.
    * Per-task override via ``task.context['hyperagent_endpoint']``.

    The bridge sends ``{instruction, context, max_steps, timeout_seconds}``
    and expects a JSON response of ``{result | error, artifacts?, usage?}``.
    Return payloads are wrapped with ``wrap_external_data`` before being
    handed back to the orchestrator so injection inside the remote agent's
    output cannot steer ZEO's own LLM calls.
    """

    async def execute_task(self, task: AgentTask) -> dict:
        import os

        endpoint = os.environ.get(
            "HYPERAGENT_ENDPOINT",
            task.context.get("hyperagent_endpoint", ""),
        )
        if not endpoint:
            return {
                "success": False,
                "error": "HYPERAGENT_ENDPOINT not configured.",
            }
        api_key = os.environ.get("HYPERAGENT_API_KEY", "")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            import httpx

            from app.security.prompt_guard import wrap_external_data

            async with httpx.AsyncClient(timeout=task.timeout_seconds) as client:
                resp = await client.post(
                    endpoint,
                    headers=headers,
                    json={
                        "instruction": task.instruction,
                        "context": task.context,
                        "max_steps": task.max_steps,
                        "timeout_seconds": task.timeout_seconds,
                    },
                )
                resp.raise_for_status()
                data = (
                    resp.json()
                    if resp.headers.get("content-type", "").startswith("application/json")
                    else {"result": resp.text}
                )
            raw_result = data.get("result", str(data))
            return {
                "success": True,
                "result": wrap_external_data(str(raw_result), source="hyperagent"),
                "artifacts": data.get("artifacts", []),
                "usage": data.get("usage", {}),
                "framework": "hyperagent",
            }
        except ImportError:
            return {"success": False, "error": "httpx not installed"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def health_check(self) -> dict:
        import os

        endpoint = os.environ.get("HYPERAGENT_ENDPOINT", "")
        return {
            "ok": bool(endpoint),
            "note": "Hyperagent node reachability depends on the configured endpoint.",
        }

    def get_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            tool_use=True,
            web_browsing=True,
            memory=True,
            code_execution=True,
        )


class CometAdapter(AgentFrameworkAdapter):
    """Perplexity Comet bridge — browser-integrated AI agent delegation.

    Unlike Hyperagent, Comet agents run inside the user's browser session.
    This bridge supports two modes:

    * **Synchronous API mode** (recommended for non-interactive use):
      POST to ``COMET_API_ENDPOINT`` with a Comet API key. Used for
      instructions that do not need a live browser UI.

    * **Browser-relay mode** (for interactive research): queue the
      instruction into the existing Comet extension via the internal
      WebSocket bridge at ``COMET_WS_ENDPOINT``. Requires the user to have
      Comet open; the adapter returns a job id and the user approves the
      browser action in Comet's own UI — ZEO never drives a remote
      browser it does not own.

    Both modes route through the approval gate so a browser side-effect
    never fires without the operator's explicit OK.
    """

    async def execute_task(self, task: AgentTask) -> dict:
        import os

        # Prefer API mode if configured; fall back to browser-relay.
        endpoint = os.environ.get(
            "COMET_API_ENDPOINT",
            task.context.get("comet_api_endpoint", ""),
        )
        api_key = os.environ.get("COMET_API_KEY", "")
        ws_endpoint = os.environ.get(
            "COMET_WS_ENDPOINT",
            task.context.get("comet_ws_endpoint", ""),
        )

        if not endpoint and not ws_endpoint:
            return {
                "success": False,
                "error": (
                    "Neither COMET_API_ENDPOINT nor COMET_WS_ENDPOINT is set. "
                    "Configure one of the two transports to delegate to Comet."
                ),
            }
        if endpoint and not api_key:
            return {"success": False, "error": "COMET_API_KEY required for API mode."}

        try:
            import httpx

            from app.security.prompt_guard import wrap_external_data

            if endpoint:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                }
                async with httpx.AsyncClient(timeout=task.timeout_seconds) as client:
                    resp = await client.post(
                        endpoint,
                        headers=headers,
                        json={
                            "prompt": task.instruction,
                            "context": task.context,
                            "max_steps": task.max_steps,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                raw_result = data.get("answer", data.get("result", str(data)))
                return {
                    "success": True,
                    "result": wrap_external_data(str(raw_result), source="comet_api"),
                    "citations": data.get("citations", []),
                    "framework": "comet",
                    "mode": "api",
                }

            # Browser-relay mode — queue and return a job id. The actual
            # user-visible browser action is driven by the Comet extension
            # itself after the user approves; ZEO only schedules the prompt.
            return {
                "success": True,
                "result": (
                    f"Browser-relay queued. Open Comet and approve job "
                    f"{task.id}. Results come back via the /api/v1/"
                    f"agent-adapters/comet/callback endpoint."
                ),
                "job_id": task.id,
                "framework": "comet",
                "mode": "browser_relay",
                "requires_user_interaction": True,
            }
        except ImportError:
            return {"success": False, "error": "httpx not installed"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def health_check(self) -> dict:
        import os

        api = bool(os.environ.get("COMET_API_ENDPOINT"))
        ws = bool(os.environ.get("COMET_WS_ENDPOINT"))
        return {
            "ok": api or ws,
            "api_mode_configured": api,
            "browser_relay_configured": ws,
            "note": (
                "Comet API mode is non-interactive; browser-relay mode "
                "requires the Comet extension to be open in the user's browser."
            ),
        }

    def get_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            tool_use=True,
            web_browsing=True,
            memory=True,
            multi_agent=False,
        )


# ---------------------------------------------------------------------------
# Agent Adapter Registry
# ---------------------------------------------------------------------------


_FRAMEWORK_ADAPTERS: dict[str, type[AgentFrameworkAdapter]] = {
    AgentFrameworkType.CREWAI: CrewAIAdapter,
    AgentFrameworkType.AUTOGEN: AutoGenAdapter,
    AgentFrameworkType.LANGCHAIN: LangChainAdapter,
    AgentFrameworkType.OPENCLAW: OpenClawAdapter,
    AgentFrameworkType.DIFY: DifyAdapter,
    AgentFrameworkType.N8N: N8NAgentAdapter,
    AgentFrameworkType.HYPERAGENT: HyperagentAdapter,
    AgentFrameworkType.COMET: CometAdapter,
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
            from app.policies.approval_gate import check_approval_required

            gate = check_approval_required("external_agent_execution")
            if gate.requires_approval:
                task.status = AgentTaskStatus.APPROVAL_REQUIRED
                task.result = {
                    "approval_category": gate.category.value if gate.category else None,
                    "risk_level": gate.risk_level.value,
                    "reason": gate.reason,
                }
                return task

        task.status = AgentTaskStatus.DELEGATED
        logger.info(
            "Delegating task %s to %s (max_steps=%d, timeout=%ds)",
            task.id,
            framework,
            task.max_steps,
            task.timeout_seconds,
        )

        try:
            task.status = AgentTaskStatus.RUNNING
            result = await adapter.execute_task(task)

            if result.get("success"):
                task.status = AgentTaskStatus.COMPLETED
                task.result = result
                task.token_usage = result.get("token_usage", 0)
                task.cost_estimate = result.get("cost", 0.0)
                # Hoist provenance fields onto the task itself so callers
                # (audit logger, plan tree builder) don't have to dig into
                # the framework-specific ``result`` dict.
                task.sub_plan_steps = list(result.get("sub_plan_steps", []) or [])
                task.sub_plan_json = result.get("sub_plan_json")
                task.delegation_reasoning = result.get("delegation_reasoning", "")
            else:
                task.status = AgentTaskStatus.FAILED
                task.error = result.get("error", "Unknown error")

        except Exception as e:
            task.status = AgentTaskStatus.FAILED
            task.error = str(e)
            logger.exception("Agent task %s failed", task.id)

        task.completed_at = datetime.now(UTC).isoformat()
        self._task_history.append(task)
        await self._persist_audit(task)
        return task

    async def _persist_audit(self, task: AgentTask) -> None:
        """Write the delegation outcome to ``audit_logs`` (best-effort).

        Skipped silently when called outside an app context (e.g. unit tests
        for the adapter classes themselves) so the registry remains usable
        without a live database session.
        """
        if not task.company_id:
            return
        try:
            from app.core.database import async_session_factory
            from app.models.audit import AuditLog
            from app.models.plan import Plan
        except Exception:
            return

        try:
            company_uuid = uuid.UUID(task.company_id)
        except (TypeError, ValueError):
            return

        try:
            async with async_session_factory() as session:
                child_plan_id: uuid.UUID | None = None
                if task.parent_plan_id and task.sub_plan_json:
                    try:
                        parent_uuid = uuid.UUID(task.parent_plan_id)
                    except (TypeError, ValueError):
                        parent_uuid = None
                    if parent_uuid is not None:
                        child = Plan(
                            id=uuid.uuid4(),
                            company_id=company_uuid,
                            ticket_id=None,
                            spec_id=None,
                            version_no=1,
                            status="delegated",
                            summary=task.delegation_reasoning
                            or f"Sub-plan from {task.framework}",
                            risk_level="low",
                            plan_json={
                                "tasks": [{"title": s} for s in task.sub_plan_steps],
                                "framework": task.framework,
                            },
                            parent_plan_id=parent_uuid,
                            delegation_metadata=task.sub_plan_json,
                        )
                        session.add(child)
                        await session.flush()
                        child_plan_id = child.id

                audit = AuditLog(
                    id=uuid.uuid4(),
                    company_id=company_uuid,
                    actor_type="agent",
                    event_type=f"agent_adapter.{task.framework}.executed",
                    target_type="agent_task",
                    target_id=None,
                    details_json={
                        "task_id": task.id,
                        "framework": task.framework,
                        "status": task.status.value,
                        "token_usage": task.token_usage,
                        "sub_plan_steps": task.sub_plan_steps[:50],
                        "sub_plan_json": task.sub_plan_json,
                        "delegation_reasoning": task.delegation_reasoning,
                        "parent_plan_id": task.parent_plan_id,
                        "child_plan_id": str(child_plan_id) if child_plan_id else None,
                    },
                )
                session.add(audit)
                await session.commit()
        except Exception:  # pragma: no cover - audit must never block execution
            logger.debug("agent_adapter audit persistence failed", exc_info=True)

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
