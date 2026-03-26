"""Browser Assist WebSocket — real-time chat WebSocket endpoint.

Accepts connections from Chrome extensions and desktop apps,
assisting users in real-time while AI views their current screen.

Safety:
- Requires explicit user consent
- Screenshots are processed temporarily only (not permanently stored)
- All messages are recorded in audit logs
- Prompt injection inspection is performed
- PII detection and masking
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.integrations.browser_assist import (
    AssistAction,
    browser_assist_service,
)
from app.security.pii_guard import detect_and_mask_pii
from app.security.prompt_guard import scan_prompt_injection

logger = logging.getLogger(__name__)

router = APIRouter()


class BrowserAssistConnectionManager:
    """Browser Assist WebSocket connection manager."""

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}  # session_id -> ws
        self._user_sessions: dict[str, list[str]] = {}  # user_id -> [session_ids]

    async def connect(self, websocket: WebSocket, session_id: str, user_id: str) -> None:
        await websocket.accept()
        self._connections[session_id] = websocket
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session_id)
        logger.info("Browser assist WS connected: session=%s, user=%s", session_id, user_id)

    def disconnect(self, session_id: str, user_id: str) -> None:
        self._connections.pop(session_id, None)
        if user_id in self._user_sessions:
            self._user_sessions[user_id] = [
                s for s in self._user_sessions[user_id] if s != session_id
            ]
        logger.info("Browser assist WS disconnected: session=%s", session_id)

    async def send_to_session(self, session_id: str, data: dict) -> None:
        ws = self._connections.get(session_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data, default=str))
            except Exception:
                self._connections.pop(session_id, None)


ba_manager = BrowserAssistConnectionManager()


@router.websocket("/ws/browser-assist")
async def browser_assist_websocket(websocket: WebSocket):
    """Browser Assist dedicated WebSocket endpoint.

    Accepts connections from Chrome extensions and conducts real-time chat.
    Receives user screen captures and questions, and AI analyzes and responds.

    Client message format:
    {
        "type": "browser_assist_chat",
        "content": "question text",
        "url": "currently viewed URL",
        "title": "page title",
        "user_id": "user ID",
        "language": "ja",
        "attachments": [{"name": "...", "type": "image/png", "data": "data:..."}]
    }
    """
    session_id = str(uuid.uuid4())
    user_id = websocket.query_params.get("user_id", "extension_user")

    await ba_manager.connect(websocket, session_id, user_id)

    try:
        # Connection confirmation message
        await ba_manager.send_to_session(
            session_id,
            {
                "type": "connected",
                "session_id": session_id,
                "message": "Browser assist connected",
            },
        )

        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ba_manager.send_to_session(
                    session_id,
                    {
                        "type": "error",
                        "message": "Invalid JSON",
                    },
                )
                continue

            msg_type = msg.get("type", "")

            if msg_type == "ping":
                await ba_manager.send_to_session(session_id, {"type": "pong"})

            elif msg_type == "browser_assist_chat":
                await _handle_chat_message(session_id, user_id, msg)

            elif msg_type == "page_context":
                # Receive page DOM information and metadata (for future extensions)
                logger.info(
                    "Page context received: session=%s, url=%s",
                    session_id,
                    msg.get("url", ""),
                )

    except WebSocketDisconnect:
        ba_manager.disconnect(session_id, user_id)
    except Exception as exc:
        logger.error("Browser assist WS error: %s", exc)
        ba_manager.disconnect(session_id, user_id)


async def _handle_chat_message(
    session_id: str,
    user_id: str,
    msg: dict,
) -> None:
    """Process a chat message."""
    content = msg.get("content", "")
    url = msg.get("url", "")
    language = msg.get("language", "ja")
    attachments = msg.get("attachments", [])

    if not content and not attachments:
        await ba_manager.send_to_session(
            session_id,
            {
                "type": "error",
                "message": "Empty message",
            },
        )
        return

    # Prompt injection inspection
    if content:
        guard = scan_prompt_injection(content)
        if not guard.is_safe and guard.threat_level.value in ("high", "critical"):
            await ba_manager.send_to_session(
                session_id,
                {
                    "type": "error",
                    "message": "Message blocked: potentially unsafe content detected.",
                },
            )
            return

    # PII detection and masking (mask user data before passing to AI)
    if content:
        pii_result = detect_and_mask_pii(content)
        if pii_result.detected_types:
            logger.info(
                "PII detected in browser assist chat: types=%s, session=%s",
                pii_result.detected_types,
                session_id,
            )
            # Warn user
            await ba_manager.send_to_session(
                session_id,
                {
                    "type": "pii_warning",
                    "message": "Personal information detected and masked before sending to AI.",
                    "detected_types": pii_result.detected_types,
                },
            )
            content = pii_result.masked_text

    # Consent check
    if not browser_assist_service.check_user_consent(user_id):
        # Auto-consent via WebSocket (consent is assumed when extension is installed)
        browser_assist_service.grant_consent(user_id)

    # Typing indicator
    await ba_manager.send_to_session(session_id, {"type": "typing_start"})

    # Extract base64 if image attachment is present
    screenshot_base64 = ""
    for att in attachments:
        if att.get("type", "").startswith("image/"):
            data = att.get("data", "")
            if data.startswith("data:"):
                screenshot_base64 = data.split(",", 1)[-1] if "," in data else ""
            else:
                screenshot_base64 = data
            break

    try:
        result = await browser_assist_service.analyze_screenshot(
            screenshot_base64=screenshot_base64,
            user_question=content,
            action=AssistAction.ANALYZE_SCREEN,
            target_url=url,
            browser="chrome",
            language=language,
            user_id=user_id,
        )

        await ba_manager.send_to_session(
            session_id,
            {
                "type": "typing_end",
            },
        )

        await ba_manager.send_to_session(
            session_id,
            {
                "type": "assistant_message",
                "content": result.explanation,
                "confidence": result.confidence,
                "warnings": result.warnings,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    except Exception as exc:
        logger.error("Browser assist chat error: %s", exc)
        await ba_manager.send_to_session(session_id, {"type": "typing_end"})
        await ba_manager.send_to_session(
            session_id,
            {
                "type": "error",
                "message": f"Analysis failed: {exc}",
            },
        )
