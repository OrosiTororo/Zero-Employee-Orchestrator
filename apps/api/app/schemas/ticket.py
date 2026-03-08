"""Ticket-related DTOs."""

from pydantic import BaseModel


class TicketCreate(BaseModel):
    title: str
    description: str | None = None
    priority: str = "medium"
    project_id: str | None = None
    goal_id: str | None = None
    source_type: str = "human"
    parent_ticket_id: str | None = None


class TicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None


class TicketRead(BaseModel):
    id: str
    company_id: str
    project_id: str | None = None
    goal_id: str | None = None
    ticket_no: int
    title: str
    description: str | None = None
    priority: str
    status: str
    source_type: str | None = None
    requester_user_id: str | None = None
    assignee_agent_id: str | None = None
    parent_ticket_id: str | None = None
    current_spec_id: str | None = None
    current_plan_id: str | None = None
    due_at: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class TicketAssign(BaseModel):
    assignee_agent_id: str | None = None
    assignee_user_id: str | None = None


class ThreadCreate(BaseModel):
    message_type: str = "comment"
    body_markdown: str
    meta_json: dict | None = None


class ThreadRead(BaseModel):
    id: str
    ticket_id: str
    author_type: str
    author_user_id: str | None = None
    author_agent_id: str | None = None
    message_type: str
    body_markdown: str
    meta_json: dict | None = None
    created_at: str

    model_config = {"from_attributes": True}
