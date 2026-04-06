"""Compliance and data governance endpoints."""

from datetime import UTC, datetime
from enum import Enum

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.routes.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/compliance")


class ExportFormat(str, Enum):
    json = "json"
    csv = "csv"


class AuditExportResponse(BaseModel):
    format: str
    generated_at: str
    record_count: int
    records: list[dict]


class RetentionPolicy(BaseModel):
    audit_logs_days: int
    chat_history_days: int
    artifacts_days: int
    deleted_data_purge_days: int
    backup_retention_days: int


class ComplianceFramework(BaseModel):
    id: str
    name: str
    status: str
    description: str


_FRAMEWORKS: list[dict] = [
    {
        "id": "gdpr",
        "name": "GDPR",
        "status": "supported",
        "description": "EU General Data Protection Regulation — data export, erasure, consent",
    },
    {
        "id": "hipaa",
        "name": "HIPAA",
        "status": "planned",
        "description": "Health Insurance Portability and Accountability Act — PHI safeguards",
    },
    {
        "id": "soc2",
        "name": "SOC 2 Type II",
        "status": "supported",
        "description": "Service Organization Control — security, availability, confidentiality",
    },
    {
        "id": "ccpa",
        "name": "CCPA",
        "status": "supported",
        "description": "California Consumer Privacy Act — consumer data rights",
    },
    {
        "id": "iso27001",
        "name": "ISO 27001",
        "status": "planned",
        "description": "Information security management system certification",
    },
    {
        "id": "fedramp",
        "name": "FedRAMP",
        "status": "roadmap",
        "description": "Federal Risk and Authorization Management Program",
    },
]


@router.get("/audit-export", response_model=AuditExportResponse)
async def audit_export(
    format: ExportFormat = Query(ExportFormat.json),
    user: User = Depends(get_current_user),
) -> AuditExportResponse:
    """Export audit logs for compliance review (stub — returns sample data)."""
    return AuditExportResponse(
        format=format.value,
        generated_at=datetime.now(UTC).isoformat(),
        record_count=0,
        records=[],
    )


@router.get("/data-retention", response_model=RetentionPolicy)
async def data_retention(
    user: User = Depends(get_current_user),
) -> RetentionPolicy:
    """Return the current data retention policy."""
    return RetentionPolicy(
        audit_logs_days=365,
        chat_history_days=90,
        artifacts_days=180,
        deleted_data_purge_days=30,
        backup_retention_days=90,
    )


@router.get("/frameworks", response_model=list[ComplianceFramework])
async def list_frameworks(
    user: User = Depends(get_current_user),
) -> list[ComplianceFramework]:
    """List supported compliance frameworks and their status."""
    return [ComplianceFramework(**f) for f in _FRAMEWORKS]
