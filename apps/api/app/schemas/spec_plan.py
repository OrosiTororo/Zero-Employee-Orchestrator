"""Spec / Plan / Task DTOs."""

from pydantic import BaseModel


class SpecCreate(BaseModel):
    objective: str
    constraints_json: dict | None = None
    acceptance_criteria_json: dict | None = None
    risk_notes: str | None = None


class SpecRead(BaseModel):
    id: str
    company_id: str
    ticket_id: str
    version_no: int
    status: str
    objective: str
    constraints_json: dict | None = None
    acceptance_criteria_json: dict | None = None
    risk_notes: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PlanCreate(BaseModel):
    spec_id: str
    summary: str
    estimated_cost_usd: float | None = None
    estimated_minutes: int | None = None
    approval_required: bool = True
    risk_level: str = "low"
    plan_json: dict | None = None


class PlanRead(BaseModel):
    id: str
    company_id: str
    ticket_id: str
    spec_id: str
    version_no: int
    status: str
    summary: str
    estimated_cost_usd: float | None = None
    estimated_minutes: int | None = None
    approval_required: bool
    risk_level: str
    plan_json: dict | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    task_type: str = "execute"
    requires_approval: bool = False
    assignee_agent_id: str | None = None
    depends_on_json: dict | None = None
    verification_json: dict | None = None


class TaskRead(BaseModel):
    id: str
    company_id: str
    ticket_id: str
    plan_id: str
    parent_task_id: str | None = None
    assignee_agent_id: str | None = None
    title: str
    description: str | None = None
    sequence_no: int
    status: str
    task_type: str
    requires_approval: bool
    depends_on_json: dict | None = None
    verification_json: dict | None = None
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class TaskRunRead(BaseModel):
    id: str
    task_id: str
    run_no: int
    executor_agent_id: str | None = None
    status: str
    started_at: str
    finished_at: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: str

    model_config = {"from_attributes": True}
