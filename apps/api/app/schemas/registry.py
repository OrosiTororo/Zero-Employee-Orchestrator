"""Skill / Plugin / Extension registry DTOs."""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Skill
# ---------------------------------------------------------------------------

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


class SkillUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    version: str | None = None
    status: str | None = None
    manifest_json: dict | None = None
    policy_json: dict | None = None
    enabled: bool | None = None


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
    is_system_protected: bool = False
    enabled: bool = True
    generated_code: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class SkillGenerateRequest(BaseModel):
    """自然言語でスキルの機能を説明してスキルを自動生成するリクエスト."""

    description: str = Field(..., min_length=10, max_length=5000)
    language: str = "ja"
    auto_register: bool = False


class SkillGenerateResponse(BaseModel):
    """自然言語スキル生成の結果."""

    skill_json: dict
    code: str
    safety_report: "RegistrySafetyReport"
    safety_passed: bool
    safety_issues: list[str] = []
    registered: bool = False
    skill_id: str | None = None


# ---------------------------------------------------------------------------
# Plugin
# ---------------------------------------------------------------------------

class PluginCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None
    version: str = "0.1.0"
    manifest_json: dict | None = None


class PluginUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    version: str | None = None
    status: str | None = None
    manifest_json: dict | None = None
    enabled: bool | None = None


class PluginRead(BaseModel):
    id: str
    company_id: str | None = None
    slug: str
    name: str
    description: str | None = None
    version: str
    status: str
    manifest_json: dict | None = None
    is_system_protected: bool = False
    enabled: bool = True
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Extension
# ---------------------------------------------------------------------------

class ExtensionCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None
    version: str = "0.1.0"
    manifest_json: dict | None = None


class ExtensionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    version: str | None = None
    status: str | None = None
    manifest_json: dict | None = None
    enabled: bool | None = None


class ExtensionRead(BaseModel):
    id: str
    company_id: str | None = None
    slug: str
    name: str
    description: str | None = None
    version: str
    status: str
    manifest_json: dict | None = None
    is_system_protected: bool = False
    enabled: bool = True
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Common
# ---------------------------------------------------------------------------

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


class RegistryDeleteResponse(BaseModel):
    deleted: bool
    message: str
