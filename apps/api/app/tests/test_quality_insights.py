"""品質・洞察機能のテスト — Quality & Insights.

5つの新機能のユニットテスト:
1. 前提変化の汎用監視 (Prerequisite Monitor)
2. Spec 間矛盾検出 (Spec Contradiction)
3. タスクリプレイ・比較 (Task Replay)
4. ユーザー判断振り返り (Judgment Review)
5. Plan 品質検証 (Plan Quality)
"""

from app.services.judgment_review_service import (
    JudgmentAction,
    JudgmentCategory,
    JudgmentReviewService,
)
from app.services.plan_quality_service import (
    PlanInput,
    PlanQualityVerifier,
    PlanTaskInput,
    QualityLevel,
    SpecInput,
)
from app.services.prerequisite_monitor_service import (
    ChangeImpact,
    MonitorStatus,
    PrerequisiteCategory,
    PrerequisiteMonitorService,
)
from app.services.spec_contradiction_service import (
    ContradictionType,
    SpecContradictionDetector,
    SpecSummary,
)
from app.services.task_replay_service import (
    ReplayStatus,
    TaskReplayService,
)

# ===========================================================================
# 1. Prerequisite Monitor
# ===========================================================================


class TestPrerequisiteMonitor:
    """前提変化監視のテスト."""

    def setup_method(self):
        self.monitor = PrerequisiteMonitorService()

    def test_register_source(self):
        """監視対象を登録できる."""
        source = self.monitor.register_source(
            company_id="c1",
            name="OpenAI API Changelog",
            url="https://platform.openai.com/docs/changelog",
            category=PrerequisiteCategory.DEPENDENCY_API,
            keywords=["deprecation", "breaking change"],
        )
        assert source.id
        assert source.name == "OpenAI API Changelog"
        assert source.category == PrerequisiteCategory.DEPENDENCY_API
        assert source.status == MonitorStatus.ACTIVE
        assert len(source.keywords) == 2

    def test_list_sources_by_category(self):
        """カテゴリで絞り込みできる."""
        self.monitor.register_source("c1", "A", "https://a.com", PrerequisiteCategory.COMPETITOR)
        self.monitor.register_source("c1", "B", "https://b.com", PrerequisiteCategory.REGULATION)
        self.monitor.register_source("c1", "C", "https://c.com", PrerequisiteCategory.COMPETITOR)

        competitors = self.monitor.list_sources(category=PrerequisiteCategory.COMPETITOR)
        assert len(competitors) == 2

    def test_check_source_first_time_no_change(self):
        """初回チェックでは変更なし."""
        source = self.monitor.register_source("c1", "Test", "https://test.com")
        change = self.monitor.check_source(source.id, "initial content")
        assert change is None
        assert source.last_content_hash != ""

    def test_check_source_detects_change(self):
        """内容変更を検出できる."""
        source = self.monitor.register_source(
            "c1", "API Docs", "https://api.example.com/docs",
            keywords=["breaking change"],
        )
        self.monitor.check_source(source.id, "version 1.0")
        change = self.monitor.check_source(source.id, "version 2.0 - breaking change")
        assert change is not None
        assert change.source_name == "API Docs"
        assert "breaking change" in change.matched_keywords
        assert change.impact == ChangeImpact.CRITICAL

    def test_check_source_no_change_same_content(self):
        """同一内容では変更なし."""
        source = self.monitor.register_source("c1", "Test", "https://test.com")
        self.monitor.check_source(source.id, "same content")
        change = self.monitor.check_source(source.id, "same content")
        assert change is None

    def test_acknowledge_change(self):
        """変更を確認済みにできる."""
        source = self.monitor.register_source("c1", "Test", "https://test.com")
        self.monitor.check_source(source.id, "v1")
        change = self.monitor.check_source(source.id, "v2")
        assert change is not None

        acked = self.monitor.acknowledge_change(change.id, "user1")
        assert acked is not None
        assert acked.acknowledged is True

    def test_get_summary(self):
        """サマリーを取得できる."""
        self.monitor.register_source("c1", "A", "https://a.com", PrerequisiteCategory.COMPETITOR)
        self.monitor.register_source("c1", "B", "https://b.com", PrerequisiteCategory.REGULATION)
        summary = self.monitor.get_summary("c1")
        assert summary["total_sources"] == 2
        assert summary["active_sources"] == 2

    def test_remove_source(self):
        """監視対象を削除できる."""
        source = self.monitor.register_source("c1", "Test", "https://test.com")
        assert self.monitor.remove_source(source.id) is True
        assert self.monitor.get_source(source.id) is None

    def test_update_source(self):
        """監視対象を更新できる."""
        source = self.monitor.register_source("c1", "Test", "https://test.com")
        updated = self.monitor.update_source(source.id, name="Updated Name")
        assert updated.name == "Updated Name"


