"""Approval-related DTOs."""

from pydantic import BaseModel


class ApprovalRequestRead(BaseModel):
    id: str
    company_id: str
    target_type: str
    target_id: str
    requested_by_type: str
    requested_by_user_id: str | None = None
    requested_by_agent_id: str | None = None
    approver_user_id: str | None = None
    status: str
    reason: str | None = None
    risk_level: str
    payload_json: dict | None = None
    requested_at: str
    decided_at: str | None = None

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    decision: str  # "approve" | "reject"
    reason: str | None = None


class ReviewCreate(BaseModel):
    ticket_id: str | None = None
    task_id: str | None = None
    status: str = "pending"
    score: float | None = None
    comments_markdown: str | None = None


class ReviewRead(BaseModel):
    id: str
    company_id: str
    ticket_id: str | None = None
    task_id: str | None = None
    reviewer_type: str
    status: str
    score: float | None = None
    comments_markdown: str | None = None
    created_at: str

    model_config = {"from_attributes": True}
