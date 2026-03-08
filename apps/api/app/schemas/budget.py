"""Budget / cost DTOs."""

from pydantic import BaseModel


class BudgetPolicyCreate(BaseModel):
    name: str
    scope_type: str = "company"
    scope_id: str | None = None
    period_type: str = "monthly"
    limit_usd: float = 100.0
    warn_threshold_pct: int = 80
    stop_threshold_pct: int = 100


class BudgetPolicyRead(BaseModel):
    id: str
    company_id: str
    name: str
    scope_type: str
    scope_id: str | None = None
    period_type: str
    limit_usd: float
    warn_threshold_pct: int
    stop_threshold_pct: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class CostSummary(BaseModel):
    total_usd: float = 0.0
    by_provider: dict[str, float] = {}
    by_model: dict[str, float] = {}
    by_agent: dict[str, float] = {}
    period: str = "month"


class CostLedgerRead(BaseModel):
    id: str
    company_id: str
    scope_type: str
    scope_id: str
    provider_name: str
    model_name: str | None = None
    cost_usd: float
    tokens_input: int | None = None
    tokens_output: int | None = None
    occurred_at: str
    created_at: str

    model_config = {"from_attributes": True}
