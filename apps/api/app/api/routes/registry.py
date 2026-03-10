"""Skill / Plugin / Extension レジストリ API エンドポイント.

全 CRUD 操作、自然言語スキル生成、システム保護を提供する。
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
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
from app.services import skill_service, registry_service

router = APIRouter()


# ===================================================================
# Skill エンドポイント
# ===================================================================


@router.get("/skills", response_model=list[SkillRead])
async def list_skills(
    status: str | None = None,
    skill_type: str | None = None,
    include_disabled: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Skill 一覧を取得する."""
    skills = await skill_service.list_skills(
        db, status=status, skill_type=skill_type, include_disabled=include_disabled
    )
    return [_skill_to_read(s) for s in skills]


@router.get("/skills/{skill_id}", response_model=SkillRead)
async def get_skill(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Skill を ID で取得する."""
    skill = await skill_service.get_skill(db, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="スキルが見つかりません")
    return _skill_to_read(skill)


@router.post("/skills", response_model=SkillRead, status_code=201)
async def create_skill(
    data: SkillCreate,
    db: AsyncSession = Depends(get_db),
):
    """新しい Skill を作成する."""
    existing = await skill_service.get_skill_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"スキル '{data.slug}' は既に存在します",
        )
    skill = await skill_service.create_skill(db, data)
    await db.commit()
    return _skill_to_read(skill)


@router.post("/skills/install", response_model=SkillRead, status_code=201)
async def install_skill(
    data: SkillCreate,
    db: AsyncSession = Depends(get_db),
):
    """Skill をインストールする (create のエイリアス)."""
    existing = await skill_service.get_skill_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"スキル '{data.slug}' は既に存在します",
        )
    skill = await skill_service.create_skill(db, data)
    await db.commit()
    return _skill_to_read(skill)


@router.patch("/skills/{skill_id}", response_model=SkillRead)
async def update_skill(
    skill_id: uuid.UUID,
    data: SkillUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Skill を更新する."""
    try:
        skill = await skill_service.update_skill(db, skill_id, data)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if skill is None:
        raise HTTPException(status_code=404, detail="スキルが見つかりません")
    await db.commit()
    return _skill_to_read(skill)


@router.delete("/skills/{skill_id}", response_model=RegistryDeleteResponse)
async def delete_skill(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Skill を削除する. システム保護スキルは削除不可."""
    deleted, message = await skill_service.delete_skill(db, skill_id)
    if not deleted and "見つかりません" in message:
        raise HTTPException(status_code=404, detail=message)
    if not deleted:
        raise HTTPException(status_code=403, detail=message)
    await db.commit()
    return RegistryDeleteResponse(deleted=True, message=message)


@router.post("/skills/generate", response_model=SkillGenerateResponse)
async def generate_skill(
    request: SkillGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """自然言語の説明からスキルを自動生成する."""
    result = await skill_service.generate_skill_from_description(request, db)
    if result.registered:
        await db.commit()
    return result


# ===================================================================
# Plugin エンドポイント
# ===================================================================


@router.get("/plugins", response_model=list[PluginRead])
async def list_plugins(
    status: str | None = None,
    include_disabled: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Plugin 一覧を取得する."""
    plugins = await registry_service.list_plugins(
        db, status=status, include_disabled=include_disabled
    )
    return [_plugin_to_read(p) for p in plugins]


@router.get("/plugins/{plugin_id}", response_model=PluginRead)
async def get_plugin(
    plugin_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Plugin を ID で取得する."""
    plugin = await registry_service.get_plugin(db, plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="プラグインが見つかりません")
    return _plugin_to_read(plugin)


@router.post("/plugins", response_model=PluginRead, status_code=201)
async def create_plugin(
    data: PluginCreate,
    db: AsyncSession = Depends(get_db),
):
    """新しい Plugin を作成する."""
    existing = await registry_service.get_plugin_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"プラグイン '{data.slug}' は既に存在します",
        )
    plugin = await registry_service.create_plugin(db, data)
    await db.commit()
    return _plugin_to_read(plugin)


@router.post("/plugins/install", response_model=PluginRead, status_code=201)
async def install_plugin(
    data: PluginCreate,
    db: AsyncSession = Depends(get_db),
):
    """Plugin をインストールする."""
    existing = await registry_service.get_plugin_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"プラグイン '{data.slug}' は既に存在します",
        )
    plugin = await registry_service.create_plugin(db, data)
    await db.commit()
    return _plugin_to_read(plugin)


@router.patch("/plugins/{plugin_id}", response_model=PluginRead)
async def update_plugin(
    plugin_id: uuid.UUID,
    data: PluginUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Plugin を更新する."""
    try:
        plugin = await registry_service.update_plugin(db, plugin_id, data)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if plugin is None:
        raise HTTPException(status_code=404, detail="プラグインが見つかりません")
    await db.commit()
    return _plugin_to_read(plugin)


@router.delete("/plugins/{plugin_id}", response_model=RegistryDeleteResponse)
async def delete_plugin(
    plugin_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Plugin を削除する. システム保護プラグインは削除不可."""
    deleted, message = await registry_service.delete_plugin(db, plugin_id)
    if not deleted and "見つかりません" in message:
        raise HTTPException(status_code=404, detail=message)
    if not deleted:
        raise HTTPException(status_code=403, detail=message)
    await db.commit()
    return RegistryDeleteResponse(deleted=True, message=message)


# ===================================================================
# Extension エンドポイント
# ===================================================================


@router.get("/extensions", response_model=list[ExtensionRead])
async def list_extensions(
    status: str | None = None,
    include_disabled: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Extension 一覧を取得する."""
    extensions = await registry_service.list_extensions(
        db, status=status, include_disabled=include_disabled
    )
    return [_extension_to_read(e) for e in extensions]


@router.get("/extensions/{ext_id}", response_model=ExtensionRead)
async def get_extension(
    ext_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Extension を ID で取得する."""
    ext = await registry_service.get_extension(db, ext_id)
    if ext is None:
        raise HTTPException(status_code=404, detail="拡張が見つかりません")
    return _extension_to_read(ext)


@router.post("/extensions", response_model=ExtensionRead, status_code=201)
async def create_extension(
    data: ExtensionCreate,
    db: AsyncSession = Depends(get_db),
):
    """新しい Extension を作成する."""
    existing = await registry_service.get_extension_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"拡張 '{data.slug}' は既に存在します",
        )
    ext = await registry_service.create_extension(db, data)
    await db.commit()
    return _extension_to_read(ext)


@router.post("/extensions/install", response_model=ExtensionRead, status_code=201)
async def install_extension(
    data: ExtensionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Extension をインストールする."""
    existing = await registry_service.get_extension_by_slug(db, data.slug)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"拡張 '{data.slug}' は既に存在します",
        )
    ext = await registry_service.create_extension(db, data)
    await db.commit()
    return _extension_to_read(ext)


@router.patch("/extensions/{ext_id}", response_model=ExtensionRead)
async def update_extension(
    ext_id: uuid.UUID,
    data: ExtensionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Extension を更新する."""
    try:
        ext = await registry_service.update_extension(db, ext_id, data)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if ext is None:
        raise HTTPException(status_code=404, detail="拡張が見つかりません")
    await db.commit()
    return _extension_to_read(ext)


@router.delete("/extensions/{ext_id}", response_model=RegistryDeleteResponse)
async def delete_extension(
    ext_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Extension を削除する. システム保護拡張は削除不可."""
    deleted, message = await registry_service.delete_extension(db, ext_id)
    if not deleted and "見つかりません" in message:
        raise HTTPException(status_code=404, detail=message)
    if not deleted:
        raise HTTPException(status_code=403, detail=message)
    await db.commit()
    return RegistryDeleteResponse(deleted=True, message=message)


# ===================================================================
# ヘルパー — ORM → Pydantic 変換
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
