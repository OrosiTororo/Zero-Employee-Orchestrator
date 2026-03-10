"""External Skill Import — 外部AIエージェント・プラットフォームからのSkill取得.

以下のソースからSkillを追加可能:
  - GitHub Agent Skills リポジトリ
  - skills.sh プラットフォーム
  - OpenClaw / Claude Code のSkill形式
  - 任意のGitリポジトリ
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SkillSourceType(str, Enum):
    GITHUB_AGENT_SKILLS = "github_agent_skills"
    SKILLS_SH = "skills_sh"
    OPENCLAW = "openclaw"
    CLAUDE_CODE = "claude_code"
    GIT_REPO = "git_repo"
    URL = "url"


@dataclass
class ExternalSkillManifest:
    """外部スキルのマニフェスト."""
    name: str
    slug: str
    description: str
    version: str = "0.1.0"
    source_type: SkillSourceType = SkillSourceType.GIT_REPO
    source_uri: str = ""
    author: str = ""
    license: str = ""
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    skill_type: str = "prompt"
    config_schema: dict[str, Any] = field(default_factory=dict)
    code: str | None = None
    manifest_json: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillSearchResult:
    """スキル検索結果."""
    name: str
    slug: str
    description: str
    source_type: str
    source_uri: str
    version: str = ""
    author: str = ""
    stars: int = 0
    downloads: int = 0


class ExternalSkillImporter:
    """外部ソースからスキルをインポートするマネージャー."""

    # 既知のスキルソース
    KNOWN_SOURCES = {
        "github_agent_skills": {
            "base_url": "https://api.github.com",
            "search_path": "/search/repositories?q=topic:agent-skills",
            "description": "GitHub Agent Skills リポジトリ",
        },
        "skills_sh": {
            "base_url": "https://skills.sh",
            "api_path": "/api/v1/skills",
            "description": "skills.sh プラットフォーム",
        },
    }

    def __init__(self) -> None:
        self._cached_searches: dict[str, list[SkillSearchResult]] = {}

    async def search_skills(
        self,
        query: str,
        source_type: SkillSourceType | None = None,
        limit: int = 20,
    ) -> list[SkillSearchResult]:
        """外部ソースからスキルを検索."""
        results: list[SkillSearchResult] = []

        if source_type is None or source_type == SkillSourceType.GITHUB_AGENT_SKILLS:
            results.extend(await self._search_github(query, limit))

        if source_type is None or source_type == SkillSourceType.SKILLS_SH:
            results.extend(await self._search_skills_sh(query, limit))

        return results[:limit]

    async def _search_github(self, query: str, limit: int) -> list[SkillSearchResult]:
        """GitHub Agent Skillsリポジトリを検索."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"https://api.github.com/search/repositories?q={query}+topic:agent-skills&per_page={limit}"
                async with session.get(url, headers={"Accept": "application/vnd.github.v3+json"}) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return [
                        SkillSearchResult(
                            name=item["name"],
                            slug=_slugify(item["name"]),
                            description=item.get("description", ""),
                            source_type="github_agent_skills",
                            source_uri=item["html_url"],
                            author=item["owner"]["login"],
                            stars=item.get("stargazers_count", 0),
                        )
                        for item in data.get("items", [])[:limit]
                    ]
        except ImportError:
            logger.debug("aiohttp not available for GitHub search")
            return []
        except Exception as exc:
            logger.warning("GitHub search failed: %s", exc)
            return []

    async def _search_skills_sh(self, query: str, limit: int) -> list[SkillSearchResult]:
        """skills.sh プラットフォームを検索."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"https://skills.sh/api/v1/skills/search?q={query}&limit={limit}"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return [
                        SkillSearchResult(
                            name=item["name"],
                            slug=item.get("slug", _slugify(item["name"])),
                            description=item.get("description", ""),
                            source_type="skills_sh",
                            source_uri=f"https://skills.sh/skills/{item.get('slug', '')}",
                            version=item.get("version", ""),
                            author=item.get("author", ""),
                            downloads=item.get("downloads", 0),
                        )
                        for item in data.get("skills", [])[:limit]
                    ]
        except Exception as exc:
            logger.debug("skills.sh search failed: %s", exc)
            return []

    async def fetch_skill_manifest(
        self,
        source_type: SkillSourceType,
        source_uri: str,
    ) -> ExternalSkillManifest | None:
        """外部ソースからスキルマニフェストを取得."""
        try:
            if source_type == SkillSourceType.GIT_REPO:
                return await self._fetch_from_git(source_uri)
            if source_type == SkillSourceType.GITHUB_AGENT_SKILLS:
                return await self._fetch_from_github(source_uri)
            if source_type == SkillSourceType.CLAUDE_CODE:
                return await self._fetch_claude_code_skill(source_uri)
            if source_type == SkillSourceType.OPENCLAW:
                return await self._fetch_openclaw_skill(source_uri)
            if source_type == SkillSourceType.URL:
                return await self._fetch_from_url(source_uri)
        except Exception as exc:
            logger.error("Failed to fetch skill manifest from %s: %s", source_uri, exc)
        return None

    async def _fetch_from_git(self, repo_url: str) -> ExternalSkillManifest | None:
        """Gitリポジトリからスキルマニフェストを取得."""
        # manifest.json または skill.json を探す
        try:
            import aiohttp
            raw_url = _git_to_raw_url(repo_url)
            async with aiohttp.ClientSession() as session:
                for manifest_name in ["manifest.json", "skill.json", "agent-skill.json"]:
                    url = f"{raw_url}/{manifest_name}"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return ExternalSkillManifest(
                                name=data.get("name", ""),
                                slug=data.get("slug", _slugify(data.get("name", ""))),
                                description=data.get("description", ""),
                                version=data.get("version", "0.1.0"),
                                source_type=SkillSourceType.GIT_REPO,
                                source_uri=repo_url,
                                author=data.get("author", ""),
                                tags=data.get("tags", []),
                                manifest_json=data,
                            )
        except Exception as exc:
            logger.debug("Git fetch failed: %s", exc)
        return None

    async def _fetch_from_github(self, repo_url: str) -> ExternalSkillManifest | None:
        return await self._fetch_from_git(repo_url)

    async def _fetch_claude_code_skill(self, source_uri: str) -> ExternalSkillManifest | None:
        """Claude Code形式のスキルを変換して取得."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(source_uri) as resp:
                    if resp.status != 200:
                        return None
                    content = await resp.text()
                    # Claude Code skill format: YAML/JSON with prompt + tools
                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError:
                        data = {"name": "imported-skill", "prompt": content}

                    return ExternalSkillManifest(
                        name=data.get("name", "claude-code-skill"),
                        slug=_slugify(data.get("name", "claude-code-skill")),
                        description=data.get("description", "Claude Code imported skill"),
                        source_type=SkillSourceType.CLAUDE_CODE,
                        source_uri=source_uri,
                        skill_type="prompt",
                        code=data.get("prompt", content),
                        manifest_json=data,
                    )
        except Exception as exc:
            logger.debug("Claude Code skill fetch failed: %s", exc)
        return None

    async def _fetch_openclaw_skill(self, source_uri: str) -> ExternalSkillManifest | None:
        """OpenClaw形式のスキルを変換して取得."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(source_uri) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    return ExternalSkillManifest(
                        name=data.get("name", "openclaw-skill"),
                        slug=_slugify(data.get("name", "openclaw-skill")),
                        description=data.get("description", ""),
                        source_type=SkillSourceType.OPENCLAW,
                        source_uri=source_uri,
                        skill_type=data.get("type", "prompt"),
                        manifest_json=data,
                    )
        except Exception as exc:
            logger.debug("OpenClaw skill fetch failed: %s", exc)
        return None

    async def _fetch_from_url(self, url: str) -> ExternalSkillManifest | None:
        """任意のURLからスキルを取得."""
        return await self._fetch_from_git(url)

    def to_skill_create_data(self, manifest: ExternalSkillManifest) -> dict[str, Any]:
        """マニフェストをSkillCreate用のデータに変換."""
        return {
            "slug": manifest.slug,
            "name": manifest.name,
            "skill_type": manifest.skill_type,
            "description": manifest.description,
            "version": manifest.version,
            "source_type": manifest.source_type.value,
            "source_uri": manifest.source_uri,
            "manifest_json": manifest.manifest_json,
        }


def _slugify(text: str) -> str:
    """テキストをslugに変換."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:120]