# ===========================================================================
# 2. Spec Contradiction
# ===========================================================================


class TestSpecContradiction:
    """Spec 間矛盾検出のテスト."""

    def setup_method(self):
        self.detector = SpecContradictionDetector()

    def test_no_contradictions(self):
        """矛盾がない場合は空."""
        specs = [
            SpecSummary(spec_id="s1", objective="売上レポート作成"),
            SpecSummary(spec_id="s2", objective="顧客満足度調査"),
        ]
        report = self.detector.detect_contradictions(specs)
        assert report.analyzed_specs == 2
        assert report.overall_consistency_score > 0.9

    def test_negation_conflict_in_objectives(self):
        """目的に否定的矛盾を検出."""
        specs = [
            SpecSummary(
                spec_id="s1",
                objective="This feature is possible to implement",
            ),
            SpecSummary(
                spec_id="s2",
                objective="This feature is impossible to implement",
            ),
        ]
        report = self.detector.detect_contradictions(specs)
        negation_conflicts = [
            c for c in report.contradictions
            if c.type == ContradictionType.NEGATION_CONFLICT
        ]
        assert len(negation_conflicts) > 0

    def test_constraint_conflict(self):
        """制約条件の矛盾を検出."""
        specs = [
            SpecSummary(
                spec_id="s1",
                constraints=["Budget should increase by 20%"],
            ),
            SpecSummary(
                spec_id="s2",
                constraints=["Budget should decrease by 20%"],
            ),
        ]
        report = self.detector.detect_contradictions(specs)
        assert len(report.contradictions) > 0

    def test_priority_conflict(self):
        """類似目的で異なる優先度を検出."""
        specs = [
            SpecSummary(
                spec_id="s1",
                objective="Build a customer dashboard with analytics",
                priority="high",
            ),
            SpecSummary(
                spec_id="s2",
                objective="Build a customer dashboard with analytics features",
                priority="low",
            ),
        ]
        report = self.detector.detect_contradictions(specs)
        priority_conflicts = [
            c for c in report.contradictions
            if c.type == ContradictionType.PRIORITY_CONFLICT
        ]
        assert len(priority_conflicts) > 0

    def test_consistency_score(self):
        """一貫性スコアが矛盾で低下."""
        specs = [
            SpecSummary(
                spec_id="s1",
                objective="The system will always be available",
            ),
            SpecSummary(
                spec_id="s2",
                objective="The system will never be available",
            ),
        ]
        report = self.detector.detect_contradictions(specs)
        assert report.overall_consistency_score < 1.0


# ===========================================================================
# 3. Task Replay
# ===========================================================================


