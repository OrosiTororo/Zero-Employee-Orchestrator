"""Orchestrator のデータモデル。"""

from pydantic import BaseModel, Field


class OrchestrationStep(BaseModel):
    step_id: str
    skill_name: str
    input_mapping: dict = {}
    depends_on: list[str] = []
    status: str = "pending"  # pending | running | completed | failed
    output: dict | None = None


class OrchestrationPlan(BaseModel):
    intent: str
    steps: list[OrchestrationStep] = []
    quality_mode: str = "balanced"


class Orchestration(BaseModel):
    id: str
    user_input: str
    plan: OrchestrationPlan | None = None
    status: str = "planning"  # planning | awaiting_approval | executing | completed | failed
    results: dict = {}
    cost_estimate: dict | None = None
    created_at: str = ""


class CostEstimate(BaseModel):
    total_api_calls: int = 0
    estimated_tokens: int = 0
    estimated_cost_usd: float = 0.0
    estimated_time_seconds: int = 0
    model_breakdown: dict = {}
    budget_exceeded: bool = False
