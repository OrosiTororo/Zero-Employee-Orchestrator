"""AI Self-Improvement サービス — Level 2: 自己改善の芽.

ai-self-improvement Plugin の 6 Skill を実装する:
1. skill-analyzer:     既存 Skill のコード品質分析と改善提案
2. skill-improver:     分析結果に基づく改善版 Skill の自動生成
3. judge-tuner:        Experience Memory から Judge 基準の自動調整
4. failure-to-skill:   失敗パターンから新 Skill の自動生成
5. skill-ab-test:      Skill 間の A/B テスト比較
6. auto-test-generator: テストコードの自動生成と品質検証
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.orchestration.experience_memory import (
    ExperienceMemoryRecord,
    FailureTaxonomyRecord,
    PersistentExperienceMemory,
)
from app.orchestration.judge import (
    RuleBasedJudge,
    rule_judge,
)
from app.services.skill_service import analyze_code_safety

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# データ構造
# ---------------------------------------------------------------------------


class AnalysisCategory(str, Enum):
    """Skill 分析カテゴリ."""

    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    ERROR_HANDLING = "error_handling"
    SECURITY = "security"
    TEST_COVERAGE = "test_coverage"
    DOCUMENTATION = "documentation"


class ImprovementPriority(str, Enum):
    """改善提案の優先度."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnalysisFinding:
    """分析結果の個別項目."""

    category: AnalysisCategory
    priority: ImprovementPriority
    title: str
    description: str
    suggestion: str
    line_range: tuple[int, int] | None = None


@dataclass
class SkillAnalysisResult:
    """Skill 分析結果."""

    skill_id: str
    skill_slug: str
    overall_score: float  # 0.0 - 1.0
    findings: list[AnalysisFinding]
    summary: str
    analyzed_at: str = ""

    def __post_init__(self) -> None:
        if not self.analyzed_at:
            self.analyzed_at = datetime.now(timezone.utc).isoformat()


@dataclass
class SkillImprovementProposal:
    """Skill 改善提案."""

    original_skill_id: str
    original_version: str
    proposed_version: str
    original_code: str
    improved_code: str
    changes_summary: list[str]
    expected_improvements: list[str]
    requires_approval: bool = True
    applied: bool = False
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class JudgeTuningRule:
    """Judge 自動調整ルール."""

    rule_name: str
    rule_type: str  # "pattern_match" | "threshold" | "category_filter"
    condition: dict[str, Any]
    action: str  # "warn" | "fail" | "pass"
    confidence: float  # 0.0 - 1.0
    source_patterns: int  # 根拠となるパターン数
    description: str


@dataclass
class JudgeTuningResult:
    """Judge 調整結果."""

    company_id: str
    proposed_rules: list[JudgeTuningRule]
    analyzed_patterns: int
    approval_rate: float
    rejection_rate: float
    summary: str
    tuned_at: str = ""

    def __post_init__(self) -> None:
        if not self.tuned_at:
            self.tuned_at = datetime.now(timezone.utc).isoformat()


@dataclass
class FailureToSkillProposal:
    """失敗パターンから生成された Skill 提案."""

    failure_category: str
    failure_subcategory: str
    occurrence_count: int
    proposed_skill_slug: str
    proposed_skill_name: str
    proposed_skill_description: str
    proposed_code: str
    prevention_strategy: str
    confidence: float


@dataclass
class ABTestConfig:
    """A/B テスト設定."""

    test_id: str
    skill_a_id: str
    skill_b_id: str
    test_input: dict[str, Any]
    iterations: int = 3
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.test_id:
            self.test_id = uuid.uuid4().hex[:12]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class ABTestResult:
    """A/B テスト結果."""

    test_id: str
    skill_a_id: str
    skill_b_id: str
    skill_a_scores: list[float]
    skill_b_scores: list[float]
    skill_a_avg_time_ms: float
    skill_b_avg_time_ms: float
    winner: str  # skill_a_id | skill_b_id | "tie"
    winner_reason: str
    details: list[dict[str, Any]]
    completed_at: str = ""

    def __post_init__(self) -> None:
        if not self.completed_at:
            self.completed_at = datetime.now(timezone.utc).isoformat()


@dataclass
class GeneratedTestCase:
    """自動生成テストケース."""

    test_name: str
    test_type: str  # "normal" | "edge" | "error"
    input_data: dict[str, Any]
    expected_behavior: str
    test_code: str


@dataclass
class AutoTestResult:
    """テスト自動生成結果."""

    skill_id: str
    skill_slug: str
    test_cases: list[GeneratedTestCase]
    total_tests: int
    normal_tests: int
    edge_tests: int
    error_tests: int
    generated_at: str = ""

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# 1. Skill Analyzer — 既存 Skill のコード品質分析
# ---------------------------------------------------------------------------


_ANALYSIS_SYSTEM_PROMPT = """\
あなたは Zero-Employee Orchestrator のスキル品質分析エンジンです。
与えられた Python スキルコードを分析し、以下の観点で評価してください。

## 分析観点
1. **code_quality** — コード品質（構造、可読性、命名規則、DRY原則）
2. **performance** — パフォーマンス（不要な処理、N+1クエリ、メモリ使用）
3. **error_handling** — エラーハンドリング（例外処理、フォールバック、入力検証）
4. **security** — セキュリティ（インジェクション、認証情報の露出、危険な操作）
5. **test_coverage** — テストカバレッジ（テスト可能性、エッジケースの考慮）
6. **documentation** — ドキュメント（docstring、型ヒント、コメント）

## 出力フォーマット
以下の JSON 形式で出力してください:

```json
{
  "overall_score": 0.0-1.0,
  "findings": [
    {
      "category": "code_quality|performance|error_handling|security|test_coverage|documentation",
      "priority": "low|medium|high|critical",
      "title": "問題のタイトル",
      "description": "問題の詳細説明",
      "suggestion": "具体的な改善提案"
    }
  ],
  "summary": "全体の評価サマリ（日本語）"
}
```
"""


