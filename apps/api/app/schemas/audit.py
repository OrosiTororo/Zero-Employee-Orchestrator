"""Audit log DTOs."""

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: str
    company_id: str
    actor_type: str
    actor_user_id: str | None = None
    actor_agent_id: str | None = None
    event_type: str
    target_type: str
    target_id: str | None = None
    ticket_id: str | None = None
    task_id: str | None = None
    details_json: dict | None = None
    trace_id: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


class AuditLogFilter(BaseModel):
    event_type: str | None = None
    actor_type: str | None = None
    target_type: str | None = None
    trace_id: str | None = None
    date_from: str | None = None
    date_to: str | None = None
