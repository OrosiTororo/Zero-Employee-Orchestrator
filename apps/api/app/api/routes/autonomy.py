"""Autonomy Dial endpoints — per-company default + per-user transient override.

Reads/writes the same ``AUTONOMY_LEVEL`` config slot the existing settings
page already exposes, plus a transient override row that the Autonomy Dial
in the status bar can set ("drop to ASSIST for the next 30 minutes").

Backend enforcement happens in :func:`app.policies.autonomy_boundary
.resolve_effective_autonomy`; this module is just the read/write surface.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.deps.validators import parse_uuid
from app.api.routes.auth import get_current_user
from app.models.audit import AuditLog
from app.models.autonomy_override import AutonomySessionOverride
from app.models.user import User
from app.policies.autonomy_boundary import AutonomyLevel, resolve_effective_autonomy

router = APIRouter()

CONFIG_KEY = "AUTONOMY_LEVEL"


class AutonomyStatus(BaseModel):
    company_default: str
    effective: str
    override_active: bool
    override_expires_at: datetime | None
    override_reason: str | None


class AutonomyDefaultUpdate(BaseModel):
    level: str = Field(..., description="One of: observe, assist, semi_auto, autonomous")


class AutonomyOverrideRequest(BaseModel):
    level: str
    ttl_minutes: int | None = Field(default=None, ge=1, le=24 * 60)
    until_session_end: bool = False
    reason: str | None = Field(default=None, max_length=255)


def _validate_level(raw: str) -> AutonomyLevel:
    candidate = (raw or "").strip().lower().replace("-", "_")
    try:
        return AutonomyLevel(candidate)
    except ValueError as exc:
        valid = ", ".join(level.value for level in AutonomyLevel)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid autonomy '{raw}'. Allowed: {valid}",
        ) from exc


def _read_company_default() -> AutonomyLevel:
    """Read the persistent autonomy default from the runtime config file.

    ZEO is single-tenant in practice (one operator's installation = one
    "company"), so the default is stored alongside other knobs in
    ``~/.zero-employee/config.json`` rather than in a per-company table.
    """
    from app.core.config_manager import get_config_value

    raw = get_config_value(CONFIG_KEY) or ""
    candidate = raw.strip().lower().replace("-", "_")
    try:
        return AutonomyLevel(candidate) if candidate else AutonomyLevel.SEMI_AUTO
    except ValueError:
        return AutonomyLevel.SEMI_AUTO


def _write_company_default(level: AutonomyLevel) -> None:
    from app.core.config_manager import set_config_value

    set_config_value(CONFIG_KEY, level.value)


@router.get("/companies/{company_id}/autonomy", response_model=AutonomyStatus)
async def get_autonomy(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AutonomyStatus:
    """Return the company default plus the operator's currently-active override."""
    parse_uuid(company_id, "company_id")
    default = _read_company_default()
    effective, expires_at = await resolve_effective_autonomy(db, user.id, default)
    override_active = expires_at is not None

    reason: str | None = None
    if override_active:
        res = await db.execute(
            select(AutonomySessionOverride)
            .where(AutonomySessionOverride.user_id == user.id)
            .order_by(AutonomySessionOverride.created_at.desc())
            .limit(1)
        )
        last = res.scalar_one_or_none()
        if last:
            reason = last.reason

    return AutonomyStatus(
        company_default=default.value,
        effective=effective.value,
        override_active=override_active,
        override_expires_at=expires_at,
        override_reason=reason,
    )


@router.patch("/companies/{company_id}/autonomy", response_model=AutonomyStatus)
async def set_autonomy_default(
    company_id: str,
    req: AutonomyDefaultUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AutonomyStatus:
    """Persist the company-level autonomy default."""
    company_uuid = parse_uuid(company_id, "company_id")
    level = _validate_level(req.level)
    _write_company_default(level)
    audit = AuditLog(
        id=uuid.uuid4(),
        company_id=company_uuid,
        actor_type="user",
        actor_user_id=user.id,
        event_type="autonomy.default.changed",
        target_type="company",
        target_id=company_uuid,
        details_json={"new_level": level.value},
    )
    db.add(audit)
    await db.commit()
    return await get_autonomy(company_id, db, user)


@router.post("/companies/{company_id}/autonomy/override", response_model=AutonomyStatus)
async def set_autonomy_override(
    company_id: str,
    req: AutonomyOverrideRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AutonomyStatus:
    """Set a transient autonomy override for the calling operator.

    Either ``ttl_minutes`` or ``until_session_end`` must be supplied.
    Setting ``until_session_end`` materialises as an 8-hour cap so we do not
    accumulate dead override rows when the user closes the tab.
    """
    company_uuid = parse_uuid(company_id, "company_id")
    level = _validate_level(req.level)
    if not req.ttl_minutes and not req.until_session_end:
        raise HTTPException(
            status_code=400,
            detail="Specify either ttl_minutes or until_session_end=true",
        )
    minutes = req.ttl_minutes if req.ttl_minutes else 8 * 60
    expires_at = (datetime.now(UTC) + timedelta(minutes=minutes)).replace(tzinfo=None)

    # Replace any existing override so we never accumulate stale rows for
    # the same operator.
    await db.execute(
        delete(AutonomySessionOverride).where(AutonomySessionOverride.user_id == user.id)
    )
    override = AutonomySessionOverride(
        id=uuid.uuid4(),
        user_id=user.id,
        company_id=company_uuid,
        autonomy_level=level.value,
        expires_at=expires_at,
        reason=req.reason,
    )
    db.add(override)

    audit = AuditLog(
        id=uuid.uuid4(),
        company_id=company_uuid,
        actor_type="user",
        actor_user_id=user.id,
        event_type="autonomy.override.start",
        target_type="user",
        target_id=user.id,
        details_json={
            "level": level.value,
            "expires_at": expires_at.isoformat(),
            "reason": req.reason,
            "until_session_end": req.until_session_end,
        },
    )
    db.add(audit)
    await db.commit()

    return await get_autonomy(company_id, db, user)


@router.delete("/companies/{company_id}/autonomy/override", response_model=AutonomyStatus)
async def clear_autonomy_override(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AutonomyStatus:
    """Clear any active autonomy override for the calling operator."""
    company_uuid = parse_uuid(company_id, "company_id")
    res = await db.execute(
        delete(AutonomySessionOverride).where(AutonomySessionOverride.user_id == user.id)
    )
    if res.rowcount:
        audit = AuditLog(
            id=uuid.uuid4(),
            company_id=company_uuid,
            actor_type="user",
            actor_user_id=user.id,
            event_type="autonomy.override.end",
            target_type="user",
            target_id=user.id,
            details_json={"cleared": True},
        )
        db.add(audit)
    await db.commit()
    return await get_autonomy(company_id, db, user)
