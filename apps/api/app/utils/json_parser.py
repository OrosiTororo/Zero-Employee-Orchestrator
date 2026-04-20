"""Safe JSON extraction from LLM responses.

LLMs frequently wrap structured output in ```json ... ``` fenced blocks, but
may omit the fence or prepend free-form prose. ``safe_extract_json`` handles
both cases: it prefers a fenced block, falls back to a bare JSON value, and
returns ``None`` instead of raising on malformed input so callers can log and
degrade gracefully.
"""

from __future__ import annotations

import json
import re
from typing import Any

_FENCED_JSON_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)


def safe_extract_json(text: str | None) -> Any | None:
    """Extract a JSON value from ``text``.

    Returns the parsed Python value (dict / list / scalar) on success, or
    ``None`` if no valid JSON payload could be located. Does not raise.
    """
    if not text:
        return None

    fenced = _FENCED_JSON_RE.search(text)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass  # fall through to bare-parse

    stripped = text.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return None

    return None
