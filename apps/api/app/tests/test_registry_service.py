"""Tests for registry_service (Plugin + Extension CRUD)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.registry import (
    ExtensionCreate,
    ExtensionUpdate,
    PluginCreate,
    PluginUpdate,
)
from app.services import registry_service


@pytest.mark.asyncio
async def test_create_and_get_plugin(db_session: AsyncSession):
    plugin = await registry_service.create_plugin(
        db=db_session,
        data=PluginCreate(slug="demo", name="Demo Plugin"),
    )
    await db_session.commit()
    assert plugin.slug == "demo"
    assert plugin.status == "experimental"

    fetched = await registry_service.get_plugin_by_slug(db_session, "demo")
    assert fetched is not None
    assert fetched.slug == "demo"


@pytest.mark.asyncio
async def test_list_plugins_excludes_disabled_by_default(db_session: AsyncSession):
    await registry_service.create_plugin(db=db_session, data=PluginCreate(slug="on", name="On"))
    disabled = await registry_service.create_plugin(
        db=db_session, data=PluginCreate(slug="off", name="Off")
    )
    disabled.enabled = False
    await db_session.commit()

    listed = await registry_service.list_plugins(db_session)
    slugs = {p.slug for p in listed}
    assert "on" in slugs
    assert "off" not in slugs

    listed_all = await registry_service.list_plugins(db_session, include_disabled=True)
    slugs_all = {p.slug for p in listed_all}
    assert {"on", "off"}.issubset(slugs_all)


@pytest.mark.asyncio
async def test_update_plugin_applies_partial_fields(db_session: AsyncSession):
    plugin = await registry_service.create_plugin(
        db=db_session, data=PluginCreate(slug="p1", name="Original")
    )
    await db_session.commit()
    updated = await registry_service.update_plugin(
        db=db_session,
        plugin_id=plugin.id,
        data=PluginUpdate(name="Renamed"),
    )
    assert updated is not None
    assert updated.name == "Renamed"
    # Unchanged fields stay as-is
    assert updated.slug == "p1"


@pytest.mark.asyncio
async def test_system_protected_plugin_cannot_be_disabled(db_session: AsyncSession):
    plugin = await registry_service.create_plugin(
        db=db_session,
        data=PluginCreate(slug="core", name="Core"),
        is_system_protected=True,
    )
    await db_session.commit()
    with pytest.raises(ValueError):
        await registry_service.update_plugin(
            db=db_session,
            plugin_id=plugin.id,
            data=PluginUpdate(enabled=False),
        )


@pytest.mark.asyncio
async def test_system_protected_plugin_cannot_be_deleted(db_session: AsyncSession):
    plugin = await registry_service.create_plugin(
        db=db_session,
        data=PluginCreate(slug="core2", name="Core 2"),
        is_system_protected=True,
    )
    await db_session.commit()
    ok, msg = await registry_service.delete_plugin(db_session, plugin.id)
    assert ok is False
    assert "システム必須" in msg or "system" in msg.lower()


@pytest.mark.asyncio
async def test_delete_missing_plugin_returns_false(db_session: AsyncSession):
    ok, msg = await registry_service.delete_plugin(db_session, uuid.uuid4())
    assert ok is False
    assert msg


@pytest.mark.asyncio
async def test_create_and_list_extensions(db_session: AsyncSession):
    await registry_service.create_extension(
        db=db_session,
        data=ExtensionCreate(slug="ext-a", name="Ext A"),
    )
    await db_session.commit()
    listed = await registry_service.list_extensions(db_session)
    assert any(e.slug == "ext-a" for e in listed)


@pytest.mark.asyncio
async def test_update_extension_respects_system_protection(db_session: AsyncSession):
    ext = await registry_service.create_extension(
        db=db_session,
        data=ExtensionCreate(slug="guarded", name="Guarded"),
        is_system_protected=True,
    )
    await db_session.commit()
    with pytest.raises(ValueError):
        await registry_service.update_extension(
            db=db_session,
            ext_id=ext.id,
            data=ExtensionUpdate(enabled=False),
        )
