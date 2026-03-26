"""Objective-to-Plan decomposition quality verification service -- Plan Quality Verifier.

Adds a verification stage using the Judge Layer to check whether the decomposition
from Spec to Plan is complete and non-overlapping (MECE: Mutually Exclusive,
Collectively Exhaustive).

Verification items:
- Objective coverage (whether all Spec objectives are mapped to Plan tasks)
- Constraint reflection (whether Spec constraints are considered at the task level)
- Acceptance criteria mapping (whether tasks exist for each acceptance criterion)
- Duplicate task detection (detecting similar tasks)
- Dependency logical consistency
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


def _tokenize_multilang(text: str) -> set[str]:
    """Tokenize text for plan quality comparison.

    ASCII/numbers are split into word tokens; CJK/Japanese characters are split
    into individual characters so that Japanese text (which has no spaces
    between words) can still produce meaningful similarity scores.
    """
    tokens: set[str] = set()
    for token in re.findall(r"[a-zA-Z0-9]+", text.lower()):
        tokens.add(token)
    for char in text:
        if ("\u3040" <= char <= "\u30ff") or ("\u4e00" <= char <= "\u9fff"):
            tokens.add(char)
    return tokens


def _plan_similarity(a: str, b: str) -> float:
    """Jaccard similarity with character-level CJK support."""
    tokens_a = _tokenize_multilang(a)
    tokens_b = _tokenize_multilang(b)
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


# ---------------------------------------------------------------------------
# データ構造
# ---------------------------------------------------------------------------


class CoverageStatus(str, Enum):
    """カバレッジ状態."""

    COVERED = "covered"
    PARTIALLY_COVERED = "partially_covered"
    NOT_COVERED = "not_covered"


class QualityLevel(str, Enum):
    """品質レベル."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class IssueType(str, Enum):
    """問題の種類."""

    MISSING_COVERAGE = "missing_coverage"
    DUPLICATE_TASK = "duplicate_task"
    CONSTRAINT_NOT_REFLECTED = "constraint_not_reflected"
    ACCEPTANCE_NOT_MAPPED = "acceptance_not_mapped"
    DEPENDENCY_ISSUE = "dependency_issue"
    SCOPE_CREEP = "scope_creep"


class IssueSeverity(str, Enum):
    """問題の深刻度."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class SpecInput:
    """検証対象の Spec."""

    spec_id: str = ""
    objective: str = ""
    constraints: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    risk_notes: str = ""


@dataclass
class PlanTaskInput:
    """検証対象の Plan のタスク."""

    task_id: str = ""
    title: str = ""
    description: str = ""
    depends_on: list[str] = field(default_factory=list)
    estimated_hours: float | None = None
    estimated_cost: float | None = None


@dataclass
class PlanInput:
    """検証対象の Plan."""

    plan_id: str = ""
    spec_id: str = ""
    tasks: list[PlanTaskInput] = field(default_factory=list)


@dataclass
class CoverageItem:
    """カバレッジチェックの個別項目."""

    source_type: str = ""
    source_text: str = ""
    status: CoverageStatus = CoverageStatus.NOT_COVERED
    matched_task_ids: list[str] = field(default_factory=list)
    matched_task_titles: list[str] = field(default_factory=list)
    similarity_score: float = 0.0


@dataclass
class QualityIssue:
    """検出された品質問題."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: IssueType = IssueType.MISSING_COVERAGE
    severity: IssueSeverity = IssueSeverity.WARNING
    description: str = ""
    affected_items: list[str] = field(default_factory=list)
    suggestion: str = ""


@dataclass
class DuplicatePair:
    """重複検出されたタスクペア."""

    task_a_id: str = ""
    task_a_title: str = ""
    task_b_id: str = ""
    task_b_title: str = ""
    similarity: float = 0.0


