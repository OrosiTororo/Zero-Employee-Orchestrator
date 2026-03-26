"""Rate limiting middleware using SlowAPI.

Applies rate limits to authentication endpoints and the API as a whole.
"""

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Response when rate limit is exceeded."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please wait a moment and try again.",
            "retry_after": str(exc.detail),
        },
    )
