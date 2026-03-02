"""Skill Registry — コミュニティSkillの公開・検索・インストール。"""

import json
import os
from pathlib import Path
from pydantic import BaseModel


class SkillPackage(BaseModel):
    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    downloads: int = 0
    rating: float = 0.0
    tags: list[str] = []


_registry_path = Path(
    os.environ.get("APPDATA", Path.home() / ".config")
) / "zpcos" / "skill_registry.json"


def _load_registry() -> list[SkillPackage]:
    if not _registry_path.exists():
        return []
    data = json.loads(_registry_path.read_text(encoding="utf-8"))
    return [SkillPackage(**p) for p in data]


def _save_registry(packages: list[SkillPackage]) -> None:
    _registry_path.parent.mkdir(parents=True, exist_ok=True)
    _registry_path.write_text(
        json.dumps([p.model_dump() for p in packages], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def search_registry(query: str) -> list[SkillPackage]:
    """レジストリからSkillを検索。"""
    packages = _load_registry()
    query_lower = query.lower()
    return [
        p for p in packages
        if query_lower in p.name.lower()
        or query_lower in p.description.lower()
        or any(query_lower in t.lower() for t in p.tags)
    ]


async def publish_skill(skill_dir: str, author: str = "") -> SkillPackage:
    """Skillをパッケージ化して公開。"""
    skill_json_path = Path(skill_dir) / "SKILL.json"
    if not skill_json_path.exists():
        raise FileNotFoundError(f"SKILL.json not found in {skill_dir}")

    data = json.loads(skill_json_path.read_text(encoding="utf-8"))
    pkg = SkillPackage(
        name=data["name"],
        version=data.get("version", "1.0.0"),
        author=author,
        description=data.get("description", ""),
        tags=data.get("tags", []),
    )

    packages = _load_registry()
    # 既存パッケージの更新
    packages = [p for p in packages if p.name != pkg.name]
    packages.append(pkg)
    _save_registry(packages)
    return pkg


async def install_skill(skill_name: str) -> bool:
    """コミュニティSkillをインストール。"""
    packages = _load_registry()
    for p in packages:
        if p.name == skill_name:
            p.downloads += 1
            _save_registry(packages)
            return True
    return False


async def get_popular(limit: int = 10) -> list[SkillPackage]:
    """人気Skill一覧。"""
    packages = _load_registry()
    packages.sort(key=lambda p: p.downloads, reverse=True)
    return packages[:limit]
