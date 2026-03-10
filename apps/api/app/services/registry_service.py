"""Plugin / Extension 管理サービス — CRUD・システム保護.

Plugin と Extension の追加・更新・削除・有効/無効化を管理する。
is_system_protected=True の項目は削除・無効化できない。
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Extension, Plugin
from app.schemas.registry import (
    ExtensionCreate,
    ExtensionUpdate,
    PluginCreate,
    PluginUpdate,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Plugin CRUD
# ---------------------------------------------------------------------------

async def list_plugins(
    db: AsyncSession,
    *,
    status: str | None = None,
    include_disabled: bool = False,
) -> Sequence[Plugin]:
    """Plugin 一覧を取得する."""
    query = select(Plugin)
    if status:
        query = query.where(Plugin.status == status)
    if not include_disabled:
        query = query.where(Plugin.enabled.is_(True))
    result = await db.execute(query.order_by(Plugin.name))
    return result.scalars().all()


async def get_plugin(db: AsyncSession, plugin_id: uuid.UUID) -> Plugin | None:
    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    return result.scalar_one_or_none()


async def get_plugin_by_slug(db: AsyncSession, slug: str) -> Plugin | None:
    result = await db.execute(select(Plugin).where(Plugin.slug == slug))
    return result.scalar_one_or_none()


async def create_plugin(
    db: AsyncSession,
    data: PluginCreate,
    *,
    is_system_protected: bool = False,
) -> Plugin:
    plugin = Plugin(
        id=uuid.uuid4(),
        slug=data.slug,
        name=data.name,
        description=data.description,
        version=data.version,
        status="experimental",
        manifest_json=data.manifest_json,
        is_system_protected=is_system_protected,
    )
    db.add(plugin)
    await db.flush()
    logger.info("Plugin 作成: %s (%s)", plugin.name, plugin.slug)
    return plugin


async def update_plugin(
    db: AsyncSession,
    plugin_id: uuid.UUID,
    data: PluginUpdate,
) -> Plugin | None:
    plugin = await get_plugin(db, plugin_id)
    if plugin is None:
        return None

    updates = data.model_dump(exclude_unset=True)

    if plugin.is_system_protected and updates.get("enabled") is False:
        raise ValueError(
            f"システム必須プラグイン '{plugin.slug}' は無効化できません"
        )

    for key, value in updates.items():
        setattr(plugin, key, value)
    await db.flush()
    logger.info("Plugin 更新: %s", plugin.slug)
    return plugin


async def delete_plugin(
    db: AsyncSession, plugin_id: uuid.UUID
) -> tuple[bool, str]:
    plugin = await get_plugin(db, plugin_id)
    if plugin is None:
        return False, "プラグインが見つかりません"

    if plugin.is_system_protected:
        return False, (
            f"システム必須プラグイン '{plugin.slug}' は削除できません。"
            "このプラグインはシステムの正常動作に必要です。"
        )

    await db.delete(plugin)
    await db.flush()
    logger.info("Plugin 削除: %s", plugin.slug)
    return True, f"プラグイン '{plugin.name}' を削除しました"


# ---------------------------------------------------------------------------
# Extension CRUD
# ---------------------------------------------------------------------------

async def list_extensions(
    db: AsyncSession,
    *,
    status: str | None = None,
    include_disabled: bool = False,
) -> Sequence[Extension]:
    query = select(Extension)
    if status:
        query = query.where(Extension.status == status)
    if not include_disabled:
        query = query.where(Extension.enabled.is_(True))
    result = await db.execute(query.order_by(Extension.name))
    return result.scalars().all()


async def get_extension(db: AsyncSession, ext_id: uuid.UUID) -> Extension | None:
    result = await db.execute(select(Extension).where(Extension.id == ext_id))
    return result.scalar_one_or_none()


async def get_extension_by_slug(db: AsyncSession, slug: str) -> Extension | None:
    result = await db.execute(select(Extension).where(Extension.slug == slug))
    return result.scalar_one_or_none()


async def create_extension(
    db: AsyncSession,
    data: ExtensionCreate,
    *,
    is_system_protected: bool = False,
) -> Extension:
    ext = Extension(
        id=uuid.uuid4(),
        slug=data.slug,
        name=data.name,
        description=data.description,
        version=data.version,
        status="experimental",
        manifest_json=data.manifest_json,
        is_system_protected=is_system_protected,
    )
    db.add(ext)
    await db.flush()
    logger.info("Extension 作成: %s (%s)", ext.name, ext.slug)
    return ext


async def update_extension(
    db: AsyncSession,
    ext_id: uuid.UUID,
    data: ExtensionUpdate,
) -> Extension | None:
    ext = await get_extension(db, ext_id)
    if ext is None:
        return None

    updates = data.model_dump(exclude_unset=True)

    if ext.is_system_protected and updates.get("enabled") is False:
        raise ValueError(
            f"システム必須拡張 '{ext.slug}' は無効化できません"
        )

    for key, value in updates.items():
        setattr(ext, key, value)
    await db.flush()
    logger.info("Extension 更新: %s", ext.slug)
    return ext


async def delete_extension(
    db: AsyncSession, ext_id: uuid.UUID
) -> tuple[bool, str]:
    ext = await get_extension(db, ext_id)
    if ext is None:
        return False, "拡張が見つかりません"

    if ext.is_system_protected:
        return False, (
            f"システム必須拡張 '{ext.slug}' は削除できません。"
            "この拡張はシステムの正常動作に必要です。"
        )

    await db.delete(ext)
    await db.flush()
    logger.info("Extension 削除: %s", ext.slug)
    return True, f"拡張 '{ext.name}' を削除しました"