@dataclass
class PlanQualityReport:
    """Plan 品質検証レポート."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str = ""
    spec_id: str = ""
    quality_level: QualityLevel = QualityLevel.GOOD
    overall_score: float = 1.0
    objective_coverage: CoverageItem | None = None
    constraint_coverage: list[CoverageItem] = field(default_factory=list)
    acceptance_coverage: list[CoverageItem] = field(default_factory=list)
    duplicate_tasks: list[DuplicatePair] = field(default_factory=list)
    issues: list[QualityIssue] = field(default_factory=list)
    total_tasks: int = 0
    covered_objectives: int = 0
    covered_constraints: int = 0
    covered_acceptance: int = 0
    verified_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# メインサービス
# ---------------------------------------------------------------------------


class PlanQualityVerifier:
    """Plan 分解の品質を検証するサービス.

    Spec → Plan の分解が MECE（漏れなく・重複なく）かを検証する。
    """

    def __init__(
        self,
        coverage_threshold: float = 0.3,
        duplicate_threshold: float = 0.7,
    ) -> None:
        self.coverage_threshold = coverage_threshold
        self.duplicate_threshold = duplicate_threshold

    def verify(self, spec: SpecInput, plan: PlanInput) -> PlanQualityReport:
        """Spec と Plan の整合性を検証する."""
        issues: list[QualityIssue] = []
        task_texts = [f"{t.title} {t.description}" for t in plan.tasks]
        combined_tasks = " ".join(task_texts)

        # 1. 目的のカバレッジ
        objective_cov = self._check_objective_coverage(spec.objective, plan.tasks, combined_tasks)
        if objective_cov.status == CoverageStatus.NOT_COVERED:
            issues.append(
                QualityIssue(
                    type=IssueType.MISSING_COVERAGE,
                    severity=IssueSeverity.ERROR,
                    description="Specの目的がPlanのタスクでカバーされていません",
                    affected_items=[spec.objective[:100]],
                    suggestion="目的を達成するためのタスクを追加してください",
                )
            )

        # 2. 制約条件のカバレッジ
        constraint_covs = []
        covered_constraints = 0
        for constraint in spec.constraints:
            cov = self._check_text_coverage(constraint, "constraint", plan.tasks)
            constraint_covs.append(cov)
            if cov.status != CoverageStatus.NOT_COVERED:
                covered_constraints += 1
            else:
                issues.append(
                    QualityIssue(
                        type=IssueType.CONSTRAINT_NOT_REFLECTED,
                        severity=IssueSeverity.WARNING,
                        description=f"制約条件がタスクに反映されていません: {constraint[:80]}",
                        affected_items=[constraint[:100]],
                        suggestion="この制約を考慮するタスクを追加するか、既存タスクの説明に反映してください",
                    )
                )

        # 3. 受け入れ基準のカバレッジ
        acceptance_covs = []
        covered_acceptance = 0
        for criteria in spec.acceptance_criteria:
            cov = self._check_text_coverage(criteria, "acceptance_criteria", plan.tasks)
            acceptance_covs.append(cov)
            if cov.status != CoverageStatus.NOT_COVERED:
                covered_acceptance += 1
            else:
                issues.append(
                    QualityIssue(
                        type=IssueType.ACCEPTANCE_NOT_MAPPED,
                        severity=IssueSeverity.ERROR,
                        description=f"受け入れ基準に対応するタスクがありません: {criteria[:80]}",
                        affected_items=[criteria[:100]],
                        suggestion="この受け入れ基準を検証するタスクを追加してください",
                    )
                )

        # 4. タスク間の重複検出
        duplicates = self._detect_duplicates(plan.tasks)
        for dup in duplicates:
            issues.append(
                QualityIssue(
                    type=IssueType.DUPLICATE_TASK,
                    severity=IssueSeverity.WARNING,
                    description=f"類似タスクを検出: 「{dup.task_a_title}」と「{dup.task_b_title}」(類似度: {dup.similarity:.0%})",
                    affected_items=[dup.task_a_id, dup.task_b_id],
                    suggestion="タスクを統合するか、差異を明確にしてください",
                )
            )

        # 5. 依存関係の整合性
        dep_issues = self._check_dependencies(plan.tasks)
        issues.extend(dep_issues)

        # 6. スコープクリープ検出（Spec に関連しないタスク）
        for task in plan.tasks:
            task_text = f"{task.title} {task.description}"
            sim = _plan_similarity(spec.objective, task_text)
            # 全制約・基準との類似度も確認
            max_sim = sim
            for c in spec.constraints + spec.acceptance_criteria:
                max_sim = max(max_sim, _plan_similarity(c, task_text))
            if max_sim < 0.1 and spec.objective:
                issues.append(
                    QualityIssue(
                        type=IssueType.SCOPE_CREEP,
                        severity=IssueSeverity.INFO,
                        description=f"Specの範囲外の可能性があるタスク: 「{task.title}」",
                        affected_items=[task.task_id],
                        suggestion="このタスクがSpecの目的に貢献するか確認してください",
                    )
                )

        # 総合スコア計算
        score = self._calculate_score(
            objective_cov,
            constraint_covs,
            acceptance_covs,
            duplicates,
            issues,
            spec,
        )
        quality_level = self._score_to_level(score)

        return PlanQualityReport(
            plan_id=plan.plan_id,
            spec_id=spec.spec_id,
            quality_level=quality_level,
            overall_score=round(score, 3),
            objective_coverage=objective_cov,
            constraint_coverage=constraint_covs,
            acceptance_coverage=acceptance_covs,
            duplicate_tasks=duplicates,
            issues=issues,
            total_tasks=len(plan.tasks),
            covered_objectives=1 if objective_cov.status != CoverageStatus.NOT_COVERED else 0,
            covered_constraints=covered_constraints,
            covered_acceptance=covered_acceptance,
        )

    def _check_objective_coverage(
        self,
        objective: str,
        tasks: list[PlanTaskInput],
        combined_tasks: str,
    ) -> CoverageItem:
        """目的のカバレッジを確認する."""
        if not objective:
            return CoverageItem(
                source_type="objective",
                source_text="",
                status=CoverageStatus.COVERED,
                similarity_score=1.0,
            )

        sim = _plan_similarity(objective, combined_tasks)
        matched = []
        matched_titles = []
        for task in tasks:
            task_text = f"{task.title} {task.description}"
            task_sim = _plan_similarity(objective, task_text)
            if task_sim > self.coverage_threshold:
                matched.append(task.task_id)
                matched_titles.append(task.title)

        if sim > 0.5 or matched:
            status = CoverageStatus.COVERED
        elif sim > 0.2:
            status = CoverageStatus.PARTIALLY_COVERED
        else:
            status = CoverageStatus.NOT_COVERED

        return CoverageItem(
            source_type="objective",
            source_text=objective[:200],
            status=status,
            matched_task_ids=matched,
            matched_task_titles=matched_titles,
            similarity_score=round(sim, 3),
        )

    def _check_text_coverage(
        self,
        text: str,
        source_type: str,
        tasks: list[PlanTaskInput],
    ) -> CoverageItem:
        """テキストのカバレッジを確認する."""
        matched = []
        matched_titles = []
        max_sim = 0.0
        for task in tasks:
            task_text = f"{task.title} {task.description}"
            sim = _plan_similarity(text, task_text)
            max_sim = max(max_sim, sim)
            if sim > self.coverage_threshold:
                matched.append(task.task_id)
                matched_titles.append(task.title)

        if matched:
            status = CoverageStatus.COVERED
        elif max_sim > self.coverage_threshold * 0.5:
            status = CoverageStatus.PARTIALLY_COVERED
        else:
            status = CoverageStatus.NOT_COVERED

        return CoverageItem(
            source_type=source_type,
            source_text=text[:200],
            status=status,
            matched_task_ids=matched,
            matched_task_titles=matched_titles,
            similarity_score=round(max_sim, 3),
        )

    def _detect_duplicates(self, tasks: list[PlanTaskInput]) -> list[DuplicatePair]:
        """タスク間の重複を検出する."""
        duplicates = []
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                text_i = f"{tasks[i].title} {tasks[i].description}"
                text_j = f"{tasks[j].title} {tasks[j].description}"
                sim = _plan_similarity(text_i, text_j)
                if sim > self.duplicate_threshold:
                    duplicates.append(
                        DuplicatePair(
                            task_a_id=tasks[i].task_id,
                            task_a_title=tasks[i].title,
                            task_b_id=tasks[j].task_id,
                            task_b_title=tasks[j].title,
                            similarity=round(sim, 3),
                        )
                    )
        return duplicates

    def _check_dependencies(self, tasks: list[PlanTaskInput]) -> list[QualityIssue]:
        """依存関係の整合性を確認する."""
        issues = []
        task_ids = {t.task_id for t in tasks}
        for task in tasks:
            for dep in task.depends_on:
                if dep not in task_ids:
                    issues.append(
                        QualityIssue(
                            type=IssueType.DEPENDENCY_ISSUE,
                            severity=IssueSeverity.ERROR,
                            description=f"タスク「{task.title}」が存在しないタスク({dep})に依存しています",
                            affected_items=[task.task_id, dep],
                            suggestion="依存関係を修正してください",
                        )
                    )

        # 循環依存チェック（簡易）
        visited: set[str] = set()
        rec_stack: set[str] = set()
        dep_map = {t.task_id: t.depends_on for t in tasks}

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for dep in dep_map.get(node, []):
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        for task in tasks:
            if task.task_id not in visited:
                if has_cycle(task.task_id):
                    issues.append(
                        QualityIssue(
                            type=IssueType.DEPENDENCY_ISSUE,
                            severity=IssueSeverity.ERROR,
                            description="タスクの依存関係に循環が検出されました",
                            affected_items=[task.task_id],
                            suggestion="循環依存を解消してください",
                        )
                    )
                    break

        return issues

    def _calculate_score(
        self,
        objective_cov: CoverageItem,
        constraint_covs: list[CoverageItem],
        acceptance_covs: list[CoverageItem],
        duplicates: list[DuplicatePair],
        issues: list[QualityIssue],
        spec: SpecInput,
    ) -> float:
        """総合スコアを計算する."""
        score = 1.0

        # 目的カバレッジ (30%)
        if objective_cov.status == CoverageStatus.NOT_COVERED:
            score -= 0.3
        elif objective_cov.status == CoverageStatus.PARTIALLY_COVERED:
            score -= 0.15

        # 制約カバレッジ (20%)
        if constraint_covs:
            covered = sum(1 for c in constraint_covs if c.status != CoverageStatus.NOT_COVERED)
            constraint_rate = covered / len(constraint_covs)
            score -= (1 - constraint_rate) * 0.2

        # 受け入れ基準カバレッジ (30%)
        if acceptance_covs:
            covered = sum(1 for c in acceptance_covs if c.status != CoverageStatus.NOT_COVERED)
            acceptance_rate = covered / len(acceptance_covs)
            score -= (1 - acceptance_rate) * 0.3

        # 重複ペナルティ (10%)
        if duplicates:
            score -= min(len(duplicates) * 0.05, 0.1)

        # 問題ペナルティ (10%)
        error_count = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
        score -= min(error_count * 0.03, 0.1)

        return max(0.0, min(1.0, score))

    def _score_to_level(self, score: float) -> QualityLevel:
        """スコアを品質レベルに変換する."""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        if score >= 0.7:
            return QualityLevel.GOOD
        if score >= 0.5:
            return QualityLevel.FAIR
        return QualityLevel.POOR


# ---------------------------------------------------------------------------
# シングルトンインスタンス
# ---------------------------------------------------------------------------

plan_quality_verifier = PlanQualityVerifier()
