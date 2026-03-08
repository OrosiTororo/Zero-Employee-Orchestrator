"""Event Dispatcher - Routes internal events to appropriate handlers.

Handles events like:
- Task completion -> trigger dependent tasks
- Approval granted -> resume blocked tasks
- Budget threshold reached -> pause agents
- Heartbeat completed -> update agent status
- External webhook received -> create ticket or trigger task
"""

import asyncio
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class InternalEvent:
    event_type: str
    source: str
    target_type: str | None = None
    target_id: str | None = None
    company_id: str | None = None
    data: dict | None = None


class EventDispatcher:
    """Dispatches internal events to registered handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, list] = {}

    def register(self, event_type: str, handler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def dispatch(self, event: InternalEvent) -> None:
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler error for {event.event_type}: {e}")

    async def run(self, shutdown_event: asyncio.Event) -> None:
        """Run event dispatcher loop."""
        logger.info("EventDispatcher started")
        while not shutdown_event.is_set():
            # In production, consume from event queue (Redis, etc.)
            await asyncio.sleep(10)
        logger.info("EventDispatcher stopped")
