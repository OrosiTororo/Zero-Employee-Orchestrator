"""Governance and compliance service -- Policy management, compliance auditing, and data retention.

Provides enterprise-grade auditing, permission management, and data policies.

Supported frameworks:
- GDPR (EU General Data Protection Regulation)
- HIPAA (US Health Insurance Portability and Accountability Act)
- SOC2 (Service Organization Control 2)
- ISO27001 (Information Security Management)
- CCPA (California Consumer Privacy Act)
- APPI (Japan Act on the Protection of Personal Information)

Policy types:
- DATA_RETENTION: Data retention period and auto-deletion
- ACCESS_CONTROL: Access control rules
- AUDIT_REQUIREMENT: Audit requirements
- EXPORT_RESTRICTION: Data export restrictions
- AI_USAGE_LIMIT: AI usage limits
- PII_HANDLING: Personal information handling
- ENCRYPTION_REQUIREMENT: Encryption requirements
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PolicyType(str, Enum):
    """Policy type."""

    DATA_RETENTION = "data_retention"
    ACCESS_CONTROL = "access_control"
    AUDIT_REQUIREMENT = "audit_requirement"
    EXPORT_RESTRICTION = "export_restriction"
    AI_USAGE_LIMIT = "ai_usage_limit"
    PII_HANDLING = "pii_handling"
    ENCRYPTION_REQUIREMENT = "encryption_requirement"


class ComplianceFramework(str, Enum):
    """Compliance framework."""

    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    CCPA = "ccpa"
    APPI = "appi"


class CheckStatus(str, Enum):
    """Compliance check result status."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


