"""Organization (departments, teams) DTOs."""

from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    name: str
    code: str | None = None
    description: str | None = None
    parent_department_id: str | None = None


class DepartmentRead(BaseModel):
    id: str
    company_id: str
    parent_department_id: str | None = None
    name: str
    code: str | None = None
    description: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class TeamCreate(BaseModel):
    name: str
    purpose: str | None = None
    department_id: str | None = None
    lead_agent_id: str | None = None


class TeamRead(BaseModel):
    id: str
    company_id: str
    department_id: str | None = None
    name: str
    purpose: str | None = None
    lead_agent_id: str | None = None
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class OrgChartNode(BaseModel):
    id: str
    name: str
    type: str  # "department" | "team" | "agent"
    title: str | None = None
    status: str | None = None
    children: list["OrgChartNode"] = []

    model_config = {"from_attributes": True}
