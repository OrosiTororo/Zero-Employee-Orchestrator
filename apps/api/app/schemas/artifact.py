"""Artifact DTOs."""

from pydantic import BaseModel


class ArtifactCreate(BaseModel):
    artifact_type: str
    title: str
    storage_type: str = "local"
    path_or_uri: str | None = None
    mime_type: str | None = None
    summary: str | None = None
    meta_json: dict | None = None


class ArtifactRead(BaseModel):
    id: str
    company_id: str
    ticket_id: str | None = None
    task_id: str | None = None
    artifact_type: str
    title: str
    storage_type: str
    path_or_uri: str | None = None
    mime_type: str | None = None
    version_no: int
    summary: str | None = None
    meta_json: dict | None = None
    created_at: str

    model_config = {"from_attributes": True}
