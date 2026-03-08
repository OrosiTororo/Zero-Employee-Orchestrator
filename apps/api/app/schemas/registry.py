"""Skill / Plugin / Extension registry DTOs."""

from pydantic import BaseModel


class SkillCreate(BaseModel):
    slug: str
    name: str
    skill_type: str = "prompt"
    description: str | None = None
    version: str = "0.1.0"
    source_type: str = "local"
    source_uri: str | None = None
    manifest_json: dict | None = None
    policy_json: dict | None = None


class SkillRead(BaseModel):
    id: str
    company_id: str | None = None
    slug: str
    name: str
    skill_type: str
    description: str | None = None
    version: str
    status: str
    source_type: str
    source_uri: str | None = None
    manifest_json: dict | None = None
    policy_json: dict | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PluginCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None
    version: str = "0.1.0"
    manifest_json: dict | None = None


class PluginRead(BaseModel):
    id: str
    company_id: str | None = None
    slug: str
    name: str
    description: str | None = None
    version: str
    status: str
    manifest_json: dict | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ExtensionCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None
    version: str = "0.1.0"
    manifest_json: dict | None = None


class ExtensionRead(BaseModel):
    id: str
    company_id: str | None = None
    slug: str
    name: str
    description: str | None = None
    version: str
    status: str
    manifest_json: dict | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class RegistryInstallRequest(BaseModel):
    source_type: str  # "local" | "git" | "registry"
    source_uri: str
    version: str | None = None


class RegistrySafetyReport(BaseModel):
    has_dangerous_code: bool = False
    has_external_communication: bool = False
    has_credential_access: bool = False
    has_destructive_operations: bool = False
    required_permissions: list[str] = []
    external_connections: list[str] = []
    risk_level: str = "low"
    summary: str = ""
