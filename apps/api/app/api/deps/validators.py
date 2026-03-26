"""Common validation helpers."""

from __future__ import annotations

import logging
import uuid

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def parse_uuid(value: str, name: str = "ID") -> uuid.UUID:
    """Safely parse a UUID string.

    Returns 400 Bad Request if the UUID string is invalid.
    """
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {name} format: {value}",
        )


def require_iam_permission(required: str):
    """IAM permission check decorator (FastAPI Depends compatible).

    Verifies that requests from AI agents have the required permissions.
    Requests from human users are always allowed.

    Usage::

        @router.post("/secrets")
        async def create_secret(
            user=Depends(get_current_user),
            _perm=Depends(require_iam_permission("read:secrets")),
        ):
            ...
    """
    from fastapi import Depends, Request

    from app.api.routes.auth import get_current_user

    async def _check(request: Request, user=Depends(get_current_user)):
        # Determine if the request is from an AI agent
        # If X-Agent-Token header is present, it's an AI agent
        agent_token = request.headers.get("X-Agent-Token")
        if not agent_token:
            return True  # Human users are always allowed

        # IAM check
        from app.security.iam import AI_DENIED_PERMISSIONS

        # Permissions explicitly denied to AI
        denied_values = {d.value for d in AI_DENIED_PERMISSIONS}
        if required in denied_values:
            logger.warning(
                "IAM denied: AI agent attempted forbidden permission %s",
                required,
            )
            raise HTTPException(
                status_code=403,
                detail=f"AI agent does not have permission for this operation: {required}",
            )

        return True

    return _check
