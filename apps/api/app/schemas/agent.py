"""Agent-related DTOs."""

from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    title: str | None = None
    description: str | None = None
    agent_type: str = "llm"
    runtime_type: str = "api"
    provider_name: str = "openrouter"
    model_name: str | None = None
    team_id: str | None = None
    manager_agent_id: str | None = None
    autonomy_level: str = "supervised"
    can_delegate: bool = False
    can_write_external: bool = False
    can_spend_budget: bool = False
    config_json: dict | None = None


class AgentUpdate(BaseModel):
    name: str | None = None
    title: str | None = None
    description: str | None = None
    status: str | None = None
    model_name: str | None = None
    team_id: str | None = None
    autonomy_level: str | None = None
    can_delegate: bool | None = None
    can_write_external: bool | None = None
    can_spend_budget: bool | None = None
    config_json: dict | None = None


class AgentRead(BaseModel):
    id: str
    company_id: str
    team_id: str | None = None
    manager_agent_id: str | None = None
    name: str
    title: str | None = None
    description: str | None = None
    agent_type: str
    runtime_type: str
    provider_name: str
    model_name: str | None = None
    status: str
    autonomy_level: str
    can_delegate: bool
    can_write_external: bool
    can_spend_budget: bool
    config_json: dict | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
