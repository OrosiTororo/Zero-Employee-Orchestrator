"""WebSocket endpoint for real-time event streaming.

Events: ticket.updated, task.updated, approval.requested,
heartbeat.finished, cost.threshold_reached, etc.
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections, grouped by company."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, company_id: str) -> None:
        await websocket.accept()
        if company_id not in self._connections:
            self._connections[company_id] = []
        self._connections[company_id].append(websocket)
        logger.info(f"WebSocket connected for company {company_id}")

    def disconnect(self, websocket: WebSocket, company_id: str) -> None:
        if company_id in self._connections:
            self._connections[company_id] = [
                ws for ws in self._connections[company_id] if ws != websocket
            ]
        logger.info(f"WebSocket disconnected for company {company_id}")

    async def broadcast(self, company_id: str, event: dict[str, Any]) -> None:
        """Send event to all connections for a company."""
        if company_id not in self._connections:
            return
        message = json.dumps(event, default=str)
        disconnected = []
        for ws in self._connections[company_id]:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws, company_id)

    async def broadcast_all(self, event: dict[str, Any]) -> None:
        """Send event to all connected clients."""
        for company_id in list(self._connections.keys()):
            await self.broadcast(company_id, event)


# Global connection manager
manager = ConnectionManager()


async def emit_event(
    company_id: str,
    event_type: str,
    target_type: str | None = None,
    target_id: str | None = None,
    data: dict | None = None,
) -> None:
    """Helper to emit a WebSocket event."""
    await manager.broadcast(
        company_id,
        {
            "event_type": event_type,
            "target_type": target_type,
            "target_id": str(target_id) if target_id else None,
            "data": data or {},
        },
    )


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming and user-agent interaction.

    Client should send initial message with company_id to subscribe.

    Supported client message types:
    - ping: keep-alive heartbeat
    - user_message: send a message to an agent (requires agent_id, content)
    - approval_response: respond to an approval request (requires approval_id, decision)
    - intervention: interrupt or redirect an agent task
    """
    company_id = websocket.query_params.get("company_id", "default")
    await manager.connect(websocket, company_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "")

                if msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

                elif msg_type == "user_message":
                    # User sends a message to a specific agent
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "message_received",
                                "agent_id": msg.get("agent_id"),
                                "content": msg.get("content", ""),
                                "status": "delivered",
                            }
                        )
                    )
                    # Broadcast to other listeners so agent workers can pick it up
                    await manager.broadcast(
                        company_id,
                        {
                            "event_type": "user.message",
                            "target_type": "agent",
                            "target_id": msg.get("agent_id"),
                            "data": {
                                "content": msg.get("content", ""),
                                "ticket_id": msg.get("ticket_id"),
                                "task_id": msg.get("task_id"),
                            },
                        },
                    )

                elif msg_type == "approval_response":
                    # User responds to an approval request via WebSocket
                    await manager.broadcast(
                        company_id,
                        {
                            "event_type": "approval.decided",
                            "target_type": "approval",
                            "target_id": msg.get("approval_id"),
                            "data": {
                                "decision": msg.get("decision"),
                                "reason": msg.get("reason", ""),
                            },
                        },
                    )

                elif msg_type == "intervention":
                    # User intervenes in agent execution (pause, redirect, cancel)
                    await manager.broadcast(
                        company_id,
                        {
                            "event_type": "user.intervention",
                            "target_type": msg.get("target_type", "task"),
                            "target_id": msg.get("target_id"),
                            "data": {
                                "action": msg.get("action"),  # pause, resume, cancel, redirect
                                "reason": msg.get("reason", ""),
                                "new_instructions": msg.get("new_instructions"),
                            },
                        },
                    )

            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "message": "Invalid JSON",
                        }
                    )
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket, company_id)