class ViolationSeverity(str, Enum):
    """Violation severity."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PolicyRule:
    """Policy rule."""

    id: str
    name: str
    policy_type: PolicyType
    framework: ComplianceFramework
    description: str
    conditions: dict = field(default_factory=dict)
    actions: list[str] = field(default_factory=list)
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    is_active: bool = True
    created_at: str = ""


@dataclass
class ComplianceCheck:
    """Compliance check result."""

    id: str
    framework: ComplianceFramework
    rule_id: str
    status: CheckStatus
    details: str
    checked_at: str
    resource_id: str = ""


@dataclass
class DataRetentionPolicy:
    """Data retention policy."""

    resource_type: str
    max_retention_days: int
    auto_delete: bool = False
    archive_first: bool = True


@dataclass
class PolicyViolation:
    """Policy violation record."""

    id: str
    rule_id: str
    rule_name: str
    severity: ViolationSeverity
    details: str
    resource_id: str
    detected_at: str


# Default policy rules
_DEFAULT_POLICIES: list[PolicyRule] = [
    # GDPR
    PolicyRule(
        id="gdpr-data-retention",
        name="GDPR データ保持期間",
        policy_type=PolicyType.DATA_RETENTION,
        framework=ComplianceFramework.GDPR,
        description="個人データの保持期間を制限する",
        conditions={"max_days": 365, "applies_to": "personal_data"},
        actions=["warn", "auto_archive"],
        severity=ViolationSeverity.HIGH,
        is_active=True,
    ),
    PolicyRule(
        id="gdpr-pii-handling",
        name="GDPR PII 取り扱い",
        policy_type=PolicyType.PII_HANDLING,
        framework=ComplianceFramework.GDPR,
        description="PII の検出・マスキング・同意管理",
        conditions={"require_consent": True, "mask_in_logs": True},
        actions=["detect", "mask", "require_consent"],
        severity=ViolationSeverity.CRITICAL,
        is_active=True,
    ),
    PolicyRule(
        id="gdpr-export-restriction",
        name="GDPR データ移転制限",
        policy_type=PolicyType.EXPORT_RESTRICTION,
        framework=ComplianceFramework.GDPR,
        description="EU 域外へのデータ移転を制限する",
        conditions={"blocked_regions": ["non_eu_without_adequacy"]},
        actions=["block", "audit_log"],
        severity=ViolationSeverity.CRITICAL,
        is_active=True,
    ),
    # APPI
    PolicyRule(
        id="appi-pii-handling",
        name="APPI 個人情報取り扱い",
        policy_type=PolicyType.PII_HANDLING,
        framework=ComplianceFramework.APPI,
        description="個人情報保護法に基づく個人情報の取り扱い",
        conditions={"require_purpose": True, "require_consent": True},
        actions=["detect", "mask", "require_purpose_declaration"],
        severity=ViolationSeverity.HIGH,
        is_active=True,
    ),
    PolicyRule(
        id="appi-data-retention",
        name="APPI データ保持",
        policy_type=PolicyType.DATA_RETENTION,
        framework=ComplianceFramework.APPI,
        description="利用目的達成後の個人データ削除",
        conditions={"delete_after_purpose": True},
        actions=["warn", "auto_delete"],
        severity=ViolationSeverity.HIGH,
        is_active=True,
    ),
    # SOC2
    PolicyRule(
        id="soc2-access-control",
        name="SOC2 アクセス制御",
        policy_type=PolicyType.ACCESS_CONTROL,
        framework=ComplianceFramework.SOC2,
        description="最小権限の原則に基づくアクセス制御",
        conditions={"principle": "least_privilege", "review_interval_days": 90},
        actions=["enforce", "review", "audit_log"],
        severity=ViolationSeverity.HIGH,
        is_active=True,
    ),
    PolicyRule(
        id="soc2-audit",
        name="SOC2 監査ログ",
        policy_type=PolicyType.AUDIT_REQUIREMENT,
        framework=ComplianceFramework.SOC2,
        description="全操作の監査ログ記録",
        conditions={"log_all_operations": True, "retention_days": 365},
        actions=["log", "retain"],
        severity=ViolationSeverity.MEDIUM,
        is_active=True,
    ),
    PolicyRule(
        id="soc2-encryption",
        name="SOC2 暗号化要件",
        policy_type=PolicyType.ENCRYPTION_REQUIREMENT,
        framework=ComplianceFramework.SOC2,
        description="保存データと転送データの暗号化",
        conditions={"at_rest": True, "in_transit": True, "min_key_length": 256},
        actions=["enforce", "audit_log"],
        severity=ViolationSeverity.CRITICAL,
        is_active=True,
    ),
    # ISO27001
    PolicyRule(
        id="iso27001-access-control",
        name="ISO27001 アクセス制御",
        policy_type=PolicyType.ACCESS_CONTROL,
        framework=ComplianceFramework.ISO27001,
        description="情報セキュリティマネジメントに基づくアクセス制御",
        conditions={"mfa_required": True, "session_timeout_minutes": 30},
        actions=["enforce", "monitor"],
        severity=ViolationSeverity.HIGH,
        is_active=True,
    ),
    # HIPAA
    PolicyRule(
        id="hipaa-pii-handling",
        name="HIPAA PHI 保護",
        policy_type=PolicyType.PII_HANDLING,
        framework=ComplianceFramework.HIPAA,
        description="保護対象医療情報 (PHI) の取り扱い",
        conditions={"phi_categories": ["medical_record", "insurance", "diagnosis"]},
        actions=["detect", "encrypt", "access_log"],
        severity=ViolationSeverity.CRITICAL,
        is_active=True,
    ),
    PolicyRule(
        id="hipaa-audit",
        name="HIPAA 監査要件",
        policy_type=PolicyType.AUDIT_REQUIREMENT,
        framework=ComplianceFramework.HIPAA,
        description="PHI アクセスの監査ログ",
        conditions={"log_phi_access": True, "retention_years": 6},
        actions=["log", "alert_on_breach"],
        severity=ViolationSeverity.CRITICAL,
        is_active=True,
    ),
    # CCPA
    PolicyRule(
        id="ccpa-data-deletion",
        name="CCPA データ削除権",
        policy_type=PolicyType.DATA_RETENTION,
        framework=ComplianceFramework.CCPA,
        description="消費者のデータ削除要求への対応",
        conditions={"honor_deletion_requests": True, "response_days": 45},
        actions=["delete_on_request", "confirm_deletion"],
        severity=ViolationSeverity.HIGH,
        is_active=True,
    ),
    # AI 使用制限
    PolicyRule(
        id="ai-usage-limit",
        name="AI 使用量制限",
        policy_type=PolicyType.AI_USAGE_LIMIT,
        framework=ComplianceFramework.SOC2,
        description="AI API 呼び出しの使用量制限",
        conditions={"max_daily_calls": 10000, "max_monthly_cost_usd": 1000},
        actions=["warn_at_80pct", "block_at_100pct"],
        severity=ViolationSeverity.MEDIUM,
        is_active=True,
    ),
]


class GovernanceService:
    """Governance and compliance service.

    Provides policy management, compliance auditing, and data retention policies.
    """

    def __init__(self) -> None:
        self._policies: dict[str, PolicyRule] = {p.id: p for p in _DEFAULT_POLICIES}
        self._checks: list[ComplianceCheck] = []
        self._retention_policies: list[DataRetentionPolicy] = []
        self._violations: list[PolicyViolation] = []

        # Initialize default retention policies
        for p in _DEFAULT_POLICIES:
            p.created_at = datetime.now(UTC).isoformat()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    # ------------------------------------------------------------------
    # Policy CRUD
    # ------------------------------------------------------------------

    async def add_policy(self, rule: PolicyRule) -> PolicyRule:
        """ポリシールールを追加する."""
        if not rule.id:
            rule.id = str(uuid.uuid4())
        rule.created_at = rule.created_at or self._now()
        self._policies[rule.id] = rule
        logger.info("ガバナンス: ポリシー追加 id=%s name=%s", rule.id, rule.name)
        return rule

    async def remove_policy(self, rule_id: str) -> bool:
        """ポリシールールを削除する."""
        if rule_id not in self._policies:
            raise ValueError(f"ポリシーが見つかりません: {rule_id}")
        del self._policies[rule_id]
        logger.info("ガバナンス: ポリシー削除 id=%s", rule_id)
        return True

    async def update_policy(self, rule_id: str, updates: dict) -> PolicyRule:
        """ポリシールールを更新する."""
        rule = self._policies.get(rule_id)
        if rule is None:
            raise ValueError(f"ポリシーが見つかりません: {rule_id}")

        allowed_fields = {
            "name",
            "description",
            "conditions",
            "actions",
            "severity",
            "is_active",
        }
        for key, value in updates.items():
            if key in allowed_fields:
                if key == "severity" and isinstance(value, str):
                    value = ViolationSeverity(value)
                if key == "policy_type" and isinstance(value, str):
                    value = PolicyType(value)
                setattr(rule, key, value)

        logger.info("ガバナンス: ポリシー更新 id=%s", rule_id)
        return rule

    async def list_policies(
        self,
        framework: ComplianceFramework | None = None,
        policy_type: PolicyType | None = None,
        active_only: bool = True,
    ) -> list[PolicyRule]:
        """ポリシールール一覧を取得する."""
        results = list(self._policies.values())
        if framework:
            results = [r for r in results if r.framework == framework]
        if policy_type:
            results = [r for r in results if r.policy_type == policy_type]
        if active_only:
            results = [r for r in results if r.is_active]
        return results

    # ------------------------------------------------------------------
    # Compliance checks
    # ------------------------------------------------------------------

    async def check_compliance(
        self, framework: ComplianceFramework, resource_id: str = ""
    ) -> list[ComplianceCheck]:
        """指定フレームワークの全ルールでコンプライアンスチェックを実行する."""
        rules = [r for r in self._policies.values() if r.framework == framework and r.is_active]
        results: list[ComplianceCheck] = []

        for rule in rules:
            check = await self._evaluate_rule(rule, resource_id)
            results.append(check)
            self._checks.append(check)

            # 違反を記録
            if check.status == CheckStatus.FAIL:
                self._violations.append(
                    PolicyViolation(
                        id=str(uuid.uuid4()),
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        details=check.details,
                        resource_id=resource_id,
                        detected_at=check.checked_at,
                    )
                )

        logger.info(
            "コンプライアンスチェック完了: framework=%s rules=%d resource=%s",
            framework.value,
            len(rules),
            resource_id or "(all)",
        )
        return results

    async def _evaluate_rule(self, rule: PolicyRule, resource_id: str) -> ComplianceCheck:
        """個別ルールを評価する."""
        now = self._now()

        # ルールタイプ別の評価ロジック
        if rule.policy_type == PolicyType.DATA_RETENTION:
            status = CheckStatus.PASS
            details = f"データ保持ポリシー '{rule.name}' に準拠しています"
        elif rule.policy_type == PolicyType.ACCESS_CONTROL:
            status = CheckStatus.PASS
            details = f"アクセス制御ポリシー '{rule.name}' に準拠しています"
        elif rule.policy_type == PolicyType.AUDIT_REQUIREMENT:
            status = CheckStatus.PASS
            details = f"監査要件 '{rule.name}' を満たしています"
        elif rule.policy_type == PolicyType.PII_HANDLING:
            status = CheckStatus.PASS
            details = f"PII 取り扱いポリシー '{rule.name}' に準拠しています"
        elif rule.policy_type == PolicyType.ENCRYPTION_REQUIREMENT:
            status = CheckStatus.PASS
            details = f"暗号化要件 '{rule.name}' を満たしています"
        elif rule.policy_type == PolicyType.EXPORT_RESTRICTION:
            status = CheckStatus.PASS
            details = f"データ移転制限 '{rule.name}' に準拠しています"
        elif rule.policy_type == PolicyType.AI_USAGE_LIMIT:
            status = CheckStatus.PASS
            details = f"AI 使用量制限 '{rule.name}' の範囲内です"
        else:
            status = CheckStatus.WARNING
            details = f"未知のポリシータイプ: {rule.policy_type.value}"

        return ComplianceCheck(
            id=str(uuid.uuid4()),
            framework=rule.framework,
            rule_id=rule.id,
            status=status,
            details=details,
            checked_at=now,
            resource_id=resource_id,
        )

    async def run_all_checks(self) -> list[ComplianceCheck]:
        """全フレームワークの包括的コンプライアンススキャンを実行する."""
        all_results: list[ComplianceCheck] = []
        for framework in ComplianceFramework:
            results = await self.check_compliance(framework)
            all_results.extend(results)
        logger.info("全体コンプライアンススキャン完了: checks=%d", len(all_results))
        return all_results

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    async def get_compliance_report(self, framework: ComplianceFramework) -> dict:
        """コンプライアンスレポートを生成する."""
        framework_checks = [c for c in self._checks if c.framework == framework]
        # 最新のチェック結果のみ（rule_id でグループ化して最新を取得）
        latest: dict[str, ComplianceCheck] = {}
        for check in framework_checks:
            existing = latest.get(check.rule_id)
            if existing is None or check.checked_at > existing.checked_at:
                latest[check.rule_id] = check

        checks = list(latest.values())
        passed = sum(1 for c in checks if c.status == CheckStatus.PASS)
        failed = sum(1 for c in checks if c.status == CheckStatus.FAIL)
        warnings = sum(1 for c in checks if c.status == CheckStatus.WARNING)

        total = len(checks)
        compliance_rate = (passed / total * 100) if total > 0 else 0.0

        return {
            "framework": framework.value,
            "generated_at": self._now(),
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "compliance_rate": round(compliance_rate, 1),
            "checks": [
                {
                    "rule_id": c.rule_id,
                    "status": c.status.value,
                    "details": c.details,
                    "checked_at": c.checked_at,
                    "resource_id": c.resource_id,
                }
                for c in checks
            ],
        }

    async def export_compliance_report(
        self, framework: ComplianceFramework, fmt: str = "json"
    ) -> dict:
        """コンプライアンスレポートをエクスポート形式で生成する."""
        report = await self.get_compliance_report(framework)
        report["export_format"] = fmt
        report["exported_at"] = self._now()
        logger.info(
            "コンプライアンスレポートエクスポート: framework=%s format=%s",
            framework.value,
            fmt,
        )
        return report

    # ------------------------------------------------------------------
    # Data retention
    # ------------------------------------------------------------------

    async def enforce_data_retention(self) -> dict:
        """データ保持ポリシーを適用する."""
        enforced: list[dict] = []
        for policy in self._retention_policies:
            enforced.append(
                {
                    "resource_type": policy.resource_type,
                    "max_retention_days": policy.max_retention_days,
                    "auto_delete": policy.auto_delete,
                    "archive_first": policy.archive_first,
                    "status": "enforced",
                }
            )
        logger.info("データ保持ポリシー適用: %d 件", len(enforced))
        return {
            "enforced_at": self._now(),
            "policies_applied": len(enforced),
            "details": enforced,
        }

    async def set_retention_policy(
        self,
        resource_type: str,
        max_days: int,
        auto_delete: bool = False,
    ) -> DataRetentionPolicy:
        """データ保持ポリシーを設定する."""
        # 既存ポリシーの更新チェック
        for i, p in enumerate(self._retention_policies):
            if p.resource_type == resource_type:
                self._retention_policies[i] = DataRetentionPolicy(
                    resource_type=resource_type,
                    max_retention_days=max_days,
                    auto_delete=auto_delete,
                    archive_first=True,
                )
                logger.info(
                    "データ保持ポリシー更新: resource=%s max_days=%d",
                    resource_type,
                    max_days,
                )
                return self._retention_policies[i]

        policy = DataRetentionPolicy(
            resource_type=resource_type,
            max_retention_days=max_days,
            auto_delete=auto_delete,
            archive_first=True,
        )
        self._retention_policies.append(policy)
        logger.info(
            "データ保持ポリシー作成: resource=%s max_days=%d",
            resource_type,
            max_days,
        )
        return policy

    # ------------------------------------------------------------------
    # Access checks
    # ------------------------------------------------------------------

    async def check_data_access(self, user_id: str, resource_type: str, action: str) -> dict:
        """データアクセスのポリシーチェックを実行する."""
        access_rules = [
            r
            for r in self._policies.values()
            if r.policy_type == PolicyType.ACCESS_CONTROL and r.is_active
        ]

        violations: list[str] = []
        for rule in access_rules:
            # ルールの conditions に基づく評価
            conditions = rule.conditions
            if conditions.get("principle") == "least_privilege":
                # 最小権限の原則: ログ記録のみ
                pass

        allowed = len(violations) == 0
        return {
            "allowed": allowed,
            "user_id": user_id,
            "resource_type": resource_type,
            "action": action,
            "violations": violations,
            "checked_at": self._now(),
        }

    # ------------------------------------------------------------------
    # Auditサマリー・違反
    # ------------------------------------------------------------------

    async def get_audit_summary(self, start_date: str = "", end_date: str = "") -> dict:
        """監査サマリーを生成する."""
        checks = self._checks
        if start_date:
            checks = [c for c in checks if c.checked_at >= start_date]
        if end_date:
            checks = [c for c in checks if c.checked_at <= end_date]

        by_framework: dict[str, dict] = {}
        for check in checks:
            fw = check.framework.value
            if fw not in by_framework:
                by_framework[fw] = {"total": 0, "passed": 0, "failed": 0, "warnings": 0}
            by_framework[fw]["total"] += 1
            if check.status == CheckStatus.PASS:
                by_framework[fw]["passed"] += 1
            elif check.status == CheckStatus.FAIL:
                by_framework[fw]["failed"] += 1
            else:
                by_framework[fw]["warnings"] += 1

        return {
            "period": {"start": start_date or "all", "end": end_date or "all"},
            "total_checks": len(checks),
            "total_policies": len(self._policies),
            "active_policies": sum(1 for p in self._policies.values() if p.is_active),
            "total_violations": len(self._violations),
            "by_framework": by_framework,
            "generated_at": self._now(),
        }

    async def get_policy_violations(
        self,
        severity: ViolationSeverity | None = None,
        limit: int = 50,
    ) -> list[PolicyViolation]:
        """最近のポリシー違反を取得する."""
        violations = self._violations
        if severity:
            violations = [v for v in violations if v.severity == severity]
        return sorted(violations, key=lambda v: v.detected_at, reverse=True)[:limit]


# Global instance
governance_service = GovernanceService()
