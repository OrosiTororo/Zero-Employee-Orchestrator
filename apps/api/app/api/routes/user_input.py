"""User input request API endpoints.

Provides functionality for AI tasks to request additional information from users
during execution: create, answer, list, and cancel requests.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.security.pii_guard import detect_and_mask_pii
from app.services.user_input_service import (
    InputRequest,
    InputRequestStatus,
    InputRequestType,
    user_input_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-input", tags=["user-input"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class CreateInputRequestBody(BaseModel):
    """Create input request body."""

    task_id: str = Field(..., description="Target task ID")
    request_type: InputRequestType = Field(..., description="Input type")
    prompt_text: str = Field(
        ..., min_length=1, max_length=2000, description="Prompt displayed to the user"
    )
    options: list[str] | None = Field(default=None, description="Options for CHOICE type")
    timeout_seconds: int = Field(default=300, ge=10, le=86400, description="Timeout in seconds")


class AnswerInputBody(BaseModel):
    """Input answer body."""

    response: str | list[str] | bool = Field(..., description="User response")


class InputRequestResponse(BaseModel):
    """Input request response."""

    id: str
    task_id: str
    request_type: str
    prompt_text: str
    options: list[str] | None
    timeout_seconds: int
    status: str
    created_at: str
    answered_at: str | None
    response: str | list[str] | bool | None


class PendingRequestsResponse(BaseModel):
    """Pending requests list response."""

    requests: list[InputRequestResponse]
    total: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_response(req: InputRequest) -> InputRequestResponse:
    """Convert InputRequest to InputRequestResponse."""
    return InputRequestResponse(
        id=req.id,
        task_id=req.task_id,
        request_type=req.request_type.value,
        prompt_text=req.prompt_text,
        options=req.options,
        timeout_seconds=req.timeout_seconds,
        status=req.status.value,
        created_at=req.created_at.isoformat(),
        answered_at=req.answered_at.isoformat() if req.answered_at else None,
        response=req.response,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/request", response_model=InputRequestResponse)
async def create_input_request(
    body: CreateInputRequestBody, user: User = Depends(get_current_user)
) -> InputRequestResponse:
    """Create an input request.

    Used when an AI task requires additional information from the user.
    """
    try:
        request_id = await user_input_service.request_input(
            task_id=body.task_id,
            request_type=body.request_type,
            prompt_text=body.prompt_text,
            options=body.options,
            timeout_seconds=body.timeout_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    req = user_input_service.get_request(request_id)
    if req is None:
        raise HTTPException(status_code=500, detail="Failed to create request")
    return _to_response(req)


@router.get("/pending", response_model=PendingRequestsResponse)
async def list_all_pending_requests(
    user: User = Depends(get_current_user),
) -> PendingRequestsResponse:
    """Get all pending requests across all tasks."""
    # Run expiration check first
    await user_input_service.expire_stale_requests()

    all_pending: list[InputRequest] = [
        r for r in user_input_service._requests.values() if r.status == InputRequestStatus.PENDING
    ]
    return PendingRequestsResponse(
        requests=[_to_response(r) for r in all_pending],
        total=len(all_pending),
    )


@router.get("/pending/{task_id}", response_model=PendingRequestsResponse)
async def list_pending_for_task(
    task_id: str, user: User = Depends(get_current_user)
) -> PendingRequestsResponse:
    """Get pending requests for a specific task."""
    await user_input_service.expire_stale_requests()
    pending = await user_input_service.get_pending_requests(task_id)
    return PendingRequestsResponse(
        requests=[_to_response(r) for r in pending],
        total=len(pending),
    )


@router.post("/{request_id}/answer", response_model=InputRequestResponse)
@limiter.limit("30/minute")
async def answer_request(
    request: Request,
    request_id: str,
    body: AnswerInputBody,
    user: User = Depends(get_current_user),
) -> InputRequestResponse:
    """Answer an input request."""
    # PII detection for string responses
    response = body.response
    if isinstance(response, str):
        pii_result = detect_and_mask_pii(response)
        if pii_result.detected_count > 0:
            logger.warning(
                "PII detected in user input answer: types=%s",
                pii_result.detected_types,
            )
            response = pii_result.masked_text

    try:
        req = await user_input_service.answer_input(request_id, response)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(req)


@router.delete("/{request_id}", response_model=InputRequestResponse)
async def cancel_request(
    request_id: str, user: User = Depends(get_current_user)
) -> InputRequestResponse:
    """Cancel an input request."""
    try:
        req = await user_input_service.cancel_request(request_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(req)
