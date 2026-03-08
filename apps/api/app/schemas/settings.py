"""Settings / Connection DTOs."""

from pydantic import BaseModel


class ToolConnectionCreate(BaseModel):
    name: str
    connection_type: str
    auth_type: str = "api_key"
    secret_ref: str | None = None
    config_json: dict | None = None


class ToolConnectionRead(BaseModel):
    id: str
    company_id: str
    name: str
    connection_type: str
    status: str
    auth_type: str
    secret_ref: str | None = None
    config_json: dict | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ProviderConfig(BaseModel):
    name: str
    provider_type: str  # "openrouter" | "openai" | "anthropic" | "local" | "litellm"
    api_key_ref: str | None = None
    base_url: str | None = None
    models: list[str] = []
    default_model: str | None = None
    enabled: bool = True


class CompanySettings(BaseModel):
    default_provider: str | None = None
    execution_mode: str = "quality"  # quality | speed | cost | free
    language: str = "ja"
    auto_approve_safe_tasks: bool = False
    providers: list[ProviderConfig] = []


class PolicyPackCreate(BaseModel):
    name: str
    version: str = "1.0.0"
    rules_json: dict | None = None


class PolicyPackRead(BaseModel):
    id: str
    company_id: str
    name: str
    version: str
    status: str
    rules_json: dict | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class SecretRefCreate(BaseModel):
    name: str
    secret_type: str
    provider: str
    masked_value: str | None = None
    expires_at: str | None = None
    rotation_policy_json: dict | None = None


class SecretRefRead(BaseModel):
    id: str
    company_id: str
    name: str
    secret_type: str
    provider: str
    masked_value: str | None = None
    expires_at: str | None = None
    rotation_policy_json: dict | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
