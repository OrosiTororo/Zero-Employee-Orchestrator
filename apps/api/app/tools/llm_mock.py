"""LLM response mocking — LLM response simulation for testing.

Mocks LLM calls in test/development environments and returns fixed responses.
Supports rule-based response generation via pattern matching, and
call history recording and assertions.

Must be disabled in production environments.
"""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MockRule:
    """Mock rule — fixed response for a prompt pattern.

    Attributes
    ----------
    pattern: Regex pattern to match against prompts
    response: Fixed response string to return on match
    latency_ms: Response delay (milliseconds). Simulates realistic latency
    model_filter: Filter to apply only to specific models (None targets all models)
    """

    pattern: str
    response: str
    latency_ms: int = 0
    model_filter: str | None = None


@dataclass
class MockCallRecord:
    """Mock call record."""

    prompt: str
    model: str
    response: dict[str, Any]
    matched_rule: MockRule | None
    timestamp: str = ""
    mock_id: str = ""


class LLMMockProvider:
    """LLM response mock provider.

    Intercepts LLM calls during testing and returns rule-based
    fixed responses. Records call history for use in assertions.
    """

    def __init__(self) -> None:
        self._rules: list[MockRule] = []
        self._enabled: bool = False
        self._call_history: list[MockCallRecord] = []

    def add_rule(self, rule: MockRule) -> int:
        """Add a mock rule.

        Returns
        -------
        int
            Index of the added rule
        """
        self._rules.append(rule)
        logger.info(
            "Mock rule added: pattern=%r, model_filter=%s",
            rule.pattern,
            rule.model_filter,
        )
        return len(self._rules) - 1

    def remove_rule(self, index: int) -> bool:
        """Remove the mock rule at the specified index."""
        if 0 <= index < len(self._rules):
            removed = self._rules.pop(index)
            logger.info("Mock rule removed: pattern=%r", removed.pattern)
            return True
        return False

    def clear_rules(self) -> None:
        """Clear all mock rules."""
        count = len(self._rules)
        self._rules.clear()
        logger.info("All mock rules cleared (%d rules)", count)

    def enable(self) -> None:
        """Enable the mock provider."""
        self._enabled = True
        logger.info("LLM mock provider enabled")

    def disable(self) -> None:
        """Disable the mock provider."""
        self._enabled = False
        logger.info("LLM mock provider disabled")

    def is_enabled(self) -> bool:
        """Return whether the mock provider is enabled."""
        return self._enabled

    def match(self, prompt: str, model: str = "") -> MockRule | None:
        """Search for a rule matching the prompt and model.

        Rules are evaluated in registration order; the first match is returned.
        """
        for rule in self._rules:
            # Check model filter
            if rule.model_filter and model:
                if rule.model_filter not in model:
                    continue

            # Pattern match
            try:
                if re.search(rule.pattern, prompt, re.IGNORECASE | re.DOTALL):
                    return rule
            except re.error as exc:
                logger.warning(
                    "Invalid regex pattern in mock rule: %r — %s",
                    rule.pattern,
                    exc,
                )
                continue

        return None

    async def generate_mock_response(self, prompt: str, model: str = "") -> dict[str, Any]:
        """Generate a mock LLM response.

        Returns the matching rule response if found, otherwise a default mock.
        Return format is LiteLLM-compatible standard format.
        """
        rule = self.match(prompt, model)
        response_text = (
            rule.response if rule else f"[MOCK] No matching rule for prompt (model={model})"
        )

        # Simulate latency
        if rule and rule.latency_ms > 0:
            await asyncio.sleep(rule.latency_ms / 1000.0)

        mock_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        response = {
            "id": f"mock-{mock_id}",
            "object": "chat.completion",
            "created": int(datetime.now(UTC).timestamp()),
            "model": model or "mock-model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(prompt.split()) + len(response_text.split()),
            },
            "_mock": True,
            "_mock_id": mock_id,
            "_matched_rule": rule.pattern if rule else None,
        }

        # Call recording
        self.record_call(prompt, model, response, rule, now, mock_id)

        return response

    def record_call(
        self,
        prompt: str,
        model: str,
        response: dict[str, Any],
        matched_rule: MockRule | None = None,
        timestamp: str = "",
        mock_id: str = "",
    ) -> None:
        """Record a call in history."""
        record = MockCallRecord(
            prompt=prompt,
            model=model,
            response=response,
            matched_rule=matched_rule,
            timestamp=timestamp or datetime.now(UTC).isoformat(),
            mock_id=mock_id or str(uuid.uuid4()),
        )
        self._call_history.append(record)

    def get_call_history(self, limit: int = 0) -> list[MockCallRecord]:
        """Return call history.

        Parameters
        ----------
        limit: Maximum number of entries to return (0 = all)
        """
        if limit > 0:
            return self._call_history[-limit:]
        return list(self._call_history)

    def clear_history(self) -> None:
        """Clear call history."""
        self._call_history.clear()

    def assert_called_with(self, pattern: str) -> bool:
        """Verify whether a call was made with a prompt matching the specified pattern.

        Used for test assertions.
        """
        try:
            compiled = re.compile(pattern, re.IGNORECASE | re.DOTALL)
        except re.error:
            logger.warning("Invalid assertion pattern: %r", pattern)
            return False

        return any(compiled.search(record.prompt) for record in self._call_history)

    def assert_call_count(self, expected: int) -> bool:
        """Verify whether the call count matches the expected value."""
        return len(self._call_history) == expected

    def assert_model_used(self, model: str) -> bool:
        """Verify whether the specified model was used."""
        return any(model in record.model for record in self._call_history)

    def get_summary(self) -> dict[str, Any]:
        """Return a summary of the mock provider."""
        return {
            "enabled": self._enabled,
            "rules_count": len(self._rules),
            "call_count": len(self._call_history),
            "rules": [
                {
                    "pattern": r.pattern,
                    "response_preview": r.response[:80],
                    "latency_ms": r.latency_ms,
                    "model_filter": r.model_filter,
                }
                for r in self._rules
            ],
        }


# Global instance
llm_mock = LLMMockProvider()
