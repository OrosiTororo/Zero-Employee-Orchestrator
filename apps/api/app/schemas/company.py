"""Company-related DTOs."""

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    slug: str
    name: str
    mission: str | None = None
    description: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    mission: str | None = None
    description: str | None = None
    status: str | None = None
    settings_json: dict | None = None


class CompanyRead(BaseModel):
    id: str
    slug: str
    name: str
    mission: str | None = None
    description: str | None = None
    status: str
    settings_json: dict | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class CompanyMemberRead(BaseModel):
    id: str
    company_id: str
    user_id: str
    company_role: str
    status: str
    joined_at: str | None = None
    display_name: str | None = None

    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    company_name: str
    mission: str | None = None
    active_tickets: int = 0
    pending_approvals: int = 0
    active_agents: int = 0
    heartbeat_today: int = 0
    cost_today_usd: float = 0.0
    cost_week_usd: float = 0.0
    cost_month_usd: float = 0.0
    errors_count: int = 0
    blocked_count: int = 0
    rework_count: int = 0
    recent_artifacts: list[dict] = []
    recommended_actions: list[str] = []