class TestTaskReplay:
    """タスクリプレイ・比較のテスト."""

    def setup_method(self):
        self.service = TaskReplayService()

    def test_create_job(self):
        """リプレイジョブを作成できる."""
        job = self.service.create_replay_job(
            task_id="t1",
            task_description="競合分析レポート作成",
            original_output="分析結果...",
            configs=[
                {"model_id": "claude-opus-4-6", "temperature": 0.7},
                {"model_id": "gpt-5.4", "temperature": 0.7},
            ],
        )
        assert job.id
        assert job.status == ReplayStatus.PENDING
        assert len(job.configs) == 2

    def test_record_execution_and_compare(self):
        """実行結果を記録し比較できる."""
        job = self.service.create_replay_job(
            task_id="t1",
            task_description="test task",
            original_output="original output text here",
            configs=[
                {"model_id": "model-a"},
                {"model_id": "model-b"},
            ],
        )

        self.service.record_execution(
            job.id, 0, "output from model a", execution_time_ms=100, estimated_cost=0.01,
        )
        self.service.record_execution(
            job.id, 1, "output from model b different", execution_time_ms=200, estimated_cost=0.02,
        )

        job = self.service.get_job(job.id)
        assert job.status == ReplayStatus.COMPLETED
        assert len(job.comparisons) > 0
        assert job.summary

    def test_list_jobs(self):
        """ジョブを一覧取得できる."""
        self.service.create_replay_job("t1", "task1", "out1", [{"model_id": "a"}])
        self.service.create_replay_job("t2", "task2", "out2", [{"model_id": "b"}])
        jobs = self.service.list_jobs()
        assert len(jobs) == 2

    def test_list_jobs_by_task(self):
        """タスクIDで絞り込みできる."""
        self.service.create_replay_job("t1", "task1", "out1", [{"model_id": "a"}])
        self.service.create_replay_job("t2", "task2", "out2", [{"model_id": "b"}])
        jobs = self.service.list_jobs(task_id="t1")
        assert len(jobs) == 1


# ===========================================================================
# 4. Judgment Review
# ===========================================================================


class TestJudgmentReview:
    """ユーザー判断振り返りのテスト."""

    def setup_method(self):
        self.service = JudgmentReviewService()

    def test_record_judgment(self):
        """判断を記録できる."""
        record = self.service.record_judgment(
            user_id="u1",
            company_id="c1",
            action=JudgmentAction.APPROVED,
            category=JudgmentCategory.PLAN_APPROVAL,
            target_type="plan",
            target_id="p1",
            risk_level="medium",
        )
        assert record.id
        assert record.action == JudgmentAction.APPROVED

    def test_generate_report_empty(self):
        """記録がない場合も空レポートを返す."""
        report = self.service.generate_report("u1", "c1")
        assert report.total_decisions == 0
        assert report.approval_rate == 0.0

    def test_generate_report_with_data(self):
        """判断データからレポートを生成できる."""
        for _ in range(7):
            self.service.record_judgment(
                "u1", "c1", JudgmentAction.APPROVED,
                JudgmentCategory.PLAN_APPROVAL,
                response_time_seconds=60.0,
            )
        for _ in range(3):
            self.service.record_judgment(
                "u1", "c1", JudgmentAction.REJECTED,
                JudgmentCategory.EXTERNAL_SEND,
                response_time_seconds=120.0,
            )

        report = self.service.generate_report("u1", "c1")
        assert report.total_decisions == 10
        assert report.approval_rate == 0.7
        assert report.rejection_rate == 0.3
        assert len(report.category_insights) == 2
        assert report.avg_response_time_seconds is not None

    def test_detect_high_rejection_pattern(self):
        """高い却下率パターンを検出."""
        for _ in range(8):
            self.service.record_judgment("u1", "c1", JudgmentAction.REJECTED)
        for _ in range(2):
            self.service.record_judgment("u1", "c1", JudgmentAction.APPROVED)

        report = self.service.generate_report("u1", "c1")
        pattern_types = [p.pattern_type for p in report.detected_patterns]
        assert "high_rejection_rate" in pattern_types

    def test_risk_distribution(self):
        """リスク分布が正しく集計される."""
        self.service.record_judgment("u1", "c1", JudgmentAction.APPROVED, risk_level="low")
        self.service.record_judgment("u1", "c1", JudgmentAction.APPROVED, risk_level="low")
        self.service.record_judgment("u1", "c1", JudgmentAction.APPROVED, risk_level="high")
        self.service.record_judgment("u1", "c1", JudgmentAction.REJECTED, risk_level="critical")
        self.service.record_judgment("u1", "c1", JudgmentAction.APPROVED, risk_level="medium")

        report = self.service.generate_report("u1", "c1")
        assert report.risk_distribution["low"] == 2
        assert report.risk_distribution["high"] == 1
        assert report.risk_distribution["critical"] == 1


