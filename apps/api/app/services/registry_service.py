"""Plugin / Extension 管理サービス — CRUD・システム保護.

Plugin と Extension の追加・更新・削除・有効/無効化を管理する。
is_system_protected=True の項目は削除・無効化できない。
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence

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
        raise ValueError(f"システム必須プラグイン '{plugin.slug}' は無効化できません")

    for key, value in updates.items():
        setattr(plugin, key, value)
    await db.flush()
    logger.info("Plugin 更新: %s", plugin.slug)
    return plugin


async def delete_plugin(db: AsyncSession, plugin_id: uuid.UUID) -> tuple[bool, str]:
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
        raise ValueError(f"システム必須拡張 '{ext.slug}' は無効化できません")

    for key, value in updates.items():
        setattr(ext, key, value)
    await db.flush()
    logger.info("Extension 更新: %s", ext.slug)
    return ext


async def delete_extension(db: AsyncSession, ext_id: uuid.UUID) -> tuple[bool, str]:
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


# ---------------------------------------------------------------------------
# Built-in Plugins & Extensions — seeded on application startup
# ---------------------------------------------------------------------------

BUILTIN_PLUGINS: list[dict] = [
    {
        "slug": "browser-use",
        "name": "Browser Use",
        "description": "LLM autonomous browser control — AI sees screenshots and DOM, decides clicks/typing",
    },
    {
        "slug": "ai-secretary",
        "name": "AI Secretary",
        "description": "Personal AI secretary for scheduling, task triage, and daily briefings",
    },
    {
        "slug": "ai-avatar",
        "name": "AI Avatar",
        "description": "AI-driven avatar that co-evolves with the user's work patterns",
    },
    {
        "slug": "research",
        "name": "Research Assistant",
        "description": "Multi-source research with fact-checking and citation management",
    },
    {
        "slug": "backoffice",
        "name": "Back Office",
        "description": "Accounting, invoicing, and administrative automation",
    },
    {
        "slug": "ai-self-improvement",
        "name": "AI Self-Improvement",
        "description": "Continuous learning loop for AI agent skill enhancement",
    },
    {
        "slug": "slack-bot",
        "name": "Slack Bot",
        "description": "Slack workspace integration for task management and notifications",
    },
    {
        "slug": "discord-bot",
        "name": "Discord Bot",
        "description": "Discord server integration for community task management",
    },
    {
        "slug": "line-bot",
        "name": "LINE Bot",
        "description": "LINE messaging integration for task management",
    },
    {
        "slug": "youtube",
        "name": "YouTube Manager",
        "description": "YouTube content management — upload, scheduling, analytics",
    },
    # Role-based plugin packs (inspired by Claude Cowork's role plugins)
    {
        "slug": "sales-pack",
        "name": "Sales Pack",
        "description": "Lead scoring, competitive analysis, CRM sync, pipeline reports, outreach drafting",
    },
    {
        "slug": "finance-pack",
        "name": "Finance Pack",
        "description": "Expense analysis, budget tracking, invoice processing, financial reporting",
    },
    {
        "slug": "hr-pack",
        "name": "HR Pack",
        "description": "Job description drafting, resume screening, onboarding checklists, survey analysis",
    },
    {
        "slug": "legal-pack",
        "name": "Legal Pack",
        "description": "Contract review, clause extraction, compliance checking, NDA drafting",
    },
    {
        "slug": "marketing-pack",
        "name": "Marketing Pack",
        "description": "Content calendar, SEO analysis, social scheduling, campaign tracking",
    },
    {
        "slug": "customer-support-pack",
        "name": "Customer Support Pack",
        "description": "Ticket triage, FAQ auto-response, escalation routing, sentiment analysis",
    },
    {
        "slug": "ai-ceo",
        "name": "AI CEO Plugin",
        "description": (
            "Claude-Code-style AI CEO pattern: a senior reasoning agent decomposes operator "
            "directives into weekly plans and delegates to CMO/CTO/COO subagents under "
            "human board-level approval."
        ),
    },
    {
        "slug": "knowledge-wiki",
        "name": "Knowledge Wiki Plugin",
        "description": (
            "Karpathy-style LLM Wiki + arscontexta context engine bundled together. "
            "Adds /ingest, /query, /lint, /ralph, and /plan commands backed by a "
            "Markdown vault any AI can read (no vendor lock-in)."
        ),
    },
]

BUILTIN_EXTENSIONS: list[dict] = [
    {
        "slug": "mcp",
        "name": "MCP Connection",
        "description": "Model Context Protocol — connect with MCP-compatible tools and servers",
    },
    {
        "slug": "oauth",
        "name": "OAuth Provider",
        "description": "OAuth 2.0 authentication for third-party service connections",
    },
    {
        "slug": "notifications",
        "name": "Notifications",
        "description": "Push notifications, email alerts, and webhook notifications",
    },
    {
        "slug": "language-pack",
        "name": "Language Pack",
        "description": "Additional language support beyond the 6 built-in languages",
    },
    {
        "slug": "browser-assist",
        "name": "Browser Assist",
        "description": "Chrome extension for overlay chat and real-time screen sharing",
    },
    {
        "slug": "obsidian",
        "name": "Obsidian",
        "description": "Obsidian vault integration for knowledge base and note-taking",
    },
    {
        "slug": "notion",
        "name": "Notion",
        "description": "Notion workspace integration for documents and databases",
    },
    {
        "slug": "logseq",
        "name": "Logseq",
        "description": "Logseq graph integration for knowledge management",
    },
    {
        "slug": "joplin",
        "name": "Joplin",
        "description": "Joplin integration for note-taking and to-do management",
    },
    {
        "slug": "google-workspace",
        "name": "Google Workspace",
        "description": "Google Docs, Sheets, Drive, Calendar, Gmail integration",
    },
    {
        "slug": "microsoft-365",
        "name": "Microsoft 365",
        "description": "Microsoft 365, Teams, OneDrive, Outlook integration",
    },
]


async def ensure_system_plugins(db: AsyncSession) -> list[Plugin]:
    """Seed built-in plugins on startup if they don't exist yet."""
    created: list[Plugin] = []
    for builtin in BUILTIN_PLUGINS:
        existing = await get_plugin_by_slug(db, builtin["slug"])
        if existing is None:
            plugin = await create_plugin(
                db,
                PluginCreate(
                    slug=builtin["slug"],
                    name=builtin["name"],
                    description=builtin["description"],
                    version="0.1.0",
                ),
                is_system_protected=True,
            )
            created.append(plugin)
    if created:
        logger.info("Seeded %d built-in plugins", len(created))
    return created


async def ensure_system_extensions(db: AsyncSession) -> list[Extension]:
    """Seed built-in extensions on startup if they don't exist yet."""
    created: list[Extension] = []
    for builtin in BUILTIN_EXTENSIONS:
        existing = await get_extension_by_slug(db, builtin["slug"])
        if existing is None:
            ext = await create_extension(
                db,
                ExtensionCreate(
                    slug=builtin["slug"],
                    name=builtin["name"],
                    description=builtin["description"],
                    version="0.1.0",
                ),
                is_system_protected=True,
            )
            created.append(ext)
    if created:
        logger.info("Seeded %d built-in extensions", len(created))
    return created