def _git_to_raw_url(repo_url: str) -> str:
    """GitHubリポジトリURLをraw content URLに変換."""
    if "github.com" in repo_url:
        parts = repo_url.rstrip("/").replace("https://github.com/", "").split("/")
        if len(parts) >= 2:
            return f"https://raw.githubusercontent.com/{parts[0]}/{parts[1]}/main"
    return repo_url


# Global singleton
skill_importer = ExternalSkillImporter()


@dataclass
class ExternalPluginManifest:
    """外部プラグインのマニフェスト."""

    name: str
    slug: str
    description: str
    version: str = "0.1.0"
    source_uri: str = ""
    author: str = ""
    license: str = ""
    tags: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    manifest_json: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginSearchResult:
    """プラグイン検索結果."""

    name: str
    slug: str
    description: str
    source_uri: str
    version: str = ""
    author: str = ""
    stars: int = 0
    downloads: int = 0


class ExternalPluginImporter:
    """外部GitHubリポジトリからプラグインをインポートするマネージャー."""

    # 既知のプラグインソース
    KNOWN_SOURCES = {
        "github": {
            "base_url": "https://api.github.com",
            "search_topics": ["zeo-plugin", "ai-orchestrator-plugin"],
            "description": "GitHub Plugin リポジトリ",
        },
        "community_registry": {
            "base_url": "https://plugins.zeo.dev",
            "api_path": "/api/v1/plugins",
            "description": "コミュニティプラグインレジストリ",
        },
    }

    def __init__(self) -> None:
        self._cached_searches: dict[str, list[PluginSearchResult]] = {}

    async def search_plugins(
        self,
        query: str,
        limit: int = 20,
    ) -> list[PluginSearchResult]:
        """GitHubおよびコミュニティレジストリからプラグインを検索."""
        cache_key = f"{query}:{limit}"
        if cache_key in self._cached_searches:
            return self._cached_searches[cache_key]

        results: list[PluginSearchResult] = []
        results.extend(await self._search_github(query, limit))
        results.extend(await self._search_community_registry(query, limit))

        results = results[:limit]
        self._cached_searches[cache_key] = results
        return results

    async def _search_github(
        self, query: str, limit: int,
    ) -> list[PluginSearchResult]:
        """GitHub リポジトリをzeo-plugin / ai-orchestrator-pluginトピックで検索."""
        results: list[PluginSearchResult] = []
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                for topic in ("zeo-plugin", "ai-orchestrator-plugin"):
                    url = (
                        f"https://api.github.com/search/repositories"
                        f"?q={query}+topic:{topic}&per_page={limit}"
                    )
                    async with session.get(
                        url,
                        headers={"Accept": "application/vnd.github.v3+json"},
                    ) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                        for item in data.get("items", [])[:limit]:
                            results.append(
                                PluginSearchResult(
                                    name=item["name"],
                                    slug=_slugify(item["name"]),
                                    description=item.get("description", ""),
                                    source_uri=item["html_url"],
                                    author=item["owner"]["login"],
                                    stars=item.get("stargazers_count", 0),
                                )
                            )
        except ImportError:
            logger.debug("aiohttp not available for GitHub plugin search")
        except Exception as exc:
            logger.warning("GitHub plugin search failed: %s", exc)

        # 重複排除（同一slug）
        seen: set[str] = set()
        unique: list[PluginSearchResult] = []
        for r in results:
            if r.slug not in seen:
                seen.add(r.slug)
                unique.append(r)
        return unique[:limit]

    async def _search_community_registry(
        self, query: str, limit: int,
    ) -> list[PluginSearchResult]:
        """コミュニティプラグインレジストリを検索."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                url = f"https://plugins.zeo.dev/api/v1/plugins/search?q={query}&limit={limit}"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return [
                        PluginSearchResult(
                            name=item["name"],
                            slug=item.get("slug", _slugify(item["name"])),
                            description=item.get("description", ""),
                            source_uri=item.get("source_uri", ""),
                            version=item.get("version", ""),
                            author=item.get("author", ""),
                            downloads=item.get("downloads", 0),
                        )
                        for item in data.get("plugins", [])[:limit]
                    ]
        except Exception as exc:
            logger.debug("Community plugin registry search failed: %s", exc)
            return []

    async def fetch_plugin_manifest(
        self,
        source_uri: str,
    ) -> ExternalPluginManifest | None:
        """GitHubリポジトリからプラグインマニフェスト(plugin.json / manifest.json)を取得."""
        try:
            import aiohttp

            raw_url = _git_to_raw_url(source_uri)
            async with aiohttp.ClientSession() as session:
                for manifest_name in ("plugin.json", "manifest.json"):
                    url = f"{raw_url}/{manifest_name}"
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                        return ExternalPluginManifest(
                            name=data.get("name", ""),
                            slug=data.get("slug", _slugify(data.get("name", ""))),
                            description=data.get("description", ""),
                            version=data.get("version", "0.1.0"),
                            source_uri=source_uri,
                            author=data.get("author", ""),
                            license=data.get("license", ""),
                            tags=data.get("tags", []),
                            skills=data.get("skills", []),
                            config_schema=data.get("config_schema", {}),
                            manifest_json=data,
                        )
        except ImportError:
            logger.debug("aiohttp not available for plugin manifest fetch")
        except Exception as exc:
            logger.error(
                "Failed to fetch plugin manifest from %s: %s", source_uri, exc,
            )
        return None

    def to_plugin_create_data(
        self, manifest: ExternalPluginManifest,
    ) -> dict[str, Any]:
        """マニフェストをPluginCreate用のデータに変換."""
        return {
            "slug": manifest.slug,
            "name": manifest.name,
            "description": manifest.description,
            "version": manifest.version,
            "source_uri": manifest.source_uri,
            "author": manifest.author,
            "license": manifest.license,
            "tags": manifest.tags,
            "skills": manifest.skills,
            "config_schema": manifest.config_schema,
            "manifest_json": manifest.manifest_json,
        }


# Global singleton
plugin_importer = ExternalPluginImporter()
