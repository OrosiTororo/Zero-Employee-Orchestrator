"""Tests for governance_service."""

from __future__ import annotations

import pytest

from app.services.governance_service import (
    ComplianceFramework,
    GovernanceService,
    PolicyRule,
    PolicyType,
    ViolationSeverity,
)


@pytest.mark.asyncio
async def test_default_policies_seed_on_init():
    svc = GovernanceService()
    all_policies = await svc.list_policies(active_only=False)
    assert len(all_policies) > 0


@pytest.mark.asyncio
async def test_add_policy_assigns_id():
    svc = GovernanceService()
    rule = PolicyRule(
        id="",
        name="test-rule",
        policy_type=PolicyType.DATA_RETENTION,
        framework=ComplianceFramework.GDPR,
        description="test",
        severity=ViolationSeverity.MEDIUM,
    )
    added = await svc.add_policy(rule)
    assert added.id
    assert added.created_at


@pytest.mark.asyncio
async def test_list_policies_filters_by_framework():
    svc = GovernanceService()
    gdpr = await svc.list_policies(framework=ComplianceFramework.GDPR)
    for r in gdpr:
        assert r.framework == ComplianceFramework.GDPR


@pytest.mark.asyncio
async def test_remove_policy_returns_bool():
    svc = GovernanceService()
    rule = PolicyRule(
        id="",
        name="drop-me",
        policy_type=PolicyType.PII_HANDLING,
        framework=ComplianceFramework.HIPAA,
        description="test",
    )
    added = await svc.add_policy(rule)
    assert await svc.remove_policy(added.id) is True
    # Subsequent removal of an already-deleted rule raises ValueError.
    with pytest.raises(ValueError):
        await svc.remove_policy(added.id)


@pytest.mark.asyncio
async def test_check_compliance_returns_result_per_rule():
    svc = GovernanceService()
    results = await svc.check_compliance(ComplianceFramework.GDPR, resource_id="res-1")
    # Exactly one check per active GDPR rule
    gdpr_rules = await svc.list_policies(framework=ComplianceFramework.GDPR)
    assert len(results) == len(gdpr_rules)
    for r in results:
        assert r.framework == ComplianceFramework.GDPR
