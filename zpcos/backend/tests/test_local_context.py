"""Local Context Skill テスト"""

import json
from pathlib import Path

import pytest


def test_skill_json_exists():
    skill_dir = Path(__file__).parent.parent / "app" / "skills" / "builtins" / "local_context"
    skill_json = skill_dir / "SKILL.json"
    assert skill_json.exists()

    data = json.loads(skill_json.read_text(encoding="utf-8"))
    assert data["name"] == "local-context"
    assert "security" in data


def test_skill_json_has_security():
    skill_dir = Path(__file__).parent.parent / "app" / "skills" / "builtins" / "local_context"
    data = json.loads((skill_dir / "SKILL.json").read_text(encoding="utf-8"))
    sec = data["security"]
    assert "allowed_dirs_config" in sec


def test_executor_exists():
    skill_dir = Path(__file__).parent.parent / "app" / "skills" / "builtins" / "local_context"
    executor = skill_dir / "executor.py"
    assert executor.exists()
