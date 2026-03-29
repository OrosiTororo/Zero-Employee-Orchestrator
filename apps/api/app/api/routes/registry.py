"""Skill / Plugin / Extension registry API endpoints.

Provides full CRUD operations, natural language skill generation, and system protection.
Write operations (create, update, delete, install) require authentication.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.models.user import User
from app.schemas.registry import (
    ExtensionCreate,
    ExtensionRead,
    ExtensionUpdate,
    PluginCreate,
    PluginRead,
    PluginUpdate,
    RegistryDeleteResponse,
    SkillCreate,
    SkillGenerateRequest,
    SkillGenerateResponse,
    SkillRead,
    SkillUpdate,
)
from app.services import registry_service, skill_service
from app.services.skill_service import analyze_code_safety

router = APIRouter()


def _check_manifest_safety(manifest_json: dict | None, force: bool = False) -> None:
    """Run safety analysis on manifest code. Blocks HIGH risk unless force=True."""
    if not manifest_json:
        return
    # Extract code from common manifest keys
    code_parts = []
    for key in ("executor_code", "code", "script", "source_code", "generated_code"):
        if key in manifest_json and isinstance(manifest_json[key], str):
            code_parts.append(manifest_json[key])
    if not code_parts:
        return
    combined = "\n".join(code_parts)
    report = analyze_code_safety(combined)
    if report.risk_level == "high" and not force:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Safety check failed: high-risk code detected / 安全チェック失敗: 高リスクコード検出",
                "safety_report": {
                    "risk_level": report.risk_level,
                    "has_dangerous_code": report.has_dangerous_code,
                    "has_external_communication": report.has_external_communication,
                    "has_credential_access": report.has_credential_access,
                    "has_destructive_operations": report.has_destructive_operations,
                    "summary": report.summary,
                },
                "hint": "Add ?force=true to bypass (requires acknowledgement) / ?force=true で強制インストール可",
            },
        )


# ===================================================================
# Skill endpoints
# ===================================================================


@router.get("/skills", response_model=list[SkillRead])
async def list_skills(
    status: str | None = None,
    skill_type: str | None = None,
    include_disabled: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List all skills."""
    skills = await skill_service.list_skills(
        db, status=status, skill_type=skill_type, include_disabled=include_disabled
    )
    return [_skill_to_read(s) for s in skills]


@router.get("/skills/{skill_id}", response_model=SkillRead)
async def get_skill(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a skill by ID."""
    skill = await skill_service.get_skill(db, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return _skill_to_read(skill)


@router.post("/skills", response_model=SkillRead, status_code=201)
async def create_skill(
    data: SkillCreate,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new skill."""
    _check_manifest_safety(data.manifest_json, force)
    existing = await skill_service.get_skill_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Skill '{data.slug}' already exists",
        )
    skill = await skill_service.create_skill(db, data)
    await db.commit()
    return _skill_to_read(skill)


