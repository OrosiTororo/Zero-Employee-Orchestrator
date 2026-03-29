"""Tests for RedTeamService -- Automated security self-testing."""

import pytest

from app.security.redteam import (
    RedTeamService,
    SecurityTest,
    TestSeverity,
    VulnerabilityType,
)


@pytest.fixture
def service() -> RedTeamService:
    return RedTeamService()


# ---------------------------------------------------------------------------
# Test definitions
# ---------------------------------------------------------------------------


class TestBuiltinTests:
    def test_builtin_tests_loaded(self, service: RedTeamService):
        assert len(service._tests) >= 20

    def test_all_vulnerability_types_covered(self, service: RedTeamService):
        covered = {t.vulnerability_type for t in service._tests}
        for vtype in VulnerabilityType:
            assert vtype in covered, f"Missing tests for {vtype.value}"


# ---------------------------------------------------------------------------
# Test execution
# ---------------------------------------------------------------------------


class TestExecution:
    @pytest.mark.asyncio
    async def test_run_single_test(self, service: RedTeamService):
        result = await service.run_test("pi-001")
        assert result.test_id == "pi-001"
        assert result.tested_at != ""

    @pytest.mark.asyncio
    async def test_run_nonexistent_test(self, service: RedTeamService):
        with pytest.raises(ValueError, match="Test not found"):
            await service.run_test("nonexistent-test")

    @pytest.mark.asyncio
    async def test_run_category(self, service: RedTeamService):
        results = await service.run_category(VulnerabilityType.PROMPT_INJECTION)
        assert len(results) >= 3
        for r in results:
            assert r.tested_at != ""

    @pytest.mark.asyncio
    async def test_run_all_tests(self, service: RedTeamService):
        report = await service.run_all_tests()
        assert report.total_tests >= 20
        assert report.passed + report.failed == report.total_tests
        assert report.generated_at != ""
        assert len(report.results) == report.total_tests


# ---------------------------------------------------------------------------
# Custom tests
# ---------------------------------------------------------------------------


class TestCustomTests:
    @pytest.mark.asyncio
    async def test_add_custom_test(self, service: RedTeamService):
        custom = SecurityTest(
            id="",
            name="Custom test",
            vulnerability_type=VulnerabilityType.DATA_LEAKAGE,
            description="A custom test",
            test_payload="test payload",
            expected_behavior="should be detected",
            severity=TestSeverity.MEDIUM,
        )
        added = await service.add_custom_test(custom)
        assert added.id.startswith("custom-")
        assert len(service._tests) >= 21


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------


class TestScheduling:
    @pytest.mark.asyncio
    async def test_schedule_periodic_run(self, service: RedTeamService):
        config = await service.schedule_periodic_run(interval_hours=12)
        assert config["enabled"] is True
        assert config["interval_hours"] == 12
        assert config["categories"] is None

    @pytest.mark.asyncio
    async def test_schedule_with_categories(self, service: RedTeamService):
        config = await service.schedule_periodic_run(
            interval_hours=6,
            categories=[VulnerabilityType.PROMPT_INJECTION, VulnerabilityType.PII_EXPOSURE],
        )
        assert len(config["categories"]) == 2

    def test_get_schedule_config_none(self, service: RedTeamService):
        assert service.get_schedule_config() is None

    @pytest.mark.asyncio
    async def test_disable_schedule(self, service: RedTeamService):
        await service.schedule_periodic_run(interval_hours=24)
        service.disable_schedule()
        config = service.get_schedule_config()
        assert config["enabled"] is False

    @pytest.mark.asyncio
    async def test_run_scheduled_all(self, service: RedTeamService):
        report = await service.run_scheduled()
        assert report.total_tests >= 20

    @pytest.mark.asyncio
    async def test_run_scheduled_categories(self, service: RedTeamService):
        await service.schedule_periodic_run(categories=[VulnerabilityType.PII_EXPOSURE])
        results = await service.run_scheduled()
        assert isinstance(results, list)
        assert len(results) >= 2


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


class TestReporting:
    @pytest.mark.asyncio
    async def test_get_latest_report_empty(self, service: RedTeamService):
        report = await service.get_latest_report()
        assert report is None

    @pytest.mark.asyncio
    async def test_get_latest_report(self, service: RedTeamService):
        await service.run_all_tests()
        report = await service.get_latest_report()
        assert report is not None

    @pytest.mark.asyncio
    async def test_get_report_history(self, service: RedTeamService):
        await service.run_all_tests()
        history = await service.get_report_history()
        assert len(history) >= 1

    @pytest.mark.asyncio
    async def test_get_findings_summary_empty(self, service: RedTeamService):
        summary = await service.get_findings_summary()
        assert summary["total_runs"] == 0
        assert summary["status"] == "no_data"

    @pytest.mark.asyncio
    async def test_get_findings_summary(self, service: RedTeamService):
        await service.run_all_tests()
        summary = await service.get_findings_summary()
        assert summary["total_runs"] == 1
        assert summary["total_tests_executed"] >= 20
        assert "pass_rate" in summary
        assert summary["status"] in ("healthy", "attention_needed")

    @pytest.mark.asyncio
    async def test_export_report_dict(self, service: RedTeamService):
        await service.run_all_tests()
        exported = await service.export_report(fmt="dict")
        assert isinstance(exported, dict)
        assert "results" in exported

    @pytest.mark.asyncio
    async def test_export_report_text(self, service: RedTeamService):
        await service.run_all_tests()
        exported = await service.export_report(fmt="text")
        assert isinstance(exported, str)
        assert "Red-Team Security Report" in exported

    @pytest.mark.asyncio
    async def test_export_no_report(self, service: RedTeamService):
        exported = await service.export_report()
        assert isinstance(exported, dict)
        assert "error" in exported

    @pytest.mark.asyncio
    async def test_get_recommendations(self, service: RedTeamService):
        recs = await service.get_recommendations()
        assert len(recs) >= 1
