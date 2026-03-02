"""Skill Framework — SkillBase + SkillRegistry。"""

import json
import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class SkillMeta(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    input_schema: dict = {}
    output_schema: dict = {}
    requires_auth: list[dict] = []


class SkillBase(ABC):
    """全 Skill の基底クラス。"""

    def __init__(self, meta: SkillMeta, skill_dir: Path):
        self.meta = meta
        self.skill_dir = skill_dir

    @abstractmethod
    async def execute(self, input_data: dict) -> dict:
        """Skill を実行。"""
        ...


class SkillRegistry:
    """Skill の登録・管理。"""

    def __init__(self):
        self._skills: dict[str, SkillBase] = {}

    def scan_builtins(self, builtins_dir: Path) -> None:
        """builtins/ ディレクトリを走査し、全 Skill を登録。"""
        if not builtins_dir.exists():
            return
        for skill_dir in builtins_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_json = skill_dir / "SKILL.json"
            executor_py = skill_dir / "executor.py"
            if not skill_json.exists() or not executor_py.exists():
                continue
            try:
                self.register_skill(skill_dir)
            except Exception as e:
                print(f"Warning: Failed to load skill {skill_dir.name}: {e}")

    def register_skill(self, skill_dir: Path) -> None:
        """1つの Skill を登録。"""
        skill_json = skill_dir / "SKILL.json"
        executor_py = skill_dir / "executor.py"

        meta = SkillMeta(**json.loads(skill_json.read_text(encoding="utf-8")))

        spec = importlib.util.spec_from_file_location(
            f"skills.{meta.name}", executor_py
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        executor_class = getattr(module, "Executor")
        skill_instance = executor_class(meta=meta, skill_dir=skill_dir)
        self._skills[meta.name] = skill_instance

    def list_skills(self) -> list[SkillMeta]:
        """登録済み Skill のメタデータ一覧。"""
        return [s.meta for s in self._skills.values()]

    def get_skill(self, name: str) -> Optional[SkillBase]:
        """名前で Skill を取得。"""
        return self._skills.get(name)

    def has_skill(self, name: str) -> bool:
        return name in self._skills
