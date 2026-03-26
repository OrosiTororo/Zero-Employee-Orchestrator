"""Skill management service -- CRUD, natural language generation, and system protection.

Provides skill creation from natural language, safety checks, and protection of system-required skills.
"""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.schemas.registry import (
    RegistrySafetyReport,
    SkillCreate,
    SkillGenerateRequest,
    SkillGenerateResponse,
    SkillUpdate,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# システム必須スキル — 削除・無効化不可
# ---------------------------------------------------------------------------

SYSTEM_PROTECTED_SLUGS: set[str] = frozenset(
    {
        "spec-writer",
        "plan-writer",
        "task-breakdown",
        "review-assistant",
        "artifact-summarizer",
        "local-context",
    }
)

# ---------------------------------------------------------------------------
# 安全性チェック用パターン
# ---------------------------------------------------------------------------

_DANGEROUS_PATTERNS: list[tuple[str, str, str]] = [
    (r"\bos\.system\b", "os.system の呼び出し", "has_dangerous_code"),
    (r"\bsubprocess\b", "subprocess モジュールの使用", "has_dangerous_code"),
    (r"\b__import__\b", "動的インポート (__import__)", "has_dangerous_code"),
    (r"\beval\s*\(", "eval() の使用", "has_dangerous_code"),
    (r"\bexec\s*\(", "exec() の使用", "has_dangerous_code"),
    (r"\bcompile\s*\(", "compile() の使用", "has_dangerous_code"),
    (r"\bopen\s*\(.*(w|a)", "ファイル書き込み操作", "has_dangerous_code"),
    (
        r"\brequests\.(post|put|delete|patch)\b",
        "外部 HTTP 送信",
        "has_external_communication",
    ),
    (
        r"\bhttpx\.(post|put|delete|patch)\b",
        "外部 HTTP 送信",
        "has_external_communication",
    ),
    (r"\baiohttp\b", "外部 HTTP 通信ライブラリ", "has_external_communication"),
    (r"\bsmtplib\b", "メール送信", "has_external_communication"),
    (r"\bsocket\b", "ソケット通信", "has_external_communication"),
    (
        r"(api_key|secret|password|token|credential)",
        "認証情報へのアクセス",
        "has_credential_access",
    ),
    (r"\bos\.environ\b", "環境変数アクセス", "has_credential_access"),
    (r"\bshutil\.rmtree\b", "ディレクトリ削除", "has_destructive_operations"),
    (r"\bos\.remove\b", "ファイル削除", "has_destructive_operations"),
    (r"\bos\.unlink\b", "ファイル削除", "has_destructive_operations"),
    (
        r"DROP\s+TABLE|DELETE\s+FROM|TRUNCATE",
        "SQL 破壊操作",
        "has_destructive_operations",
    ),
]


def analyze_code_safety(code: str) -> RegistrySafetyReport:
    """生成されたスキルコードの安全性を静的解析する."""
    report = RegistrySafetyReport()
    issues: list[str] = []
    permissions: list[str] = []
    externals: list[str] = []

    for pattern, desc, category in _DANGEROUS_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            setattr(report, category, True)
            issues.append(desc)
            if category == "has_external_communication":
                externals.append(desc)
            if category == "has_credential_access":
                permissions.append("credential_access")
            if category == "has_dangerous_code":
                permissions.append("system_access")

    report.required_permissions = list(set(permissions))
    report.external_connections = externals

    if report.has_destructive_operations or report.has_credential_access:
        report.risk_level = "high"
    elif report.has_external_communication or report.has_dangerous_code:
        report.risk_level = "medium"
    else:
        report.risk_level = "low"

    report.summary = (
        f"検出された問題: {len(issues)} 件" if issues else "安全性の問題は検出されませんでした"
    )

    return report


# ---------------------------------------------------------------------------
# 自然言語 → Skill マニフェスト + コード生成
# ---------------------------------------------------------------------------

_SKILL_GENERATE_SYSTEM_PROMPT = """\
あなたは Zero-Employee Orchestrator のスキル生成エンジンです。
ユーザーが自然言語で説明したスキルの機能から、以下の2つを生成してください。

1. **skill.json** — スキルマニフェスト (JSON)
   必須フィールド:
   - slug: スキルの一意識別子 (kebab-case, 英語)
   - name: スキル名
   - description: 説明
   - version: "0.1.0"
   - skill_type: "custom"
   - author: "auto-generated"
   - permissions: { read_local, write_local, external_api, external_send } (各 bool)
   - required_providers: [] (必要な LLM プロバイダー)
   - estimated_cost: "low" | "medium" | "high"

2. **executor.py** — Python 実行コード
   - `async def execute(context: dict) -> dict` を必ず実装
   - context には input, local_context, provider, settings が含まれる
   - 戻り値: { status, output, artifacts, cost_usd }
   - 安全でないコード (eval, exec, subprocess, os.system) は使わないこと
   - 外部通信が不要な場合は requests/httpx を使わないこと

出力は以下の形式で返してください:

```json
{skill.json の内容}
```

```python
{executor.py の内容}
```
"""


async def generate_skill_from_description(
    request: SkillGenerateRequest,
    db: AsyncSession,
) -> SkillGenerateResponse:
    """自然言語の説明からスキルを自動生成する.

    LLM を使ってマニフェストと実行コードを生成し、安全性チェックを行う。
    LLM が利用不可の場合はテンプレートベースのフォールバックを使用する。
    """
    import json

    manifest: dict = {}
    code: str = ""

    try:
        from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

        llm_response = await llm_gateway.complete(
            CompletionRequest(
                messages=[
                    {"role": "system", "content": _SKILL_GENERATE_SYSTEM_PROMPT},
                    {"role": "user", "content": request.description},
                ],
                temperature=0.3,
                max_tokens=4096,
                mode=ExecutionMode.QUALITY,
            )
        )

        content = llm_response.content

        # JSON ブロックを抽出
        json_match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
        if json_match:
            manifest = json.loads(json_match.group(1))

        # Python ブロックを抽出
        py_match = re.search(r"```python\s*\n(.*?)\n```", content, re.DOTALL)
        if py_match:
            code = py_match.group(1)

    except Exception as exc:
        logger.warning("LLM スキル生成に失敗、テンプレートフォールバック: %s", exc)

    # LLM が失敗した場合のフォールバック: テンプレートベース生成
    if not manifest or not code:
        slug = _generate_slug(request.description)
        manifest = {
            "slug": slug,
            "name": request.description[:60],
            "description": request.description,
            "version": "0.1.0",
            "skill_type": "custom",
            "author": "auto-generated",
            "permissions": {
                "read_local": False,
                "write_local": False,
                "external_api": False,
                "external_send": False,
            },
            "required_providers": [],
            "estimated_cost": "low",
        }
        code = _generate_template_code(slug, request.description)

    # 安全性チェック
    safety_report = analyze_code_safety(code)
    safety_passed = safety_report.risk_level in ("low", "medium")
    safety_issues: list[str] = []
    if safety_report.has_dangerous_code:
        safety_issues.append("危険なコードパターンが検出されました")
    if safety_report.has_external_communication:
        safety_issues.append("外部通信が検出されました")
    if safety_report.has_credential_access:
        safety_issues.append("認証情報へのアクセスが検出されました")
    if safety_report.has_destructive_operations:
        safety_issues.append("破壊的操作が検出されました")
        safety_passed = False

    # 自動登録
    skill_id: str | None = None
    registered = False
    if request.auto_register and safety_passed:
        skill = await create_skill(
            db,
            SkillCreate(
                slug=manifest.get("slug", _generate_slug(request.description)),
                name=manifest.get("name", request.description[:60]),
                skill_type="custom",
                description=manifest.get("description", request.description),
                version=manifest.get("version", "0.1.0"),
                source_type="generated",
                manifest_json=manifest,
                policy_json={"permissions": manifest.get("permissions", {})},
            ),
            generated_code=code,
        )
        skill_id = str(skill.id)
        registered = True

    return SkillGenerateResponse(
        skill_json=manifest,
        code=code,
        safety_report=safety_report,
        safety_passed=safety_passed,
        safety_issues=safety_issues,
        registered=registered,
        skill_id=skill_id,
    )


def _generate_slug(description: str) -> str:
    """説明文から slug を生成する."""
    # 英数字とハイフン以外を除去し、kebab-case にする
    slug = re.sub(r"[^a-zA-Z0-9\s]", "", description[:40])
    slug = re.sub(r"\s+", "-", slug.strip()).lower()
    if not slug:
        slug = f"custom-skill-{uuid.uuid4().hex[:8]}"
    return slug


def _generate_template_code(slug: str, description: str) -> str:
    """テンプレートベースのスキルコードを生成する."""
    safe_desc = description.replace('"', '\\"').replace("\n", "\\n")
    return f'''"""自動生成スキル: {slug}"""


async def execute(context: dict) -> dict:
    """スキルを実行する.

    説明: {safe_desc}

    Args:
        context: 実行コンテキスト
            - input: ユーザー入力
            - local_context: ローカルファイル情報
            - provider: LLM プロバイダー
            - settings: 設定

    Returns:
        実行結果
    """
    user_input = context.get("input", "")
    provider = context.get("provider")

    # LLM に処理を委譲
    if provider:
        result = await provider.complete(
            messages=[
                {{"role": "system", "content": "{safe_desc}"}},
                {{"role": "user", "content": user_input}},
            ],
            temperature=0.7,
            max_tokens=2048,
        )
        return {{
            "status": "success",
            "output": result.content if hasattr(result, "content") else str(result),
            "artifacts": [],
            "cost_usd": 0.0,
        }}

    return {{
        "status": "success",
        "output": f"スキル \\"{slug}\\" が入力を受け取りました: {{user_input}}",
        "artifacts": [],
        "cost_usd": 0.0,
    }}
'''


# ---------------------------------------------------------------------------
# CRUD 操作
# ---------------------------------------------------------------------------


async def list_skills(
    db: AsyncSession,
    *,
    status: str | None = None,
    skill_type: str | None = None,
    include_disabled: bool = False,
) -> Sequence[Skill]:
    """スキル一覧を取得する."""
    query = select(Skill)
    if status:
        query = query.where(Skill.status == status)
    if skill_type:
        query = query.where(Skill.skill_type == skill_type)
    if not include_disabled:
        query = query.where(Skill.enabled.is_(True))
    result = await db.execute(query.order_by(Skill.name))
    return result.scalars().all()


async def get_skill(db: AsyncSession, skill_id: uuid.UUID) -> Skill | None:
    """ID でスキルを取得する."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    return result.scalar_one_or_none()


async def get_skill_by_slug(db: AsyncSession, slug: str) -> Skill | None:
    """slug でスキルを取得する."""
    result = await db.execute(select(Skill).where(Skill.slug == slug))
    return result.scalar_one_or_none()


async def create_skill(
    db: AsyncSession,
    data: SkillCreate,
    *,
    is_system_protected: bool = False,
    generated_code: str | None = None,
) -> Skill:
    """新しいスキルを作成する."""
    skill = Skill(
        id=uuid.uuid4(),
        slug=data.slug,
        name=data.name,
        skill_type=data.skill_type,
        description=data.description,
        version=data.version,
        status="experimental",
        source_type=data.source_type,
        source_uri=data.source_uri,
        manifest_json=data.manifest_json,
        policy_json=data.policy_json,
        is_system_protected=is_system_protected,
        generated_code=generated_code,
    )
    db.add(skill)
    await db.flush()
    logger.info("スキル作成: %s (%s)", skill.name, skill.slug)
    return skill


async def update_skill(
    db: AsyncSession,
    skill_id: uuid.UUID,
    data: SkillUpdate,
) -> Skill | None:
    """スキルを更新する."""
    skill = await get_skill(db, skill_id)
    if skill is None:
        return None

    updates = data.model_dump(exclude_unset=True)

    # システム保護スキルは無効化不可
    if skill.is_system_protected and updates.get("enabled") is False:
        raise ValueError(f"システム必須スキル '{skill.slug}' は無効化できません")

    for key, value in updates.items():
        setattr(skill, key, value)
    await db.flush()
    logger.info("スキル更新: %s", skill.slug)
    return skill


async def delete_skill(db: AsyncSession, skill_id: uuid.UUID) -> tuple[bool, str]:
    """スキルを削除する. システム保護スキルは削除不可."""
    skill = await get_skill(db, skill_id)
    if skill is None:
        return False, "スキルが見つかりません"

    if skill.is_system_protected:
        return False, (
            f"システム必須スキル '{skill.slug}' は削除できません。"
            "このスキルはシステムの正常動作に必要です。"
        )

    await db.delete(skill)
    await db.flush()
    logger.info("スキル削除: %s", skill.slug)
    return True, f"スキル '{skill.name}' を削除しました"


# ---------------------------------------------------------------------------
# システム保護スキルの初期登録
# ---------------------------------------------------------------------------

BUILTIN_SKILLS: list[dict] = [
    {
        "slug": "spec-writer",
        "name": "Spec Writer",
        "skill_type": "builtin",
        "description": "Ticket から仕様書 (Spec) を生成する",
        "source_type": "local",
    },
    {
        "slug": "plan-writer",
        "name": "Plan Writer",
        "skill_type": "builtin",
        "description": "仕様書から実行計画 (Plan) を生成する",
        "source_type": "local",
    },
    {
        "slug": "task-breakdown",
        "name": "Task Breakdown",
        "skill_type": "builtin",
        "description": "実行計画をタスク DAG に分解する",
        "source_type": "local",
    },
    {
        "slug": "review-assistant",
        "name": "Review Assistant",
        "skill_type": "builtin",
        "description": "タスク成果物の品質レビューを実施する",
        "source_type": "local",
    },
    {
        "slug": "artifact-summarizer",
        "name": "Artifact Summarizer",
        "skill_type": "builtin",
        "description": "成果物を要約する",
        "source_type": "local",
    },
    {
        "slug": "local-context",
        "name": "Local Context",
        "skill_type": "builtin",
        "description": "ローカルファイル・システム情報にアクセスする",
        "source_type": "local",
    },
]


async def ensure_system_skills(db: AsyncSession) -> list[Skill]:
    """システム必須スキルが DB に登録されていることを保証する.

    アプリケーション起動時に呼び出される。
    """
    created: list[Skill] = []
    for builtin in BUILTIN_SKILLS:
        existing = await get_skill_by_slug(db, builtin["slug"])
        if existing is None:
            skill = await create_skill(
                db,
                SkillCreate(
                    slug=builtin["slug"],
                    name=builtin["name"],
                    skill_type=builtin["skill_type"],
                    description=builtin["description"],
                    version="0.1.0",
                    source_type=builtin["source_type"],
                ),
                is_system_protected=True,
            )
            created.append(skill)
        elif not existing.is_system_protected:
            existing.is_system_protected = True
            await db.flush()

    if created:
        logger.info(
            "システム必須スキルを %d 件登録しました: %s",
            len(created),
            ", ".join(s.slug for s in created),
        )
    return created