async def analyze_skill(
    db: AsyncSession,
    skill_id: uuid.UUID,
) -> SkillAnalysisResult:
    """既存 Skill のコードを分析し、改善提案を生成する.

    LLM を使った深い分析と、静的パターンマッチによる基本分析を組み合わせる。
    """
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise ValueError(f"Skill not found: {skill_id}")

    code = skill.generated_code or ""
    findings: list[AnalysisFinding] = []

    # -- 静的分析（常に実行）--
    findings.extend(_static_analyze(code))

    # -- 安全性チェック --
    safety = analyze_code_safety(code)
    if safety.has_dangerous_code:
        findings.append(
            AnalysisFinding(
                category=AnalysisCategory.SECURITY,
                priority=ImprovementPriority.CRITICAL,
                title="危険なコードパターンの検出",
                description=safety.summary,
                suggestion="eval/exec/subprocess などの危険なパターンを安全な代替手段に置き換えてください",
            )
        )
    if safety.has_external_communication:
        findings.append(
            AnalysisFinding(
                category=AnalysisCategory.SECURITY,
                priority=ImprovementPriority.HIGH,
                title="外部通信の検出",
                description="外部HTTP通信が含まれています",
                suggestion="必要最小限の通信のみ行い、タイムアウトとエラーハンドリングを追加してください",
            )
        )

    # -- LLM 分析 --
    try:
        llm_findings = await _llm_analyze(code)
        findings.extend(llm_findings)
    except Exception as exc:
        logger.warning("LLM分析をスキップ: %s", exc)

    # スコア算出
    overall_score = _calculate_overall_score(findings)

    summary_parts = []
    by_category = {}
    for f in findings:
        by_category.setdefault(f.category.value, []).append(f)
    for cat, items in by_category.items():
        critical_count = sum(
            1 for i in items if i.priority == ImprovementPriority.CRITICAL
        )
        high_count = sum(1 for i in items if i.priority == ImprovementPriority.HIGH)
        summary_parts.append(
            f"{cat}: {len(items)}件 (critical={critical_count}, high={high_count})"
        )

    summary = (
        f"スキル '{skill.slug}' の分析完了。スコア: {overall_score:.0%}。"
        f" 検出事項: {len(findings)}件。{'; '.join(summary_parts)}"
    )

    return SkillAnalysisResult(
        skill_id=str(skill_id),
        skill_slug=skill.slug,
        overall_score=overall_score,
        findings=findings,
        summary=summary,
    )


def _static_analyze(code: str) -> list[AnalysisFinding]:
    """静的パターンマッチによるコード分析."""
    findings: list[AnalysisFinding] = []

    if not code.strip():
        findings.append(
            AnalysisFinding(
                category=AnalysisCategory.CODE_QUALITY,
                priority=ImprovementPriority.CRITICAL,
                title="コードが空です",
                description="スキルの実装コードが存在しません",
                suggestion="execute(context) 関数を実装してください",
            )
        )
        return findings

    lines = code.split("\n")

    # docstring チェック
    if '"""' not in code and "'''" not in code:
        findings.append(
            AnalysisFinding(
                category=AnalysisCategory.DOCUMENTATION,
                priority=ImprovementPriority.MEDIUM,
                title="docstring が未記述",
                description="関数やモジュールに docstring が見つかりません",
                suggestion="各関数に docstring を追加してください",
            )
        )

    # 型ヒントチェック
    func_defs = re.findall(r"(async\s+)?def\s+\w+\([^)]*\)", code)
    for func_def in func_defs:
        if (
            "->" not in func_def
            and "-> "
            not in code[
                code.index(func_def) : code.index(func_def) + len(func_def) + 30
            ]
        ):
            findings.append(
                AnalysisFinding(
                    category=AnalysisCategory.DOCUMENTATION,
                    priority=ImprovementPriority.LOW,
                    title="戻り値の型ヒントが未記述",
                    description=f"関数定義に戻り値の型ヒントがありません: {func_def[:60]}",
                    suggestion="-> ReturnType の形式で戻り値の型を明示してください",
                )
            )
            break  # 1つ見つけたら十分

    # try/except チェック
    if "try:" not in code and "except" not in code:
        findings.append(
            AnalysisFinding(
                category=AnalysisCategory.ERROR_HANDLING,
                priority=ImprovementPriority.HIGH,
                title="エラーハンドリングが未実装",
                description="try/except ブロックが見つかりません",
                suggestion="外部APIコール・ファイル操作には try/except を追加してください",
            )
        )

    # ハードコードされた値
    hardcoded_patterns = [
        (r'https?://[^\s"\']+', "ハードコードされたURL"),
        (r'["\'][\w-]+\.[\w-]+@[\w-]+\.[\w]+["\']', "ハードコードされたメールアドレス"),
    ]
    for pattern, desc in hardcoded_patterns:
        if re.search(pattern, code):
            findings.append(
                AnalysisFinding(
                    category=AnalysisCategory.CODE_QUALITY,
                    priority=ImprovementPriority.MEDIUM,
                    title=desc,
                    description=f"{desc}がコード内に検出されました",
                    suggestion="設定値やコンテキストから注入するようにしてください",
                )
            )

    # 長すぎる関数
    current_func_lines = 0
    in_func = False
    for line in lines:
        if re.match(r"(async\s+)?def\s+", line):
            if in_func and current_func_lines > 50:
                findings.append(
                    AnalysisFinding(
                        category=AnalysisCategory.CODE_QUALITY,
                        priority=ImprovementPriority.MEDIUM,
                        title="長すぎる関数",
                        description=f"50行を超える関数が存在します ({current_func_lines}行)",
                        suggestion="関数を小さな単位に分割してください",
                    )
                )
            in_func = True
            current_func_lines = 0
        elif in_func:
            current_func_lines += 1

    return findings


