"""Project / Goal DTOs."""

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    goal: str | None = None
    description: str | None = None
    priority: str = "medium"


class ProjectRead(BaseModel):
    id: str
    company_id: str
    name: str
    goal: str | None = None
    description: str | None = None
    priority: str
    status: str
    owner_user_id: str | None = None
    owner_agent_id: str | None = None
    due_at: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class GoalCreate(BaseModel):
    title: str
    description: str | None = None
    goal_level: str = "project"
    parent_goal_id: str | None = None
    metric_name: str | None = None
    metric_target: float | None = None
    metric_unit: str | None = None


class GoalRead(BaseModel):
    id: str
    company_id: str
    parent_goal_id: str | None = None
    project_id: str | None = None
    title: str
    description: str | None = None
    goal_level: str
    status: str
    metric_name: str | None = None
    metric_target: float | None = None
    metric_unit: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