# ===========================================================================
# 5. Plan Quality
# ===========================================================================


class TestPlanQuality:
    """Plan 品質検証のテスト."""

    def setup_method(self):
        self.verifier = PlanQualityVerifier()

    def test_good_plan(self):
        """良い Plan は高スコア."""
        spec = SpecInput(
            spec_id="s1",
            objective="市場調査レポートを作成する",
            constraints=["予算100万円以内"],
            acceptance_criteria=["市場規模の推定値を含む", "競合3社以上の分析"],
        )
        plan = PlanInput(
            plan_id="p1",
            spec_id="s1",
            tasks=[
                PlanTaskInput(task_id="t1", title="市場規模調査", description="市場規模の推定値を算出する"),
                PlanTaskInput(task_id="t2", title="競合分析", description="競合5社の分析を行う", depends_on=["t1"]),
                PlanTaskInput(task_id="t3", title="レポート作成", description="調査結果をレポートにまとめる", depends_on=["t1", "t2"]),
            ],
        )
        report = self.verifier.verify(spec, plan)
        assert report.quality_level in (QualityLevel.EXCELLENT, QualityLevel.GOOD)
        assert report.overall_score > 0.5

    def test_empty_plan(self):
        """タスクのない Plan は低スコア."""
        spec = SpecInput(
            spec_id="s1",
            objective="レポート作成",
            acceptance_criteria=["分析結果を含む"],
        )
        plan = PlanInput(plan_id="p1", spec_id="s1", tasks=[])
        report = self.verifier.verify(spec, plan)
        assert report.quality_level == QualityLevel.POOR
        assert report.overall_score < 0.5

    def test_duplicate_detection(self):
        """重複タスクを検出."""
        spec = SpecInput(spec_id="s1", objective="分析レポート")
        plan = PlanInput(
            plan_id="p1",
            spec_id="s1",
            tasks=[
                PlanTaskInput(task_id="t1", title="競合分析レポート作成", description="競合企業を分析"),
                PlanTaskInput(task_id="t2", title="競合分析レポート作成", description="競合企業を分析する"),
            ],
        )
        report = self.verifier.verify(spec, plan)
        assert len(report.duplicate_tasks) > 0

    def test_dependency_issue_missing(self):
        """存在しないタスクへの依存を検出."""
        spec = SpecInput(spec_id="s1", objective="テスト")
        plan = PlanInput(
            plan_id="p1",
            spec_id="s1",
            tasks=[
                PlanTaskInput(task_id="t1", title="タスク1", depends_on=["t99"]),
            ],
        )
        report = self.verifier.verify(spec, plan)
        dep_issues = [i for i in report.issues if i.type.value == "dependency_issue"]
        assert len(dep_issues) > 0

    def test_acceptance_coverage(self):
        """受け入れ基準のカバレッジを検証."""
        spec = SpecInput(
            spec_id="s1",
            objective="アプリ開発",
            acceptance_criteria=["ログイン機能", "ダッシュボード"],
        )
        plan = PlanInput(
            plan_id="p1",
            spec_id="s1",
            tasks=[
                PlanTaskInput(task_id="t1", title="ログイン機能の実装", description="ユーザー認証"),
            ],
        )
        report = self.verifier.verify(spec, plan)
        # ダッシュボードがカバーされていないのでスコアが下がる
        assert report.covered_acceptance < len(spec.acceptance_criteria)
