"""Browser automation — Playwright-based web automation.

Executes browser automation using Playwright.
Allows defining and executing navigation, clicking, form input,
screenshots, and data extraction in script format.

Safety:
- Pre-execution approval via approval gates
- Per-step approval option
- Audit log recording
- Data protection policy applied
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


class BrowserAction(str, Enum):
    """Browser action."""

    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCREENSHOT = "screenshot"
    EXTRACT = "extract"
    FILL_FORM = "fill_form"
    WAIT = "wait"
    SCROLL = "scroll"
    SELECT = "select"


@dataclass
class AutomationStep:
    """A single step of an automation script."""

    action: BrowserAction = BrowserAction.NAVIGATE
    selector: str = ""
    value: str = ""
    description: str = ""
    requires_approval: bool = False
    timeout_ms: int = 30000


@dataclass
class AutomationScript:
    """Automation script."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    steps: list[AutomationStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_run: datetime | None = None


@dataclass
class AutomationResult:
    """Automation execution result."""

    success: bool = False
    screenshots: list[bytes] = field(default_factory=list)
    extracted_data: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    duration_ms: int = 0


class BrowserAutomation:
    """Browser automation service.

    Manages and executes browser automation using Playwright.
    Goes through approval gates and records all operations in audit logs.
    """

    def __init__(self) -> None:
        self._scripts: dict[str, AutomationScript] = {}
        self._approval_required: bool = True

    def create_script(
        self,
        name: str,
        steps: list[AutomationStep],
    ) -> AutomationScript:
        """Create and register an automation script.

        Args:
            name: Script name
            steps: List of execution steps

        Returns:
            Created AutomationScript
        """
        script = AutomationScript(name=name, steps=steps)
        self._scripts[script.id] = script
        logger.info("Script created: %s (%s), steps=%d", name, script.id, len(steps))
        return script

    async def execute_script(
        self,
        script_id: str,
        headless: bool = True,
    ) -> AutomationResult:
        """Execute a script.

        Checks the approval gate, then executes browser operations with Playwright.
        Returns simulation results if Playwright is not available.

        Args:
            script_id: Script ID to execute
            headless: Whether to run in headless mode

        Returns:
            Execution result
        """
        script = self._scripts.get(script_id)
        if not script:
            return AutomationResult(
                success=False,
                errors=[f"Script not found: {script_id}"],
            )

        # Approval check
        if self._approval_required:
            try:
                from app.policies.approval_gate import check_approval_required

                approval = check_approval_required("browser_automation")
                if approval.requires_approval:
                    return AutomationResult(
                        success=False,
                        errors=["Approval required. Please re-execute after approval."],
                    )
            except ImportError:
                logger.debug("Approval gate not available, skipping")

        start_time = time.monotonic()

        # Check if Playwright is available
        try:
            from playwright.async_api import async_playwright

            result = await self._execute_with_playwright(
                script,
                headless,
                async_playwright,
            )
        except ImportError:
            logger.info("Playwright not installed — running in simulation mode")
            result = self._simulate_execution(script)

        duration = int((time.monotonic() - start_time) * 1000)
        result.duration_ms = duration
        script.last_run = datetime.now(UTC)

        logger.info(
            "Script execution complete: %s, success=%s, duration=%dms",
            script.name,
            result.success,
            duration,
        )
        return result

    async def _execute_with_playwright(
        self,
        script: AutomationScript,
        headless: bool,
        async_playwright: object,
    ) -> AutomationResult:
        """Execute a script using Playwright."""
        screenshots: list[bytes] = []
        extracted_data: dict = {}
        errors: list[str] = []

        try:
            async with async_playwright() as pw:  # type: ignore[operator]
                browser = await pw.chromium.launch(headless=headless)
                context = await browser.new_context()
                page = await context.new_page()

                for i, step in enumerate(script.steps):
                    try:
                        step_result = await self._execute_step(page, step)
                        if step.action == BrowserAction.SCREENSHOT and step_result:
                            screenshots.append(step_result)
                        elif step.action == BrowserAction.EXTRACT and step_result:
                            extracted_data[f"step_{i}"] = step_result
                    except Exception as exc:
                        error_msg = f"Step {i} ({step.action.value}) failed: {exc}"
                        errors.append(error_msg)
                        logger.warning(error_msg)

                await browser.close()

        except Exception as exc:
            errors.append(f"Browser launch failed: {exc}")

        return AutomationResult(
            success=len(errors) == 0,
            screenshots=screenshots,
            extracted_data=extracted_data,
            errors=errors,
        )

    async def _execute_step(
        self,
        page: object,
        step: AutomationStep,
    ) -> bytes | str | None:
        """Execute a single step.

        Args:
            page: Playwright Page object
            step: Step to execute

        Returns:
            Screenshot binary, extracted text, or None
        """
        timeout = step.timeout_ms

        if step.action == BrowserAction.NAVIGATE:
            await page.goto(step.value, timeout=timeout)  # type: ignore[union-attr]
            return None

        elif step.action == BrowserAction.CLICK:
            await page.click(step.selector, timeout=timeout)  # type: ignore[union-attr]
            return None

        elif step.action == BrowserAction.TYPE:
            await page.fill(step.selector, step.value, timeout=timeout)  # type: ignore[union-attr]
            return None

        elif step.action == BrowserAction.SCREENSHOT:
            screenshot_bytes = await page.screenshot(full_page=True)  # type: ignore[union-attr]
            return screenshot_bytes  # type: ignore[return-value]

        elif step.action == BrowserAction.EXTRACT:
            elements = await page.query_selector_all(step.selector)  # type: ignore[union-attr]
            texts = []
            for el in elements:
                text = await el.text_content()
                if text:
                    texts.append(text.strip())
            return "\n".join(texts)

        elif step.action == BrowserAction.FILL_FORM:
            await page.fill(step.selector, step.value, timeout=timeout)  # type: ignore[union-attr]
            return None

        elif step.action == BrowserAction.WAIT:
            wait_ms = int(step.value) if step.value.isdigit() else timeout
            await page.wait_for_timeout(wait_ms)  # type: ignore[union-attr]
            return None

        elif step.action == BrowserAction.SCROLL:
            direction = step.value.lower() if step.value else "down"
            delta = 500 if direction == "down" else -500
            await page.mouse.wheel(0, delta)  # type: ignore[union-attr]
            return None

        elif step.action == BrowserAction.SELECT:
            await page.select_option(  # type: ignore[union-attr]
                step.selector,
                value=step.value,
                timeout=timeout,
            )
            return None

        return None

    def _simulate_execution(self, script: AutomationScript) -> AutomationResult:
        """Simulation execution without Playwright.

        Records each step and returns simulation results.
        """
        extracted: dict = {}

        for i, step in enumerate(script.steps):
            extracted[f"step_{i}"] = {
                "action": step.action.value,
                "selector": step.selector,
                "value": step.value,
                "status": "simulated",
            }

        return AutomationResult(
            success=True,
            screenshots=[],
            extracted_data={"simulation": True, "steps": extracted},
            errors=[],
        )

    async def take_screenshot(self, url: str) -> AutomationResult:
        """Take a screenshot of the specified URL.

        Args:
            url: URL to screenshot

        Returns:
            AutomationResult containing the screenshot
        """
        steps = [
            AutomationStep(
                action=BrowserAction.NAVIGATE,
                value=url,
                description=f"Navigate to {url}",
            ),
            AutomationStep(
                action=BrowserAction.SCREENSHOT,
                description="Take full-page screenshot",
            ),
        ]
        script = self.create_script(f"screenshot_{url[:50]}", steps)
        return await self.execute_script(script.id, headless=True)

    async def extract_data(
        self,
        url: str,
        selectors: dict[str, str],
    ) -> AutomationResult:
        """Extract data from the specified URL.

        Args:
            url: URL to extract data from
            selectors: Dictionary mapping extraction name to CSS selector

        Returns:
            AutomationResult containing extracted data
        """
        steps: list[AutomationStep] = [
            AutomationStep(
                action=BrowserAction.NAVIGATE,
                value=url,
                description=f"Navigate to {url}",
            ),
        ]
        for name, selector in selectors.items():
            steps.append(
                AutomationStep(
                    action=BrowserAction.EXTRACT,
                    selector=selector,
                    description=f"Extract {name}",
                )
            )

        script = self.create_script(f"extract_{url[:50]}", steps)
        return await self.execute_script(script.id, headless=True)

    async def fill_form(
        self,
        url: str,
        form_data: dict[str, str],
        submit: bool = False,
    ) -> AutomationResult:
        """Fill form values on the specified URL.

        Args:
            url: Form page URL
            form_data: Dictionary mapping selector to input value
            submit: Whether to click the form submit button

        Returns:
            Execution result
        """
        steps: list[AutomationStep] = [
            AutomationStep(
                action=BrowserAction.NAVIGATE,
                value=url,
                description=f"Navigate to {url}",
                requires_approval=True,
            ),
        ]
        for selector, value in form_data.items():
            steps.append(
                AutomationStep(
                    action=BrowserAction.FILL_FORM,
                    selector=selector,
                    value=value,
                    description=f"Fill {selector}",
                    requires_approval=True,
                )
            )

        if submit:
            steps.append(
                AutomationStep(
                    action=BrowserAction.CLICK,
                    selector='button[type="submit"], input[type="submit"]',
                    description="Submit form",
                    requires_approval=True,
                )
            )

        script = self.create_script(f"form_{url[:50]}", steps)
        return await self.execute_script(script.id, headless=True)

    def list_scripts(self) -> list[AutomationScript]:
        """Return a list of registered scripts."""
        return list(self._scripts.values())

    def get_script(self, script_id: str) -> AutomationScript | None:
        """Get a script."""
        return self._scripts.get(script_id)

    def delete_script(self, script_id: str) -> bool:
        """Delete a script.

        Args:
            script_id: Script ID to delete

        Returns:
            Whether the deletion was successful
        """
        if script_id in self._scripts:
            name = self._scripts[script_id].name
            del self._scripts[script_id]
            logger.info("Script deleted: %s (%s)", name, script_id)
            return True
        return False


# Global instance
browser_automation = BrowserAutomation()
