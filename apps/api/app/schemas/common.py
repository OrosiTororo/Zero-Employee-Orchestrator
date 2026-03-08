"""Common schema types shared across modules."""

from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    items: list = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_next: bool = False


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None


class SuccessResponse(BaseModel):
    success: bool = True
    message: str = ""


class WebSocketEvent(BaseModel):
    event_type: str
    target_type: str | None = None
    target_id: str | None = None
    company_id: str | None = None
    data: dict = {}
