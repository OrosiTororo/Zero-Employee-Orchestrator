"""Skill / Plugin / Extension registry endpoints."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.database import get_db
from app.models.skill import Extension, Plugin, Skill

router = APIRouter()


class SkillInstall(BaseModel):
    slug: str
    name: str
    description: str = ""
    version: str = "0.1.0"
    skill_type: str = "builtin"
    source_type: str = "local"


@router.get("/skills")
async def list_skills(status: str | None = None, db: AsyncSession = Depends(get_db)):
    """Skill一覧"""
    query = select(Skill)
    if status:
        query = query.where(Skill.status == status)
    result = await db.execute(query.order_by(Skill.name))
    skills = result.scalars().all()
    return [
        {
            "id": str(s.id), "slug": s.slug, "name": s.name,
            "skill_type": s.skill_type, "description": s.description,
            "version": s.version, "status": s.status,
        }
        for s in skills
    ]


@router.post("/skills/install")
async def install_skill(req: SkillInstall, db: AsyncSession = Depends(get_db)):
    """Skillをインストール"""
    skill = Skill(
        id=uuid.uuid4(), slug=req.slug, name=req.name,
        skill_type=req.skill_type, description=req.description,
        version=req.version, status="experimental",
        source_type=req.source_type,
    )
    db.add(skill)
    await db.flush()
    return {"id": str(skill.id), "name": skill.name, "status": skill.status}


@router.get("/plugins")
async def list_plugins(db: AsyncSession = Depends(get_db)):
    """Plugin一覧"""
    result = await db.execute(select(Plugin).order_by(Plugin.name))
    plugins = result.scalars().all()
    return [
        {"id": str(p.id), "slug": p.slug, "name": p.name, "version": p.version, "status": p.status}
        for p in plugins
    ]


@router.post("/plugins/install")
async def install_plugin(slug: str, name: str, version: str = "0.1.0", db: AsyncSession = Depends(get_db)):
    """Pluginをインストール"""
    plugin = Plugin(
        id=uuid.uuid4(), slug=slug, name=name,
        version=version, status="experimental",
    )
    db.add(plugin)
    await db.flush()
    return {"id": str(plugin.id), "name": plugin.name}


@router.get("/extensions")
async def list_extensions(db: AsyncSession = Depends(get_db)):
    """Extension一覧"""
    result = await db.execute(select(Extension).order_by(Extension.name))
    extensions = result.scalars().all()
    return [
        {"id": str(e.id), "slug": e.slug, "name": e.name, "version": e.version, "status": e.status}
        for e in extensions
    ]


@router.post("/extensions/install")
async def install_extension(slug: str, name: str, version: str = "0.1.0", db: AsyncSession = Depends(get_db)):
    """Extensionをインストール"""
    ext = Extension(
        id=uuid.uuid4(), slug=slug, name=name,
        version=version, status="experimental",
    )
    db.add(ext)
    await db.flush()
    return {"id": str(ext.id), "name": ext.name}
