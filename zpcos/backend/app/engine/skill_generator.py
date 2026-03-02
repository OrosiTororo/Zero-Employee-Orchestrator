"""Skill Auto-Generation Engine.
LLM に SKILL.json + executor.py を生成させ、安全性検証後に登録。
"""

import ast
import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from app.gateway import call_llm
from app.main import resource_path


class SkillGenerationResult(BaseModel):
    skill_json: dict
    code: str
    safety_passed: bool
    safety_issues: list[str] = []
    registered: bool = False


IMPORT_WHITELIST = {"httpx", "json", "re", "datetime", "pydantic", "math", "typing", "asyncio"}
FUNCTION_BLACKLIST = {"eval", "exec", "compile", "__import__", "os.system", "subprocess"}


def _validate_ast(code: str) -> tuple[bool, list[str]]:
    """AST パースで安全性検証。"""
    issues = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, [f"Syntax error: {e}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
                if module not in IMPORT_WHITELIST and module not in ("app",):
                    issues.append(f"Forbidden import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split(".")[0]
                if module not in IMPORT_WHITELIST and module not in ("app",):
                    issues.append(f"Forbidden import: {node.module}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in FUNCTION_BLACKLIST:
                    issues.append(f"Forbidden function: {node.func.id}")
            elif isinstance(node.func, ast.Attribute):
                full = f"{getattr(node.func.value, 'id', '')}.{node.func.attr}"
                if full in FUNCTION_BLACKLIST:
                    issues.append(f"Forbidden function: {full}")

    return len(issues) == 0, issues


async def generate_skill(
    description: str,
    skill_registry=None,
) -> SkillGenerationResult:
    """自然言語の説明からSkillを自動生成。"""
    prompt = f"""以下の説明に基づいて、ZPCOS Skill を生成してください。

説明: {description}

2つのファイルを生成:

1. SKILL.json（メタデータ）:
{{
  "name": "skill-name",
  "description": "...",
  "version": "1.0.0",
  "input_schema": {{}},
  "output_schema": {{}},
  "requires_auth": []
}}

2. executor.py（実行コード）:
```python
from app.skills.framework import SkillBase
from app.gateway import call_llm

class Executor(SkillBase):
    async def execute(self, input_data: dict) -> dict:
        ...
```

利用可能なインポート: httpx, json, re, datetime, pydantic, math, typing, asyncio, app.gateway, app.skills.framework

以下のJSON形式で返してください:
{{"skill_json": {{...}}, "code": "..."}}
JSON のみを返してください。"""

    response = await call_llm(
        messages=[{"role": "user", "content": prompt}],
        model_group="quality",
    )
    content = response.choices[0].message.content
    if "```" in content:
        content = content.split("```json")[-1].split("```")[0]

    try:
        data = json.loads(content.strip())
    except json.JSONDecodeError:
        return SkillGenerationResult(
            skill_json={}, code="", safety_passed=False,
            safety_issues=["Failed to parse LLM response"],
        )

    skill_json = data.get("skill_json", {})
    code = data.get("code", "")

    safe, issues = _validate_ast(code)

    result = SkillGenerationResult(
        skill_json=skill_json, code=code,
        safety_passed=safe, safety_issues=issues,
    )

    if safe and skill_registry and skill_json.get("name"):
        # Skill を登録
        builtins_dir = resource_path("skills/builtins")
        skill_dir = Path(builtins_dir) / skill_json["name"].replace("-", "_")
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.json").write_text(
            json.dumps(skill_json, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (skill_dir / "executor.py").write_text(code, encoding="utf-8")
        try:
            skill_registry.register_skill(skill_dir)
            result.registered = True
        except Exception:
            pass

    return result
