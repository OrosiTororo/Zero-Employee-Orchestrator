"""Heartbeat DTOs."""

from pydantic import BaseModel


class HeartbeatPolicyCreate(BaseModel):
    name: str
    cron_expr: str = "0 * * * *"
    timezone: str = "UTC"
    enabled: bool = True
    jitter_seconds: int = 0
    max_parallel_runs: int = 1


class HeartbeatPolicyRead(BaseModel):
    id: str
    company_id: str
    name: str
    cron_expr: str
    timezone: str
    enabled: bool
    jitter_seconds: int
    max_parallel_runs: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class HeartbeatRunRead(BaseModel):
    id: str
    company_id: str
    policy_id: str
    agent_id: str | None = None
    team_id: str | None = None
    status: str
    started_at: str
    finished_at: str | None = None
    summary: dict | None = None
    created_at: str

    model_config = {"from_attributes": True}
