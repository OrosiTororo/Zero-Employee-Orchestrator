"""Skill Framework テスト"""

import pytest
from pathlib import Path

from app.skills.framework import SkillRegistry, SkillMeta


def test_registry_init():
    registry = SkillRegistry()
    assert len(registry.list_skills()) == 0


def test_scan_builtins():
    registry = SkillRegistry()
    builtins_dir = Path(__file__).parent.parent / "app" / "skills" / "builtins"
    if builtins_dir.exists():
        registry.scan_builtins(builtins_dir)
        skills = registry.list_skills()
        names = [s.name for s in skills]
        assert "local-context" in names


def test_get_nonexistent_skill():
    registry = SkillRegistry()
    skill = registry.get_skill("nonexistent")
    assert skill is None
