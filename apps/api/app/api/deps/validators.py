"""共通バリデーションヘルパー."""

import uuid

from fastapi import HTTPException


def parse_uuid(value: str, name: str = "ID") -> uuid.UUID:
    """UUID 文字列を安全にパースする.

    不正な UUID 文字列の場合は 400 Bad Request を返す。
    """
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {name} format: {value}",
        )
