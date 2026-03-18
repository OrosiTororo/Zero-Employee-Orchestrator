"""Rate limiting middleware using SlowAPI.

認証エンドポイントやAPI全体にレート制限を適用する。
"""

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """レート制限超過時のレスポンス."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "リクエストが多すぎます。しばらく待ってから再試行してください。",
            "retry_after": str(exc.detail),
        },
    )
