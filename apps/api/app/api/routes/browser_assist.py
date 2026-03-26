"""Browser Assist API endpoints.

API for users to share their screen while operating a browser or application
and receive operation guidance or error diagnosis from AI.

Safety:
- Requires explicit user consent
- Screenshots are processed temporarily only (not permanently stored)
- All requests are recorded in audit logs
- Prompt injection inspection is performed
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.integrations.browser_assist import (
    AssistAction,
    browser_assist_service,
)
from app.models.user import User
from app.security.prompt_guard import ThreatLevel, scan_prompt_injection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/browser-assist", tags=["browser-assist"])


class ConsentRequest(BaseModel):
    """Screen sharing consent request."""

    user_id: str
    consent: bool = True


class AssistRequest(BaseModel):
    """Assist request."""

    user_id: str
    action: str = Field(default="analyze_screen")
    screenshot_base64: str = Field(default="", description="Base64 encoded screenshot")
    user_question: str = Field(..., min_length=1, max_length=2000)
    target_url: str = ""
    browser: str = "chrome"
    language: str = "ja"


class AssistStepResponse(BaseModel):
    """One step of operation instructions."""

    step_number: int
    instruction: str
    ui_element: str = ""


class AssistResponse(BaseModel):
    """Assist result."""

    action: str
    steps: list[AssistStepResponse] = []
    explanation: str = ""
    warnings: list[str] = []
    confidence: float = 0.0


@router.post("/consent")
async def update_consent(req: ConsentRequest, user: User = Depends(get_current_user)) -> dict:
    """Set screen sharing consent.

    Users must explicitly grant consent before using
    the browser assist feature.
    """
    if req.consent:
        browser_assist_service.grant_consent(req.user_id)
        return {"status": "granted", "message": "Screen sharing consent granted"}
    else:
        browser_assist_service.revoke_consent(req.user_id)
        return {"status": "revoked", "message": "Screen sharing consent revoked"}


@router.post("/analyze", response_model=AssistResponse)
async def analyze_screen(
    req: AssistRequest, user: User = Depends(get_current_user)
) -> AssistResponse:
    """Analyze a screenshot and provide operation guidance or error diagnosis.

    AI analyzes the user's screen and responds with operation methods, steps, and error solutions.
    Consent must be granted in advance via /consent.
    """
    # Consent check
    if not browser_assist_service.check_user_consent(req.user_id):
        raise HTTPException(
            status_code=403,
            detail="Screen sharing consent not granted. Call POST /browser-assist/consent first.",
        )

    # Prompt injection inspection
    guard_result = scan_prompt_injection(req.user_question)
    if not guard_result.is_safe:
        logger.warning(
            "Prompt injection detected in browser-assist request: user=%s, threat=%s, detections=%s",
            req.user_id,
            guard_result.threat_level.value,
            guard_result.detections,
        )
        if guard_result.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
            raise HTTPException(
                status_code=400,
                detail="Request blocked: potentially unsafe content detected in question.",
            )

    # Convert action type
    try:
        action = AssistAction(req.action)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {req.action}. Valid: {[a.value for a in AssistAction]}",
        )

    # Execute screenshot analysis
    result = await browser_assist_service.analyze_screenshot(
        screenshot_base64=req.screenshot_base64,
        user_question=req.user_question,
        action=action,
        target_url=req.target_url,
        browser=req.browser,
        language=req.language,
        user_id=req.user_id,
    )

    return AssistResponse(
        action=result.action.value,
        steps=[
            AssistStepResponse(
                step_number=s.step_number,
                instruction=s.instruction,
                ui_element=s.ui_element,
            )
            for s in result.steps
        ],
        explanation=result.explanation,
        warnings=result.warnings,
        confidence=result.confidence,
    )


@router.get("/status")
async def assist_status(user: User = Depends(get_current_user)) -> dict:
    """Return browser assist feature status."""
    return {
        "available": True,
        "supported_actions": [a.value for a in AssistAction],
        "supported_browsers": ["chrome", "firefox", "edge", "safari"],
        "privacy": {
            "screenshots_stored": False,
            "consent_required": True,
            "audit_logged": True,
        },
    }
