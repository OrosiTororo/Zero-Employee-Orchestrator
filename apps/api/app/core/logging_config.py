"""Structured logging configuration.

Provides JSON-format log output for production and human-readable output
for development.  Automatically injects ``request_id`` from the current
request context when available.

Usage::

    from app.core.logging_config import configure_logging

    configure_logging(json_format=not settings.DEBUG)

Individual modules continue to use ``logging.getLogger(__name__)`` as
normal — the structured formatter enriches all log records automatically.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

# Context variables set by RequestIDMiddleware
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
user_id_var: ContextVar[str] = ContextVar("user_id", default="-")


class StructuredFormatter(logging.Formatter):
    """JSON log formatter that includes request_id and user_id context."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import UTC, datetime

        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get("-"),
            "user_id": user_id_var.get("-"),
        }
        if record.exc_info and record.exc_info[1]:
            entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            entry["extra"] = record.extra_data
        return json.dumps(entry, ensure_ascii=False)


class ReadableFormatter(logging.Formatter):
    """Human-readable formatter for development that includes request context."""

    def format(self, record: logging.LogRecord) -> str:
        rid = request_id_var.get("-")
        prefix = f"[{rid[:8]}]" if rid != "-" else ""
        base = super().format(record)
        return f"{prefix} {base}" if prefix else base


def configure_logging(*, json_format: bool = False, level: str = "INFO") -> None:
    """Configure the root logger with structured or readable output.

    Args:
        json_format: Use JSON output (production). False = human-readable (dev).
        level: Root log level.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates on re-init
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stderr)
    if json_format:
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(
            ReadableFormatter(
                fmt="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
                datefmt="%H:%M:%S",
            )
        )

    root.addHandler(handler)

    # Suppress noisy third-party loggers
    for noisy in ("httpcore", "httpx", "hpack", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