@router.post("/skills/install", response_model=SkillRead, status_code=201)
async def install_skill(
    data: SkillCreate,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Install a skill (alias for create)."""
    _check_manifest_safety(data.manifest_json, force)
    existing = await skill_service.get_skill_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Skill '{data.slug}' already exists",
        )
    skill = await skill_service.create_skill(db, data)
    await db.commit()
    return _skill_to_read(skill)


@router.patch("/skills/{skill_id}", response_model=SkillRead)
async def update_skill(
    skill_id: uuid.UUID,
    data: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a skill."""
    try:
        skill = await skill_service.update_skill(db, skill_id, data)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    await db.commit()
    return _skill_to_read(skill)


@router.delete("/skills/{skill_id}", response_model=RegistryDeleteResponse)
async def delete_skill(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a skill. System-protected skills cannot be deleted."""
    deleted, message = await skill_service.delete_skill(db, skill_id)
    if not deleted and "not found" in message.lower():
        raise HTTPException(status_code=404, detail=message)
    if not deleted:
        raise HTTPException(status_code=403, detail=message)
    await db.commit()
    return RegistryDeleteResponse(deleted=True, message=message)


@router.post("/skills/generate", response_model=SkillGenerateResponse)
async def generate_skill(
    request: SkillGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Auto-generate a skill from a natural language description."""
    result = await skill_service.generate_skill_from_description(request, db)
    if result.registered:
        await db.commit()
    return result


# ===================================================================
# Plugin endpoints
# ===================================================================


@router.get("/plugins", response_model=list[PluginRead])
async def list_plugins(
    status: str | None = None,
    include_disabled: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List all plugins."""
    plugins = await registry_service.list_plugins(
        db, status=status, include_disabled=include_disabled
    )
    return [_plugin_to_read(p) for p in plugins]


@router.get("/plugins/{plugin_id}", response_model=PluginRead)
async def get_plugin(
    plugin_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a plugin by ID."""
    plugin = await registry_service.get_plugin(db, plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return _plugin_to_read(plugin)


@router.post("/plugins", response_model=PluginRead, status_code=201)
async def create_plugin(
    data: PluginCreate,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new plugin."""
    _check_manifest_safety(data.manifest_json, force)
    existing = await registry_service.get_plugin_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Plugin '{data.slug}' already exists",
        )
    plugin = await registry_service.create_plugin(db, data)
    await db.commit()
    return _plugin_to_read(plugin)


@router.post("/plugins/install", response_model=PluginRead, status_code=201)
async def install_plugin(
    data: PluginCreate,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Install a plugin."""
    _check_manifest_safety(data.manifest_json, force)
    existing = await registry_service.get_plugin_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Plugin '{data.slug}' already exists",
        )
    plugin = await registry_service.create_plugin(db, data)
    await db.commit()
    return _plugin_to_read(plugin)


@router.patch("/plugins/{plugin_id}", response_model=PluginRead)
async def update_plugin(
    plugin_id: uuid.UUID,
    data: PluginUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a plugin."""
    try:
        plugin = await registry_service.update_plugin(db, plugin_id, data)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")
    await db.commit()
    return _plugin_to_read(plugin)


@router.delete("/plugins/{plugin_id}", response_model=RegistryDeleteResponse)
async def delete_plugin(
    plugin_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a plugin. System-protected plugins cannot be deleted."""
    deleted, message = await registry_service.delete_plugin(db, plugin_id)
    if not deleted and "not found" in message.lower():
        raise HTTPException(status_code=404, detail=message)
    if not deleted:
        raise HTTPException(status_code=403, detail=message)
    await db.commit()
    return RegistryDeleteResponse(deleted=True, message=message)


@router.post("/plugins/search-external")
async def search_external_plugins(
    query: str = "",
    limit: int = 20,
):
    """Search for plugins from external sources (GitHub, etc.)."""
    from app.integrations.external_skills import plugin_importer

    results = await plugin_importer.search_plugins(query, limit)
    return [
        {
            "name": r.name,
            "slug": r.slug,
            "description": r.description,
            "source_uri": r.source_uri,
            "author": r.author,
            "stars": r.stars,
        }
        for r in results
    ]


@router.post("/plugins/import", response_model=PluginRead, status_code=201)
async def import_plugin(
    source_uri: str,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Import and install a plugin from a GitHub repository."""
    from app.integrations.external_skills import plugin_importer

    manifest = await plugin_importer.fetch_plugin_manifest(source_uri)
    if manifest is None:
        raise HTTPException(
            status_code=404,
            detail="Plugin manifest not found at the specified source",
        )

    # Safety check on the fetched manifest
    manifest_dict = manifest.model_dump() if hasattr(manifest, "model_dump") else (
        manifest.dict() if hasattr(manifest, "dict") else None
    )
    _check_manifest_safety(manifest_dict, force)

    existing = await registry_service.get_plugin_by_slug(db, manifest.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Plugin '{manifest.slug}' already exists",
        )

    create_data = plugin_importer.to_plugin_create_data(manifest)
    from app.schemas.registry import PluginCreate

    plugin = await registry_service.create_plugin(db, PluginCreate(**create_data))
    await db.commit()
    return _plugin_to_read(plugin)


# ===================================================================
# Extension endpoints
# ===================================================================


@router.get("/extensions", response_model=list[ExtensionRead])
async def list_extensions(
    status: str | None = None,
    include_disabled: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List all extensions."""
    extensions = await registry_service.list_extensions(
        db, status=status, include_disabled=include_disabled
    )
    return [_extension_to_read(e) for e in extensions]


@router.get("/extensions/{ext_id}", response_model=ExtensionRead)
async def get_extension(
    ext_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get an extension by ID."""
    ext = await registry_service.get_extension(db, ext_id)
    if ext is None:
        raise HTTPException(status_code=404, detail="Extension not found")
    return _extension_to_read(ext)


@router.post("/extensions", response_model=ExtensionRead, status_code=201)
async def create_extension(
    data: ExtensionCreate,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new extension."""
    _check_manifest_safety(data.manifest_json, force)
    existing = await registry_service.get_extension_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Extension '{data.slug}' already exists",
        )
    ext = await registry_service.create_extension(db, data)
    await db.commit()
    return _extension_to_read(ext)


@router.post("/extensions/install", response_model=ExtensionRead, status_code=201)
async def install_extension(
    data: ExtensionCreate,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Install an extension."""
    _check_manifest_safety(data.manifest_json, force)
    existing = await registry_service.get_extension_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Extension '{data.slug}' already exists",
        )
    ext = await registry_service.create_extension(db, data)
    await db.commit()
    return _extension_to_read(ext)


@router.patch("/extensions/{ext_id}", response_model=ExtensionRead)
async def update_extension(
    ext_id: uuid.UUID,
    data: ExtensionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update an extension."""
    try:
        ext = await registry_service.update_extension(db, ext_id, data)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if ext is None:
        raise HTTPException(status_code=404, detail="Extension not found")
    await db.commit()
    return _extension_to_read(ext)


@router.delete("/extensions/{ext_id}", response_model=RegistryDeleteResponse)
async def delete_extension(
    ext_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete an extension. System-protected extensions cannot be deleted."""
    deleted, message = await registry_service.delete_extension(db, ext_id)
    if not deleted and "not found" in message.lower():
        raise HTTPException(status_code=404, detail=message)
    if not deleted:
        raise HTTPException(status_code=403, detail=message)
    await db.commit()
    return RegistryDeleteResponse(deleted=True, message=message)


# ===================================================================
# Helpers — ORM to Pydantic conversion
# ===================================================================


def _skill_to_read(s) -> SkillRead:
    return SkillRead(
        id=str(s.id),
        company_id=str(s.company_id) if s.company_id else None,
        slug=s.slug,
        name=s.name,
        skill_type=s.skill_type,
        description=s.description,
        version=s.version,
        status=s.status,
        source_type=s.source_type,
        source_uri=s.source_uri,
        manifest_json=s.manifest_json,
        policy_json=s.policy_json,
        is_system_protected=s.is_system_protected,
        enabled=s.enabled,
        generated_code=s.generated_code,
        created_at=str(s.created_at) if s.created_at else "",
        updated_at=str(s.updated_at) if s.updated_at else "",
    )


def _plugin_to_read(p) -> PluginRead:
    return PluginRead(
        id=str(p.id),
        company_id=str(p.company_id) if p.company_id else None,
        slug=p.slug,
        name=p.name,
        description=p.description,
        version=p.version,
        status=p.status,
        manifest_json=p.manifest_json,
        is_system_protected=p.is_system_protected,
        enabled=p.enabled,
        created_at=str(p.created_at) if p.created_at else "",
        updated_at=str(p.updated_at) if p.updated_at else "",
    )


def _extension_to_read(e) -> ExtensionRead:
    return ExtensionRead(
        id=str(e.id),
        company_id=str(e.company_id) if e.company_id else None,
        slug=e.slug,
        name=e.name,
        description=e.description,
        version=e.version,
        status=e.status,
        manifest_json=e.manifest_json,
        is_system_protected=e.is_system_protected,
        enabled=e.enabled,
        created_at=str(e.created_at) if e.created_at else "",
        updated_at=str(e.updated_at) if e.updated_at else "",
    )