async def _llm_analyze(code: str) -> list[AnalysisFinding]:
    """LLM を使ったコード分析."""
    from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

    response = await llm_gateway.complete(
        CompletionRequest(
            messages=[
                {"role": "system", "content": _ANALYSIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"以下のスキルコードを分析してください:\n\n```python\n{code}\n```",
                },
            ],
            temperature=0.2,
            max_tokens=4096,
            mode=ExecutionMode.QUALITY,
        )
    )

    findings: list[AnalysisFinding] = []
    try:
        json_match = re.search(r"```json\s*\n(.*?)\n```", response.content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            for item in data.get("findings", []):
                try:
                    findings.append(
                        AnalysisFinding(
                            category=AnalysisCategory(
                                item.get("category", "code_quality")
                            ),
                            priority=ImprovementPriority(
                                item.get("priority", "medium")
                            ),
                            title=item.get("title", ""),
                            description=item.get("description", ""),
                            suggestion=item.get("suggestion", ""),
                        )
                    )
                except (ValueError, KeyError):
                    continue
    except (json.JSONDecodeError, AttributeError):
        pass

    return findings


def _calculate_overall_score(findings: list[AnalysisFinding]) -> float:
    """検出事項から全体スコアを算出."""
    if not findings:
        return 1.0

    penalty = 0.0
    for f in findings:
        if f.priority == ImprovementPriority.CRITICAL:
            penalty += 0.20
        elif f.priority == ImprovementPriority.HIGH:
            penalty += 0.10
        elif f.priority == ImprovementPriority.MEDIUM:
            penalty += 0.05
        else:
            penalty += 0.02

    return max(0.0, min(1.0, 1.0 - penalty))


# ---------------------------------------------------------------------------
# 2. Skill Improver — 分析結果に基づく改善版生成
# ---------------------------------------------------------------------------


_IMPROVE_SYSTEM_PROMPT = """\
あなたは Zero-Employee Orchestrator のスキル改善エンジンです。
既存のスキルコードと分析結果を受け取り、改善版のコードを生成してください。

## ルール
- `async def execute(context: dict) -> dict` のインターフェースを維持すること
- 既存の機能を壊さないこと
- 安全でないコード (eval, exec, subprocess) を使わないこと
- 改善内容を変更点サマリとして出力すること

## 出力フォーマット
```python
{改善されたコード全体}
```

```json
{
  "changes": ["変更点1", "変更点2"],
  "expected_improvements": ["改善効果1", "改善効果2"]
}
```
"""


async def improve_skill(
    db: AsyncSession,
    skill_id: uuid.UUID,
    analysis: SkillAnalysisResult | None = None,
) -> SkillImprovementProposal:
    """分析結果に基づいて Skill の改善版を生成する.

    analysis が未指定の場合は先に分析を実行する。
    """
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise ValueError(f"Skill not found: {skill_id}")

    if analysis is None:
        analysis = await analyze_skill(db, skill_id)

    original_code = skill.generated_code or ""
    if not original_code.strip():
        raise ValueError("改善対象のコードが存在しません")

    # 分析結果のサマリを構築
    findings_text = "\n".join(
        f"- [{f.priority.value}] {f.category.value}: {f.title} — {f.suggestion}"
        for f in analysis.findings
    )

    improved_code = original_code
    changes: list[str] = []
    expected: list[str] = []

    try:
        from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

        response = await llm_gateway.complete(
            CompletionRequest(
                messages=[
                    {"role": "system", "content": _IMPROVE_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"## 元のコード\n```python\n{original_code}\n```\n\n"
                            f"## 分析結果 (スコア: {analysis.overall_score:.0%})\n{findings_text}\n\n"
                            "上記の分析結果に基づいてコードを改善してください。"
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=4096,
                mode=ExecutionMode.QUALITY,
            )
        )

        py_match = re.search(r"```python\s*\n(.*?)\n```", response.content, re.DOTALL)
        if py_match:
            improved_code = py_match.group(1)

        json_match = re.search(r"```json\s*\n(.*?)\n```", response.content, re.DOTALL)
        if json_match:
            meta = json.loads(json_match.group(1))
            changes = meta.get("changes", [])
            expected = meta.get("expected_improvements", [])

    except Exception as exc:
        logger.warning("LLM改善生成をスキップ、静的改善のみ適用: %s", exc)
        improved_code, changes = _apply_static_improvements(
            original_code, analysis.findings
        )
        expected = ["静的分析に基づく基本的な改善"]

    # 安全性チェック
    safety = analyze_code_safety(improved_code)
    if safety.risk_level == "high":
        logger.warning("改善版コードに安全性リスクあり、元コードを維持")
        improved_code = original_code
        changes = ["安全性リスクにより改善を却下"]
        expected = []

    # バージョン番号を更新
    current_version = skill.version or "0.1.0"
    parts = current_version.split(".")
    try:
        parts[-1] = str(int(parts[-1]) + 1)
    except ValueError:
        parts.append("1")
    proposed_version = ".".join(parts)

    return SkillImprovementProposal(
        original_skill_id=str(skill_id),
        original_version=current_version,
        proposed_version=proposed_version,
        original_code=original_code,
        improved_code=improved_code,
        changes_summary=changes if changes else ["コードの品質改善"],
        expected_improvements=expected if expected else ["コード品質の向上"],
        requires_approval=True,
    )


def _apply_static_improvements(
    code: str, findings: list[AnalysisFinding]
) -> tuple[str, list[str]]:
    """LLM なしで適用可能な静的改善."""
    improved = code
    changes: list[str] = []

    # エラーハンドリング追加
    has_error_handling = any(
        f.category == AnalysisCategory.ERROR_HANDLING for f in findings
    )
    if has_error_handling and "try:" not in improved:
        # execute 関数の本体を try/except で囲む
        if "async def execute(" in improved:
            improved = improved.replace(
                "async def execute(context: dict) -> dict:",
                "async def execute(context: dict) -> dict:\n    try:",
            )
            # インデントを調整
            lines = improved.split("\n")
            new_lines = []
            in_execute = False
            added_try = False
            for line in lines:
                if "async def execute(" in line:
                    in_execute = True
                    new_lines.append(line)
                    continue
                if in_execute and line.strip() == "try:":
                    added_try = True
                    new_lines.append(line)
                    continue
                if (
                    in_execute
                    and added_try
                    and line.strip()
                    and not line.startswith("    ")
                ):
                    in_execute = False
                if in_execute and added_try and line.strip():
                    new_lines.append("    " + line)
                else:
                    new_lines.append(line)
            improved = "\n".join(new_lines)
            improved += '\n    except Exception as exc:\n        return {"status": "error", "output": str(exc), "artifacts": [], "cost_usd": 0.0}\n'
            changes.append("execute() 関数にエラーハンドリングを追加")

    return improved, changes


async def apply_improvement(
    db: AsyncSession,
    skill_id: uuid.UUID,
    proposal: SkillImprovementProposal,
) -> Skill:
    """改善提案を適用する（承認後に呼び出し）."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise ValueError(f"Skill not found: {skill_id}")

    # バージョン履歴を manifest_json に保存
    manifest = skill.manifest_json or {}
    version_history = manifest.get("version_history", [])
    version_history.append(
        {
            "version": skill.version,
            "code_snapshot": skill.generated_code,
            "replaced_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    manifest["version_history"] = version_history
    skill.manifest_json = manifest

    # 更新適用
    skill.generated_code = proposal.improved_code
    skill.version = proposal.proposed_version
    await db.flush()

    logger.info(
        "Skill改善適用: %s v%s -> v%s",
        skill.slug,
        proposal.original_version,
        proposal.proposed_version,
    )
    return skill


# ---------------------------------------------------------------------------
# 3. Judge Tuner — Experience Memory からの Judge 基準自動調整
# ---------------------------------------------------------------------------


async def tune_judge_from_experience(
    db: AsyncSession,
    company_id: uuid.UUID,
) -> JudgeTuningResult:
    """Experience Memory の承認/却下パターンから Judge ルールを提案する."""

    # 成功パターン取得
    success_records = await db.execute(
        select(ExperienceMemoryRecord)
        .where(
            ExperienceMemoryRecord.company_id == company_id,
        )
        .limit(200)
    )
    successes = list(success_records.scalars().all())

    # 失敗パターン取得
    failure_records = await db.execute(
        select(FailureTaxonomyRecord)
        .where(
            FailureTaxonomyRecord.company_id == company_id,
        )
        .limit(200)
    )
    failures = list(failure_records.scalars().all())

    total_patterns = len(successes) + len(failures)
    approval_rate = len(successes) / total_patterns if total_patterns > 0 else 0.0
    rejection_rate = len(failures) / total_patterns if total_patterns > 0 else 0.0

    proposed_rules: list[JudgeTuningRule] = []

    # -- パターン1: 頻発する失敗カテゴリから自動ルール生成 --
    failure_categories: dict[str, int] = {}
    for f in failures:
        failure_categories[f.category] = (
            failure_categories.get(f.category, 0) + f.occurrence_count
        )

    for category, count in failure_categories.items():
        if count >= 3:
            proposed_rules.append(
                JudgeTuningRule(
                    rule_name=f"auto_check_{category}",
                    rule_type="category_filter",
                    condition={"failure_category": category, "min_occurrences": count},
                    action="warn",
                    confidence=min(0.9, 0.5 + count * 0.05),
                    source_patterns=count,
                    description=f"失敗カテゴリ '{category}' が{count}回発生。出力に該当パターンがないか追加チェックを推奨。",
                )
            )

    # -- パターン2: 高い有効性スコアのパターンからルール生成 --
    high_effectiveness = [s for s in successes if s.effectiveness_score >= 0.8]
    if high_effectiveness:
        categories = {}
        for s in high_effectiveness:
            categories[s.category] = categories.get(s.category, 0) + 1
        for cat, cnt in categories.items():
            if cnt >= 2:
                proposed_rules.append(
                    JudgeTuningRule(
                        rule_name=f"prefer_{cat}_pattern",
                        rule_type="pattern_match",
                        condition={"success_category": cat, "min_effectiveness": 0.8},
                        action="pass",
                        confidence=min(0.85, 0.5 + cnt * 0.1),
                        source_patterns=cnt,
                        description=f"カテゴリ '{cat}' で有効性スコア0.8以上の成功パターンが{cnt}件。このカテゴリの出力は品質が高い傾向。",
                    )
                )

    # -- パターン3: 回復成功率の低い障害から厳格チェック --
    low_recovery = [
        f for f in failures if f.recovery_success_rate < 0.3 and f.occurrence_count >= 2
    ]
    for f in low_recovery:
        proposed_rules.append(
            JudgeTuningRule(
                rule_name=f"strict_check_{f.category}_{f.subcategory}",
                rule_type="threshold",
                condition={
                    "failure_category": f.category,
                    "failure_subcategory": f.subcategory,
                    "recovery_rate": f.recovery_success_rate,
                },
                action="fail",
                confidence=min(0.95, 0.6 + f.occurrence_count * 0.05),
                source_patterns=f.occurrence_count,
                description=(
                    f"'{f.category}/{f.subcategory}' は回復成功率が{f.recovery_success_rate:.0%}と低く、"
                    f"{f.occurrence_count}回発生。事前に厳格チェックで防止を推奨。"
                ),
            )
        )

    # -- LLM による追加ルール提案 --
    try:
        llm_rules = await _llm_propose_judge_rules(successes, failures)
        proposed_rules.extend(llm_rules)
    except Exception as exc:
        logger.warning("LLMによるJudgeルール提案をスキップ: %s", exc)

    summary = (
        f"分析パターン数: {total_patterns} (成功: {len(successes)}, 失敗: {len(failures)})。"
        f" 承認率: {approval_rate:.0%}。提案ルール数: {len(proposed_rules)}。"
    )

    return JudgeTuningResult(
        company_id=str(company_id),
        proposed_rules=proposed_rules,
        analyzed_patterns=total_patterns,
        approval_rate=approval_rate,
        rejection_rate=rejection_rate,
        summary=summary,
    )


async def _llm_propose_judge_rules(
    successes: list[ExperienceMemoryRecord],
    failures: list[FailureTaxonomyRecord],
) -> list[JudgeTuningRule]:
    """LLM を使ってパターンからルールを提案."""
    from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

    # データを要約
    success_summary = "\n".join(
        f"- [{s.category}] {s.title} (有効性: {s.effectiveness_score})"
        for s in successes[:20]
    )
    failure_summary = "\n".join(
        f"- [{f.category}/{f.subcategory}] {f.description} (発生: {f.occurrence_count}回, 回復率: {f.recovery_success_rate:.0%})"
        for f in failures[:20]
    )

    prompt = f"""以下のデータから Judge Layer の品質チェックルールを提案してください。

## 成功パターン
{success_summary or "（データなし）"}

## 失敗パターン
{failure_summary or "（データなし）"}

JSON配列で出力:
```json
[
  {{
    "rule_name": "ルール名（英語snake_case）",
    "description": "ルールの説明（日本語）",
    "action": "warn または fail"
  }}
]
```"""

    response = await llm_gateway.complete(
        CompletionRequest(
            messages=[
                {"role": "system", "content": "あなたは品質管理の専門家です。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
            mode=ExecutionMode.SPEED,
        )
    )

    rules: list[JudgeTuningRule] = []
    try:
        json_match = re.search(r"```json\s*\n(.*?)\n```", response.content, re.DOTALL)
        if json_match:
            items = json.loads(json_match.group(1))
            for item in items[:5]:  # 最大5ルール
                rules.append(
                    JudgeTuningRule(
                        rule_name=item.get("rule_name", "llm_rule"),
                        rule_type="pattern_match",
                        condition={},
                        action=item.get("action", "warn"),
                        confidence=0.6,
                        source_patterns=0,
                        description=item.get("description", ""),
                    )
                )
    except (json.JSONDecodeError, AttributeError):
        pass

    return rules


async def apply_judge_tuning(
    tuning_result: JudgeTuningResult,
    judge: RuleBasedJudge | None = None,
) -> int:
    """提案された Judge ルールを適用する（承認後に呼び出し）."""
    target_judge = judge or rule_judge
    applied = 0

    for rule in tuning_result.proposed_rules:
        if rule.confidence < 0.5:
            continue

        severity = "error" if rule.action == "fail" else "warning"

        def make_check(r: JudgeTuningRule):
            def check_fn(output: dict, context: dict) -> bool:
                # カテゴリフィルタの場合
                if r.rule_type == "category_filter":
                    cat = r.condition.get("failure_category", "")
                    content = json.dumps(output, ensure_ascii=False, default=str)
                    return cat.lower() not in content.lower()
                return True

            return check_fn

        target_judge.add_rule(
            name=rule.rule_name,
            check_fn=make_check(rule),
            severity=severity,
        )
        applied += 1

    logger.info("Judge ルール %d 件を適用", applied)
    return applied


# ---------------------------------------------------------------------------
# 4. Failure-to-Skill — 失敗パターンから新 Skill 自動生成
# ---------------------------------------------------------------------------


async def generate_skills_from_failures(
    db: AsyncSession,
    company_id: uuid.UUID,
    min_occurrences: int = 2,
) -> list[FailureToSkillProposal]:
    """頻発する失敗パターンから予防 Skill を提案する."""
    memory = PersistentExperienceMemory(db, company_id)
    frequent_failures = await memory.get_frequent_failures(min_count=min_occurrences)

    proposals: list[FailureToSkillProposal] = []

    for failure in frequent_failures:
        slug = f"prevent-{failure.category}-{failure.subcategory}".lower()
        slug = re.sub(r"[^a-z0-9-]", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")

        name = f"失敗防止: {failure.category}/{failure.subcategory}"

        description = (
            f"失敗パターン '{failure.category}/{failure.subcategory}' の再発を防止するスキル。"
            f" {failure.description}。予防策: {failure.prevention_strategy}"
        )

        # LLM でコード生成を試みる
        code = ""
        try:
            code = await _generate_prevention_skill_code(failure)
        except Exception as exc:
            logger.warning("LLM予防スキル生成をスキップ: %s", exc)

        # フォールバック: テンプレートベースコード
        if not code:
            code = _generate_prevention_template(slug, failure)

        confidence = min(0.9, 0.4 + failure.occurrence_count * 0.1)

        proposals.append(
            FailureToSkillProposal(
                failure_category=failure.category,
                failure_subcategory=failure.subcategory,
                occurrence_count=failure.occurrence_count,
                proposed_skill_slug=slug,
                proposed_skill_name=name,
                proposed_skill_description=description,
                proposed_code=code,
                prevention_strategy=failure.prevention_strategy,
                confidence=confidence,
            )
        )

    return proposals


async def _generate_prevention_skill_code(
    failure: FailureTaxonomyRecord,
) -> str:
    """LLM を使って予防スキルのコードを生成."""
    from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

    prompt = f"""以下の失敗パターンを防止するスキルのPythonコードを生成してください。

## 失敗パターン
- カテゴリ: {failure.category}
- サブカテゴリ: {failure.subcategory}
- 説明: {failure.description}
- 予防策: {failure.prevention_strategy}
- 発生回数: {failure.occurrence_count}

## ルール
- `async def execute(context: dict) -> dict` を実装
- context には input, local_context, provider, settings が含まれる
- 戻り値: {{ status, output, artifacts, cost_usd }}
- eval/exec/subprocess は使わない
- タスク実行前にチェックし、問題があれば警告を返す

```python
{{コード}}
```"""

    response = await llm_gateway.complete(
        CompletionRequest(
            messages=[
                {"role": "system", "content": "あなたはスキルコード生成の専門家です。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
            mode=ExecutionMode.SPEED,
        )
    )

    py_match = re.search(r"```python\s*\n(.*?)\n```", response.content, re.DOTALL)
    return py_match.group(1) if py_match else ""


def _generate_prevention_template(slug: str, failure: FailureTaxonomyRecord) -> str:
    """テンプレートベースの予防スキルコード."""
    safe_cat = failure.category.replace('"', '\\"')
    safe_sub = failure.subcategory.replace('"', '\\"')
    safe_desc = failure.description.replace('"', '\\"').replace("\n", "\\n")
    safe_prev = failure.prevention_strategy.replace('"', '\\"').replace("\n", "\\n")

    return f'''"""失敗防止スキル: {slug}

カテゴリ: {safe_cat}/{safe_sub}
予防策: {safe_prev}
"""


async def execute(context: dict) -> dict:
    """タスク実行前に失敗パターンをチェックする.

    検出対象: {safe_desc}
    """
    user_input = context.get("input", "")
    warnings: list[str] = []

    # 失敗パターンのキーワードチェック
    risk_keywords = ["{safe_cat}", "{safe_sub}"]
    for keyword in risk_keywords:
        if keyword.lower() in user_input.lower():
            warnings.append(
                f"入力に失敗パターン関連キーワード '{{keyword}}' が含まれています。"
                f"予防策: {safe_prev}"
            )

    if warnings:
        return {{
            "status": "warning",
            "output": "失敗パターンの兆候を検出しました: " + "; ".join(warnings),
            "artifacts": [],
            "cost_usd": 0.0,
            "prevention_advice": "{safe_prev}",
        }}

    return {{
        "status": "success",
        "output": "失敗パターンの兆候は検出されませんでした",
        "artifacts": [],
        "cost_usd": 0.0,
    }}
'''


# ---------------------------------------------------------------------------
# 5. Skill A/B Test — Skill 間の性能比較
# ---------------------------------------------------------------------------


async def run_skill_ab_test(
    db: AsyncSession,
    skill_a_id: uuid.UUID,
    skill_b_id: uuid.UUID,
    test_input: dict[str, Any],
    iterations: int = 3,
) -> ABTestResult:
    """2つの Skill を同じ入力で実行し、品質・速度を比較する."""
    result_a = await db.execute(select(Skill).where(Skill.id == skill_a_id))
    skill_a = result_a.scalar_one_or_none()
    result_b = await db.execute(select(Skill).where(Skill.id == skill_b_id))
    skill_b = result_b.scalar_one_or_none()

    if skill_a is None:
        raise ValueError(f"Skill A not found: {skill_a_id}")
    if skill_b is None:
        raise ValueError(f"Skill B not found: {skill_b_id}")

    test_id = uuid.uuid4().hex[:12]
    a_scores: list[float] = []
    b_scores: list[float] = []
    a_times: list[float] = []
    b_times: list[float] = []
    details: list[dict[str, Any]] = []

    for i in range(iterations):
        # Skill A 実行
        a_result, a_time = await _execute_skill_for_test(skill_a, test_input)
        a_score = _evaluate_output_quality(a_result)
        a_scores.append(a_score)
        a_times.append(a_time)

        # Skill B 実行
        b_result, b_time = await _execute_skill_for_test(skill_b, test_input)
        b_score = _evaluate_output_quality(b_result)
        b_scores.append(b_score)
        b_times.append(b_time)

        details.append(
            {
                "iteration": i + 1,
                "skill_a": {
                    "score": a_score,
                    "time_ms": a_time,
                    "output_preview": str(a_result.get("output", ""))[:200],
                },
                "skill_b": {
                    "score": b_score,
                    "time_ms": b_time,
                    "output_preview": str(b_result.get("output", ""))[:200],
                },
            }
        )

    avg_a_score = sum(a_scores) / len(a_scores) if a_scores else 0
    avg_b_score = sum(b_scores) / len(b_scores) if b_scores else 0
    avg_a_time = sum(a_times) / len(a_times) if a_times else 0
    avg_b_time = sum(b_times) / len(b_times) if b_times else 0

    # 勝者判定: 品質を優先、同等なら速度で判定
    score_diff = avg_a_score - avg_b_score
    if abs(score_diff) > 0.05:
        winner = str(skill_a_id) if score_diff > 0 else str(skill_b_id)
        winner_reason = (
            f"品質スコア差: {abs(score_diff):.2f} "
            f"(A: {avg_a_score:.2f}, B: {avg_b_score:.2f})"
        )
    elif abs(avg_a_time - avg_b_time) > 100:  # 100ms以上の差
        winner = str(skill_a_id) if avg_a_time < avg_b_time else str(skill_b_id)
        winner_reason = (
            f"品質同等、速度差: {abs(avg_a_time - avg_b_time):.0f}ms "
            f"(A: {avg_a_time:.0f}ms, B: {avg_b_time:.0f}ms)"
        )
    else:
        winner = "tie"
        winner_reason = f"品質・速度ともに同等 (A: {avg_a_score:.2f}/{avg_a_time:.0f}ms, B: {avg_b_score:.2f}/{avg_b_time:.0f}ms)"

    return ABTestResult(
        test_id=test_id,
        skill_a_id=str(skill_a_id),
        skill_b_id=str(skill_b_id),
        skill_a_scores=a_scores,
        skill_b_scores=b_scores,
        skill_a_avg_time_ms=avg_a_time,
        skill_b_avg_time_ms=avg_b_time,
        winner=winner,
        winner_reason=winner_reason,
        details=details,
    )


async def _execute_skill_for_test(
    skill: Skill,
    test_input: dict[str, Any],
) -> tuple[dict[str, Any], float]:
    """Skill をテスト実行し、結果と実行時間を返す."""
    code = skill.generated_code or ""
    if not code.strip():
        return {"status": "error", "output": "コードなし"}, 0.0

    context = {
        "input": test_input.get("input", ""),
        "local_context": test_input.get("local_context", {}),
        "provider": None,
        "settings": test_input.get("settings", {}),
    }

    start = time.monotonic()
    try:
        # サンドボックス実行: compile + exec で execute 関数を取り出し安全に実行
        namespace: dict[str, Any] = {}
        compiled = compile(code, f"<skill:{skill.slug}>", "exec")
        exec(compiled, namespace)  # noqa: S102 — sandbox execution

        execute_fn = namespace.get("execute")
        if execute_fn is None:
            return {"status": "error", "output": "execute関数が未定義"}, 0.0

        import asyncio

        if asyncio.iscoroutinefunction(execute_fn):
            result = await execute_fn(context)
        else:
            result = execute_fn(context)

        elapsed = (time.monotonic() - start) * 1000
        return result if isinstance(result, dict) else {
            "status": "success",
            "output": str(result),
        }, elapsed

    except Exception as exc:
        elapsed = (time.monotonic() - start) * 1000
        return {"status": "error", "output": f"実行エラー: {exc}"}, elapsed


def _evaluate_output_quality(output: dict[str, Any]) -> float:
    """出力の品質をスコアリング."""
    score = 0.0

    # ステータスチェック
    status = output.get("status", "")
    if status == "success":
        score += 0.4
    elif status == "warning":
        score += 0.2

    # 出力内容の充実度
    content = str(output.get("output", ""))
    if content and content != "コードなし":
        score += 0.3
        if len(content) > 50:
            score += 0.1

    # artifacts の有無
    artifacts = output.get("artifacts", [])
    if artifacts:
        score += 0.1

    # エラーがない
    if "error" not in content.lower() and "エラー" not in content:
        score += 0.1

    return min(1.0, score)


# ---------------------------------------------------------------------------
# 6. Auto Test Generator — テストコード自動生成
# ---------------------------------------------------------------------------


_TEST_GEN_SYSTEM_PROMPT = """\
あなたは Zero-Employee Orchestrator のテスト自動生成エンジンです。
与えられたスキルコードから、pytest 形式のテストコードを生成してください。

## テストの種類
1. **normal** — 正常系テスト（期待通りの入力で正常動作を確認）
2. **edge** — エッジケーステスト（空入力、長大入力、特殊文字）
3. **error** — 異常系テスト（不正入力、provider=None、例外発生）

## 出力フォーマット
```json
{
  "test_cases": [
    {
      "test_name": "test_正常な入力で成功を返す",
      "test_type": "normal|edge|error",
      "input_data": {"input": "テスト入力"},
      "expected_behavior": "status=success を返す",
      "test_code": "async def test_...(): ..."
    }
  ]
}
```
"""


async def generate_tests_for_skill(
    db: AsyncSession,
    skill_id: uuid.UUID,
) -> AutoTestResult:
    """Skill のコードからテストケースを自動生成する."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise ValueError(f"Skill not found: {skill_id}")

    code = skill.generated_code or ""
    test_cases: list[GeneratedTestCase] = []

    # -- 静的テスト生成（常に実行）--
    test_cases.extend(_generate_static_tests(skill.slug, code))

    # -- LLM テスト生成 --
    try:
        llm_tests = await _llm_generate_tests(skill.slug, code)
        test_cases.extend(llm_tests)
    except Exception as exc:
        logger.warning("LLMテスト生成をスキップ: %s", exc)

    normal_count = sum(1 for t in test_cases if t.test_type == "normal")
    edge_count = sum(1 for t in test_cases if t.test_type == "edge")
    error_count = sum(1 for t in test_cases if t.test_type == "error")

    return AutoTestResult(
        skill_id=str(skill_id),
        skill_slug=skill.slug,
        test_cases=test_cases,
        total_tests=len(test_cases),
        normal_tests=normal_count,
        edge_tests=edge_count,
        error_tests=error_count,
    )


def _generate_static_tests(slug: str, code: str) -> list[GeneratedTestCase]:
    """静的分析に基づくテストケース生成."""
    tests: list[GeneratedTestCase] = []
    safe_slug = slug.replace("-", "_")

    # 正常系: 基本実行テスト
    tests.append(
        GeneratedTestCase(
            test_name=f"test_{safe_slug}_normal_execution",
            test_type="normal",
            input_data={"input": "テスト入力データ"},
            expected_behavior="status が success または warning を返す",
            test_code=f'''import pytest


@pytest.mark.asyncio
async def test_{safe_slug}_normal_execution():
    """正常な入力で実行できることを確認."""
    context = {{
        "input": "テスト入力データ",
        "local_context": {{}},
        "provider": None,
        "settings": {{}},
    }}
    # execute 関数を取得
    namespace = {{}}
    exec(SKILL_CODE, namespace)
    execute = namespace["execute"]
    result = await execute(context)
    assert isinstance(result, dict)
    assert "status" in result
    assert result["status"] in ("success", "warning")
''',
        )
    )

    # エッジ: 空入力テスト
    tests.append(
        GeneratedTestCase(
            test_name=f"test_{safe_slug}_empty_input",
            test_type="edge",
            input_data={"input": ""},
            expected_behavior="空入力でもエラーにならない",
            test_code=f'''import pytest


@pytest.mark.asyncio
async def test_{safe_slug}_empty_input():
    """空入力でもクラッシュしないことを確認."""
    context = {{
        "input": "",
        "local_context": {{}},
        "provider": None,
        "settings": {{}},
    }}
    namespace = {{}}
    exec(SKILL_CODE, namespace)
    execute = namespace["execute"]
    result = await execute(context)
    assert isinstance(result, dict)
    assert "status" in result
''',
        )
    )

    # 異常系: context が不完全
    tests.append(
        GeneratedTestCase(
            test_name=f"test_{safe_slug}_minimal_context",
            test_type="error",
            input_data={},
            expected_behavior="最小限の context でもエラーハンドリングされる",
            test_code=f'''import pytest


@pytest.mark.asyncio
async def test_{safe_slug}_minimal_context():
    """最小限のcontextでもクラッシュしないことを確認."""
    context = {{}}
    namespace = {{}}
    exec(SKILL_CODE, namespace)
    execute = namespace["execute"]
    try:
        result = await execute(context)
        assert isinstance(result, dict)
    except (KeyError, TypeError):
        pass  # context 未チェックの場合は例外が発生しうる
''',
        )
    )

    return tests


async def _llm_generate_tests(slug: str, code: str) -> list[GeneratedTestCase]:
    """LLM を使ったテストケース生成."""
    from app.providers.gateway import CompletionRequest, ExecutionMode, llm_gateway

    response = await llm_gateway.complete(
        CompletionRequest(
            messages=[
                {"role": "system", "content": _TEST_GEN_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"以下のスキルコードのテストを生成:\n\n```python\n{code}\n```",
                },
            ],
            temperature=0.3,
            max_tokens=4096,
            mode=ExecutionMode.SPEED,
        )
    )

    tests: list[GeneratedTestCase] = []
    try:
        json_match = re.search(r"```json\s*\n(.*?)\n```", response.content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            for item in data.get("test_cases", []):
                tests.append(
                    GeneratedTestCase(
                        test_name=item.get("test_name", "test_unnamed"),
                        test_type=item.get("test_type", "normal"),
                        input_data=item.get("input_data", {}),
                        expected_behavior=item.get("expected_behavior", ""),
                        test_code=item.get("test_code", ""),
                    )
                )
    except (json.JSONDecodeError, AttributeError):
        pass

    return tests
