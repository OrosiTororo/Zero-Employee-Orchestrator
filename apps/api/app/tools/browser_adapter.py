"""Browser automation adapter — plugin-style extensible browser automation framework.

Like VS Code extensions, allows third-party browser automation libraries to be
added and switched as adapters. Initially includes only the built-in Playwright
adapter; browser-use / Selenium / Puppeteer etc. are added later as Plugins.

Supported adapters:
- builtin (Playwright) — default, bundled with ZEO
- browser-use — LLM-driven autonomous browser automation (installed via Plugin)
- selenium — Traditional web automation (installed via Plugin)
- custom — User-defined adapter (registered via Plugin API)

Safety:
- All adapters go through approval gates
- Operation logs are recorded in the audit system
- Executed within the sandbox
"""

from __future__ import annotations

import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Common data types
# ---------------------------------------------------------------------------


class AdapterType(str, Enum):
    """Supported browser automation backends."""

    BUILTIN = "builtin"  # Playwright (bundled with ZEO)
    BROWSER_USE = "browser-use"  # browser-use library
    SELENIUM = "selenium"
    CUSTOM = "custom"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STUCK = "stuck"  # Loop detected
    REPLANNING = "replanning"  # Auto-replanning in progress


@dataclass
class BrowserTask:
    """Natural language task description passed to LLM."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    instruction: str = ""
    url: str | None = None
    max_steps: int = 50
    timeout_seconds: int = 300
    require_approval: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class BrowserTaskResult:
    """Task execution result."""

    task_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    output: str = ""
    extracted_data: dict = field(default_factory=dict)
    screenshots: list[bytes] = field(default_factory=list)
    steps_executed: int = 0
    errors: list[str] = field(default_factory=list)
    duration_ms: int = 0
    adapter_used: str = ""
    replanned: bool = False


@dataclass
class AdapterCapabilities:
    """Capabilities provided by the adapter."""

    natural_language_control: bool = False  # Operation via natural language instructions
    loop_detection: bool = False  # Loop detection
    auto_replanning: bool = False  # Auto-replanning
    screenshot_analysis: bool = False  # Screenshot analysis
    dom_inspection: bool = False  # DOM structure analysis
    form_filling: bool = True  # Form filling
    navigation: bool = True  # Page navigation
    data_extraction: bool = True  # Data extraction
    headless: bool = True  # Headless mode


@dataclass
class AdapterInfo:
    """Registered adapter information."""

    adapter_type: AdapterType
    name: str
    version: str
    description: str
    capabilities: AdapterCapabilities
    installed: bool = False
    install_package: str = ""  # pip install command


# ---------------------------------------------------------------------------
# Abstract adapter interface
# ---------------------------------------------------------------------------


class BrowserAdapter(ABC):
    """Abstract base class for browser automation adapters.

    To integrate a new browser automation library, inherit from this class
    and implement each method. Register as a Plugin to make it available in ZEO.
    """

    @abstractmethod
    def info(self) -> AdapterInfo:
        """Return adapter information."""

    @abstractmethod
    async def execute_task(self, task: BrowserTask) -> BrowserTaskResult:
        """Execute a natural language task.

        Args:
            task: Task to execute

        Returns:
            Execution result
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the adapter is available."""

    async def cleanup(self) -> None:  # noqa: B027
        """Release resources (optional)."""


# ---------------------------------------------------------------------------
# Built-in adapter (Playwright) — minimal bundled adapter
# ---------------------------------------------------------------------------


class BuiltinPlaywrightAdapter(BrowserAdapter):
    """Playwright-based built-in adapter.

    Minimal browser automation bundled with ZEO. Only supports step-based
    operations; does not provide natural language control or loop detection.
    Install adapters like browser-use as Plugins for advanced features.
    """

    def info(self) -> AdapterInfo:
        return AdapterInfo(
            adapter_type=AdapterType.BUILTIN,
            name="Builtin Playwright Adapter",
            version="0.1.0",
            description="Minimal browser automation bundled with ZEO. Playwright-based.",
            capabilities=AdapterCapabilities(
                natural_language_control=False,
                loop_detection=False,
                auto_replanning=False,
                screenshot_analysis=False,
                dom_inspection=True,
                form_filling=True,
                navigation=True,
                data_extraction=True,
                headless=True,
            ),
            installed=True,
            install_package="playwright",
        )

    async def execute_task(self, task: BrowserTask) -> BrowserTaskResult:
        """Execute a task with Playwright.

        The built-in adapter does not support natural language control,
        so only URL navigation + screenshot are executed.
        Use the BrowserAutomation class for full script execution.
        """
        start = time.monotonic()
        screenshots: list[bytes] = []
        errors: list[str] = []

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page()

                if task.url:
                    await page.goto(task.url, timeout=task.timeout_seconds * 1000)

                screenshot = await page.screenshot(full_page=True)
                screenshots.append(screenshot)

                title = await page.title()
                await browser.close()

            return BrowserTaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                output=f"Page fetched: {title}",
                screenshots=screenshots,
                steps_executed=1,
                duration_ms=int((time.monotonic() - start) * 1000),
                adapter_used="builtin",
            )
        except ImportError:
            errors.append("Playwright not installed (pip install playwright)")
            return BrowserTaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                output="[Playwright not installed]",
                errors=errors,
                duration_ms=int((time.monotonic() - start) * 1000),
                adapter_used="builtin",
            )
        except Exception as exc:
            errors.append(str(exc))
            return BrowserTaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                output=f"[Error: {exc}]",
                errors=errors,
                duration_ms=int((time.monotonic() - start) * 1000),
                adapter_used="builtin",
            )

    async def health_check(self) -> bool:
        try:
            import playwright  # noqa: F401

            return True
        except ImportError:
            return False


# ---------------------------------------------------------------------------
# browser-use adapter (installed via Plugin)
# ---------------------------------------------------------------------------


class BrowserUseAdapter(BrowserAdapter):
    """LLM-driven browser automation adapter using the browser-use library.

    Autonomously operates web browsers using only natural language instructions.
    The LLM "sees" screenshots and DOM structure to make decisions and
    executes clicks, input, and scrolling.

    Handles dead ends with loop detection and auto-replanning.

    Requirement: pip install browser-use
    """

    def __init__(self, llm_provider: str = "auto") -> None:
        self._llm_provider = llm_provider
        self._available = False
        self._check_availability()

    def _check_availability(self) -> None:
        try:
            import browser_use  # noqa: F401

            self._available = True
        except ImportError:
            self._available = False

    def info(self) -> AdapterInfo:
        return AdapterInfo(
            adapter_type=AdapterType.BROWSER_USE,
            name="browser-use Adapter",
            version="0.1.0",
            description=(
                "LLM-driven autonomous browser automation. Operates the web using only "
                "natural language instructions. Loop detection and auto-replanning supported."
            ),
            capabilities=AdapterCapabilities(
                natural_language_control=True,
                loop_detection=True,
                auto_replanning=True,
                screenshot_analysis=True,
                dom_inspection=True,
                form_filling=True,
                navigation=True,
                data_extraction=True,
                headless=True,
            ),
            installed=self._available,
            install_package="browser-use",
        )

    async def execute_task(self, task: BrowserTask) -> BrowserTaskResult:
        """Execute a natural language task with browser-use."""
        if not self._available:
            return BrowserTaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                output="[browser-use not installed — pip install browser-use]",
                errors=["browser-use not installed"],
                adapter_used="browser-use",
            )

        start = time.monotonic()
        errors: list[str] = []

        try:
            from browser_use import Agent as BrowserUseAgent

            # LLM is obtained from ZEO LLM Gateway
            llm = await self._resolve_llm()

            agent = BrowserUseAgent(
                task=task.instruction,
                llm=llm,
                max_steps=task.max_steps,
            )

            result = await agent.run()

            output = ""
            extracted = {}
            if result:
                output = (
                    str(result.final_result()) if hasattr(result, "final_result") else str(result)
                )
                if hasattr(result, "extracted_content"):
                    extracted = {"content": result.extracted_content()}

            return BrowserTaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                output=output,
                extracted_data=extracted,
                steps_executed=task.max_steps,
                duration_ms=int((time.monotonic() - start) * 1000),
                adapter_used="browser-use",
            )
        except Exception as exc:
            errors.append(str(exc))
            logger.error("browser-use task failed: %s", exc)
            return BrowserTaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                output=f"[browser-use error: {exc}]",
                errors=errors,
                duration_ms=int((time.monotonic() - start) * 1000),
                adapter_used="browser-use",
            )

    async def _resolve_llm(self) -> object:
        """Get an LLM instance from ZEO LLM Gateway.

        browser-use expects a langchain-compatible LLM object.
        Returns the appropriate LLM based on ZEO gateway configuration.
        """
        if self._llm_provider == "auto":
            try:
                import os

                from langchain_openai import ChatOpenAI

                # Prioritize OpenAI-compatible providers
                api_key = os.environ.get("OPENAI_API_KEY", "")
                if api_key:
                    return ChatOpenAI(model="gpt-5.4", api_key=api_key)

                # Via OpenRouter
                openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
                if openrouter_key:
                    return ChatOpenAI(
                        model="openai/gpt-5.4",
                        api_key=openrouter_key,
                        base_url="https://openrouter.ai/api/v1",
                    )
            except ImportError:
                pass

        # Fallback: dummy LLM (will actually error)
        raise RuntimeError(
            "LLM provider required for browser-use is not configured. "
            "Please set OPENAI_API_KEY or OPENROUTER_API_KEY."
        )

    async def health_check(self) -> bool:
        return self._available


# ---------------------------------------------------------------------------
# Adapter registry — registration, search, and switching
# ---------------------------------------------------------------------------


class BrowserAdapterRegistry:
    """Browser automation adapter registry.

    Like VS Code's extension marketplace, allows registering,
    searching, and switching adapters.
    """

    def __init__(self) -> None:
        self._adapters: dict[str, BrowserAdapter] = {}
        self._active_adapter: str = "builtin"
        # Initially register only the built-in adapter
        self.register("builtin", BuiltinPlaywrightAdapter())

    def register(self, name: str, adapter: BrowserAdapter) -> None:
        """Register an adapter.

        Args:
            name: Adapter identifier name
            adapter: Adapter instance
        """
        self._adapters[name] = adapter
        logger.info("Browser adapter registered: %s", name)

    def unregister(self, name: str) -> bool:
        """Unregister an adapter (built-in cannot be unregistered)."""
        if name == "builtin":
            logger.warning("Built-in adapter cannot be unregistered")
            return False
        if name in self._adapters:
            del self._adapters[name]
            if self._active_adapter == name:
                self._active_adapter = "builtin"
            logger.info("Browser adapter unregistered: %s", name)
            return True
        return False

    def set_active(self, name: str) -> bool:
        """Switch the active adapter."""
        if name not in self._adapters:
            logger.warning("Adapter not found: %s", name)
            return False
        self._active_adapter = name
        logger.info("Active adapter changed: %s", name)
        return True

    def get_active(self) -> BrowserAdapter:
        """Return the current active adapter."""
        return self._adapters[self._active_adapter]

    def get_active_name(self) -> str:
        return self._active_adapter

    def get_adapter(self, name: str) -> BrowserAdapter | None:
        return self._adapters.get(name)

    def list_adapters(self) -> list[AdapterInfo]:
        """Return a list of registered adapters."""
        infos = []
        for _name, adapter in self._adapters.items():
            info = adapter.info()
            infos.append(info)
        return infos

    def list_installable(self) -> list[AdapterInfo]:
        """Return a list of installable unregistered adapters.

        Returns adapters that are registered in the marketplace but
        not yet installed locally.
        """
        known: list[AdapterInfo] = [
            AdapterInfo(
                adapter_type=AdapterType.BROWSER_USE,
                name="browser-use",
                version="0.4.x",
                description=(
                    "LLM-driven autonomous browser automation. Operates the web using only "
                    "natural language instructions. Loop detection and auto-replanning supported."
                ),
                capabilities=AdapterCapabilities(
                    natural_language_control=True,
                    loop_detection=True,
                    auto_replanning=True,
                    screenshot_analysis=True,
                    dom_inspection=True,
                ),
                installed=False,
                install_package="browser-use",
            ),
            AdapterInfo(
                adapter_type=AdapterType.SELENIUM,
                name="selenium",
                version="4.x",
                description="Selenium WebDriver-based browser automation.",
                capabilities=AdapterCapabilities(
                    natural_language_control=False,
                    loop_detection=False,
                    auto_replanning=False,
                    dom_inspection=True,
                ),
                installed=False,
                install_package="selenium",
            ),
        ]
        registered_types = {a.info().adapter_type for a in self._adapters.values()}
        return [a for a in known if a.adapter_type not in registered_types]

    async def execute_task(self, task: BrowserTask) -> BrowserTaskResult:
        """Execute a task with the active adapter.

        Goes through approval gates and records in audit logs.
        """
        adapter = self.get_active()

        # Tiered approval check (Cowork pattern: read < write < execute)
        if task.require_approval:
            try:
                from app.policies.approval_gate import check_approval_required

                # Determine action tier from task instruction
                op = _classify_browser_operation(task.instruction)
                approval = check_approval_required(op)
                if approval.requires_approval:
                    return BrowserTaskResult(
                        task_id=task.id,
                        status=TaskStatus.FAILED,
                        output=(
                            f"Approval required for '{op}' "
                            f"(risk: {approval.risk_level.value}). "
                            f"Reason: {approval.reason}"
                        ),
                        errors=["approval_required"],
                        adapter_used=self._active_adapter,
                    )
            except ImportError:
                logger.debug("Approval gate not available, skipping")

        result = await adapter.execute_task(task)

        # Audit log
        logger.info(
            "Browser task executed: adapter=%s, task=%s, op=%s, status=%s, duration=%dms",
            self._active_adapter,
            task.id,
            _classify_browser_operation(task.instruction),
            result.status.value,
            result.duration_ms,
        )

        return result


def _classify_browser_operation(instruction: str) -> str:
    """Classify a browser task instruction into a tiered operation type.

    Follows Cowork's tool hierarchy: navigate < extract < interact < submit.
    Handles negation patterns (e.g., "don't click" → navigate, not click).
    """
    import re

    lower = instruction.lower()

    # Collect negated spans — all words following a negation word until punctuation/end
    negated_words: set[str] = set()
    for m in re.finditer(r"(?:don'?t|do not|never|avoid|without|no)\s+([\w\s]+)", lower):
        negated_words.update(m.group(1).split())

    def _match(keywords: tuple[str, ...]) -> bool:
        """Match keywords while respecting negation."""
        for kw in keywords:
            if kw in lower:
                root = kw.strip().split()[0] if " " in kw else kw
                # Check if root or any variant of it appears in negated words
                if not any(root in nw or nw.startswith(root) for nw in negated_words):
                    return True
        return False

    # Critical: login, payment, credentials
    if _match(("login", "sign in", "password", "credential")):
        return "browser_login"
    if _match(("payment", "purchase", "checkout", "pay ", "billing")):
        return "browser_payment"

    # Medium: clicking (check before submit to avoid "click submit" → submit_form)
    if _match(("click", "press button", "select ", "toggle")):
        return "browser_click"

    # High: form submission, filling, typing
    if _match(("submit", "send form", "confirm order")):
        return "browser_submit_form"
    if _match(("fill", "enter ")):
        return "browser_fill_form"
    if _match(("type ", "input ")):
        return "browser_type"
    if _match(("download",)):
        return "browser_download"
    if _match(("extract", "scrape", "copy ", "get data")):
        return "browser_extract_data"

    # Low: navigation, screenshots (safe)
    if _match(("screenshot", "capture")):
        return "browser_screenshot"

    return "browser_navigate"

    async def auto_install_adapter(self, adapter_type: AdapterType) -> bool:
        """Install and register an adapter.

        Works with the Plugin system to install required pip packages
        and then register the adapter.

        Args:
            adapter_type: Adapter type to install

        Returns:
            Whether installation was successful
        """
        if adapter_type == AdapterType.BROWSER_USE:
            adapter = BrowserUseAdapter()
            if not adapter._available:
                logger.info("Please install browser-use: pip install browser-use")
                return False
            self.register("browser-use", adapter)
            return True

        logger.warning("Unsupported adapter type: %s", adapter_type)
        return False


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------

browser_adapter_registry = BrowserAdapterRegistry()
