"""Judge Layer (Layer 5) - Two-stage Detection + Cross-Model Verification.

Provides quality assurance, policy compliance checking, and output verification.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class JudgeVerdict(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"


@dataclass
class JudgeResult:
    verdict: JudgeVerdict
    score: float  # 0.0 - 1.0
    reasons: list[str]
    suggestions: list[str]
    policy_violations: list[str]
    requires_human_review: bool = False
    contradiction_details: list[dict] = field(default_factory=list)


class RuleBasedJudge:
    """Stage 1: Fast rule-based checks."""

    def __init__(self) -> None:
        self.rules: list[dict] = []

    def add_rule(self, name: str, check_fn: Callable[[dict, dict], bool], severity: str = "error") -> None:
        self.rules.append({"name": name, "check": check_fn, "severity": severity})

    def evaluate(self, output: dict, context: dict | None = None) -> JudgeResult:
        violations = []
        warnings = []
        score = 1.0

        for rule in self.rules:
            try:
                passed = rule["check"](output, context or {})
                if not passed:
                    if rule["severity"] == "error":
                        violations.append(rule["name"])
                        score -= 0.2
                    else:
                        warnings.append(rule["name"])
                        score -= 0.05
            except (KeyError, TypeError, AttributeError, ValueError) as exc:
                warnings.append(f"Rule check failed: {rule['name']} ({exc})")

        score = max(0.0, score)

        if violations:
            verdict = JudgeVerdict.FAIL
        elif warnings:
            verdict = JudgeVerdict.WARN
        else:
            verdict = JudgeVerdict.PASS

        return JudgeResult(
            verdict=verdict,
            score=score,
            reasons=violations + warnings,
            suggestions=[],
            policy_violations=violations,
            requires_human_review=len(violations) > 0,
        )


class PolicyPackJudge:
    """Evaluates output against Policy Pack rules (compliance control)."""

    def __init__(self, policy_rules: dict | None = None) -> None:
        self.rules = policy_rules or {}

    def check_dangerous_operations(self, operations: list[str]) -> list[str]:
        """Check if any operations require forced approval."""
        dangerous = {
            "external_send",
            "publish",
            "post",
            "delete",
            "charge",
            "git_push",
            "git_release",
            "file_overwrite_important",
            "permission_change",
            "api_key_update",
            "credential_update",
        }
        return [op for op in operations if op in dangerous]

    def check_credential_exposure(self, content: str) -> bool:
        """Check if content might contain credential values."""
        suspicious_patterns = [
            "sk-",
            "Bearer ",
            "api_key=",
            "password=",
            "secret=",
            "token=",
            "AKIA",
        ]
        return any(p in content for p in suspicious_patterns)

    def evaluate(self, output: dict, operations: list[str] | None = None) -> JudgeResult:
        violations = []
        suggestions = []

        # Check dangerous operations via approval_gate
        if operations:
            dangerous = self.check_dangerous_operations(operations)
            if dangerous:
                violations.extend(
                    [f"Approval-required operation detected: {op}" for op in dangerous]
                )

            # autonomy_boundary check
            try:
                from app.policies.autonomy_boundary import check_autonomy

                for op in operations:
                    autonomy = check_autonomy(op)
                    if autonomy.requires_approval and op not in dangerous:
                        violations.append(f"Autonomy boundary: {autonomy.reason}")
            except ImportError:
                pass

        # Check credential exposure
        content = str(output)
        if self.check_credential_exposure(content):
            violations.append("Credentials may be included in plaintext")
            suggestions.append("Please mask sensitive information or replace with reference IDs")

        # PII check — verify output does not contain personal information
        try:
            from app.security.pii_guard import detect_and_mask_pii

            pii_result = detect_and_mask_pii(content[:5000])  # Scan first 5000 characters
            if pii_result.has_pii:
                suggestions.append(
                    f"PII detected ({pii_result.detected_count} items): "
                    f"{', '.join(pii_result.detected_types)} — masking recommended"
                )
        except ImportError:
            pass

        score = 1.0 - (len(violations) * 0.3)
        score = max(0.0, score)

        return JudgeResult(
            verdict=JudgeVerdict.FAIL if violations else JudgeVerdict.PASS,
            score=score,
            reasons=violations,
            suggestions=suggestions,
            policy_violations=violations,
            requires_human_review=len(violations) > 0,
        )


# ---------------------------------------------------------------------------
# Utility functions for semantic comparison
# Utility functions for semantic comparison
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> set[str]:
    """Tokenize text into lowercase word tokens for Jaccard similarity.

    Tokenize text into lowercase tokens (for Jaccard similarity calculation).
    """
    return set(re.findall(r"[a-zA-Z0-9\u3040-\u9fff]+", text.lower()))


def _jaccard_similarity(a: str, b: str) -> float:
    """Compute token-level Jaccard similarity between two strings.

    Compute token-level Jaccard similarity between two strings.
    """
    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def _normalize_value(value: str) -> str:
    """Normalize a string value for comparison (strip, lowercase).

    Normalize a string for comparison (strip whitespace, lowercase).
    """
    return value.strip().lower()


def _try_parse_number(value: str) -> float | None:
    """Try to parse a string as a number, return None on failure.

    Parse a string as a number. Returns None on failure.
    """
    cleaned = value.strip().replace(",", "").replace(" ", "")
    # Handle percentages
    if cleaned.endswith("%"):
        try:
            return float(cleaned[:-1]) / 100.0
        except ValueError:
            return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _numeric_close(a_str: str, b_str: str, tolerance: float = 0.05) -> bool | None:
    """Compare two values numerically within tolerance.

    Returns True if close, False if not close, None if not both numeric.
    Compare two values numerically. True if close, False if not close, None if not both numeric.
    """
    a_num = _try_parse_number(a_str)
    b_num = _try_parse_number(b_str)
    if a_num is None or b_num is None:
        return None
    if a_num == b_num == 0.0:
        return True
    denominator = max(abs(a_num), abs(b_num))
    if denominator == 0:
        return True
    return abs(a_num - b_num) / denominator <= tolerance


# Negation patterns for contradiction detection
# Negation patterns for contradiction detection
_NEGATION_PAIRS: list[tuple[re.Pattern, re.Pattern]] = [
    (re.compile(r"\bis\b", re.I), re.compile(r"\bis\s+not\b", re.I)),
    (re.compile(r"\btrue\b", re.I), re.compile(r"\bfalse\b", re.I)),
    (re.compile(r"\byes\b", re.I), re.compile(r"\bno\b", re.I)),
    (re.compile(r"\bcorrect\b", re.I), re.compile(r"\bincorrect\b", re.I)),
    (re.compile(r"\bvalid\b", re.I), re.compile(r"\binvalid\b", re.I)),
    (re.compile(r"\bpossible\b", re.I), re.compile(r"\bimpossible\b", re.I)),
    (re.compile(r"\bcan\b", re.I), re.compile(r"\bcannot\b|\bcan't\b", re.I)),
    (re.compile(r"\bwill\b", re.I), re.compile(r"\bwill\s+not\b|\bwon't\b", re.I)),
    (re.compile(r"\bsuccess\b", re.I), re.compile(r"\bfailure\b|\bfail\b", re.I)),
    (re.compile(r"\bincrease\b", re.I), re.compile(r"\bdecrease\b", re.I)),
    (re.compile(r"\bhigher\b", re.I), re.compile(r"\blower\b", re.I)),
    (re.compile(r"\bpositive\b", re.I), re.compile(r"\bnegative\b", re.I)),
    (re.compile(r"\bbefore\b", re.I), re.compile(r"\bafter\b", re.I)),
    (re.compile(r"\babove\b", re.I), re.compile(r"\bbelow\b", re.I)),
    (re.compile(r"\bmore\b", re.I), re.compile(r"\bless\b|\bfewer\b", re.I)),
    (re.compile(r"\balways\b", re.I), re.compile(r"\bnever\b", re.I)),
]

# Known factual patterns for basic verification
# Known factual patterns for basic verification
_FACTUAL_PATTERNS: list[dict] = [
    # Year range sanity checks
    {
        "pattern": re.compile(r"\b(\d{4})\b"),
        "check": "year_range",
        "desc": "Year should be between 1000-2100",
    },
    # Percentage bounds
    {
        "pattern": re.compile(r"(\d+(?:\.\d+)?)\s*%"),
        "check": "percentage_bound",
        "desc": "Percentage typically 0-100",
    },
    # Temperature bounds (Celsius)
    {
        "pattern": re.compile(r"(-?\d+(?:\.\d+)?)\s*°?[Cc]"),
        "check": "temp_celsius",
        "desc": "Temperature in Celsius typically -90 to 60",
    },
]


class CrossModelJudge:
    """Cross-Model Verification: compare outputs from multiple models to verify quality.

    Used in HIGH / CRITICAL quality modes, evaluating the agreement
    between different LLM outputs to ensure reliability.

    Enhanced with:
    - Semantic similarity (token-level Jaccard)
    - Numeric tolerance comparison (5% default)
    - Negation / contradiction detection
    - Confidence-weighted scoring (majority vote)
    - Factual verification heuristics
    """

    def __init__(
        self,
        agreement_threshold: float = 0.7,
        numeric_tolerance: float = 0.05,
        semantic_threshold: float = 0.5,
    ) -> None:
        self.agreement_threshold = agreement_threshold
        self.numeric_tolerance = numeric_tolerance
        self.semantic_threshold = semantic_threshold

    # ------------------------------------------------------------------
    # Semantic value comparison
    # Semantic value comparison
    # ------------------------------------------------------------------

    def _values_match(self, a: str, b: str) -> bool:
        """Check if two string values match semantically.

        Check if two string values match semantically.
        Checks in order: exact match -> normalized match -> numeric match -> Jaccard.
        """
        # Exact match
        if a == b:
            return True

        # Normalized match
        na, nb = _normalize_value(a), _normalize_value(b)
        if na == nb:
            return True

        # Numeric tolerance match
        num_result = _numeric_close(a, b, self.numeric_tolerance)
        if num_result is not None:
            return num_result

        # Jaccard similarity
        return _jaccard_similarity(a, b) >= self.semantic_threshold

    # ------------------------------------------------------------------
    # Contradiction detection
    # Contradiction detection
    # ------------------------------------------------------------------

    def detect_contradictions(self, outputs: list[dict]) -> list[dict]:
        """Detect contradictions between multiple model outputs.

        Detect contradictions between multiple model outputs.

        Returns a list of contradiction detail dicts with keys:
            key, type, values, description
        """
        if len(outputs) < 2:
            return []

        contradictions: list[dict] = []

        # Collect all keys across outputs
        all_keys: set[str] = set()
        for out in outputs:
            all_keys.update(out.keys())

        for key in sorted(all_keys):
            values = [str(out[key]) for out in outputs if key in out]
            if len(values) < 2:
                continue

            # Check every pair of values for this key
            for i in range(len(values)):
                for j in range(i + 1, len(values)):
                    vi, vj = values[i], values[j]
                    contradiction = self._check_pair_contradiction(key, vi, vj)
                    if contradiction:
                        contradictions.append(contradiction)

        return contradictions

    def _check_pair_contradiction(self, key: str, val_a: str, val_b: str) -> dict | None:
        """Check a single pair of values for contradiction.

        Check a pair of values for contradiction.
        """
        # 1. Numeric discrepancy
        num_result = _numeric_close(val_a, val_b, self.numeric_tolerance)
        if num_result is False:
            return {
                "key": key,
                "type": "numeric_discrepancy",
                "values": [val_a, val_b],
                "description": f"Numeric values differ beyond {self.numeric_tolerance:.0%} "
                f"tolerance: '{val_a}' vs '{val_b}'",
            }

        # 2. Negation pattern
        for pos_pat, neg_pat in _NEGATION_PAIRS:
            a_has_pos = bool(pos_pat.search(val_a)) and not bool(neg_pat.search(val_a))
            a_has_neg = bool(neg_pat.search(val_a))
            b_has_pos = bool(pos_pat.search(val_b)) and not bool(neg_pat.search(val_b))
            b_has_neg = bool(neg_pat.search(val_b))

            if (a_has_pos and b_has_neg) or (a_has_neg and b_has_pos):
                return {
                    "key": key,
                    "type": "negation_contradiction",
                    "values": [val_a, val_b],
                    "description": f"Opposing assertions detected for '{key}': "
                    f"'{val_a}' vs '{val_b}'",
                }

        # 3. Low semantic similarity with no numeric match means conflicting text
        # Low semantic similarity (no numeric match) = text contradiction
        if num_result is None:  # not numeric
            sim = _jaccard_similarity(val_a, val_b)
            if sim < 0.2 and len(val_a) > 3 and len(val_b) > 3:
                return {
                    "key": key,
                    "type": "semantic_divergence",
                    "values": [val_a, val_b],
                    "description": f"Very low semantic similarity ({sim:.2f}) for '{key}': "
                    f"'{val_a}' vs '{val_b}'",
                }

        return None

    # ------------------------------------------------------------------
    # Factual verification heuristics
    # Factual verification heuristics
    # ------------------------------------------------------------------

    def _check_factual_patterns(self, outputs: list[dict]) -> list[dict]:
        """Run factual verification heuristics on output values.

        Run factual verification heuristics on output values.
        """
        issues: list[dict] = []
        for out in outputs:
            for key, value in out.items():
                val_str = str(value)
                for fp in _FACTUAL_PATTERNS:
                    matches = fp["pattern"].findall(val_str)
                    for match_val in matches:
                        try:
                            num = float(match_val)
                        except (ValueError, TypeError):
                            continue

                        flagged = False
                        if (
                            (fp["check"] == "year_range" and not (1000 <= num <= 2100))
                            or (fp["check"] == "percentage_bound" and not (0 <= num <= 100))
                            or (fp["check"] == "temp_celsius" and not (-90 <= num <= 60))
                        ):
                            flagged = True

                        if flagged:
                            issues.append(
                                {
                                    "key": key,
                                    "type": "factual_anomaly",
                                    "values": [val_str],
                                    "description": f"{fp['desc']}, got {num} in key '{key}'",
                                }
                            )
        return issues

    # ------------------------------------------------------------------
    # Confidence-weighted majority scoring
    # Confidence-weighted majority scoring
    # ------------------------------------------------------------------

    def _majority_agreement_score(self, outputs: list[dict]) -> float:
        """Compute confidence-weighted agreement using majority vote.

        Compute confidence-weighted agreement using majority vote.
        For each common key, find the largest group of matching values.
        """
        all_keys: set[str] = set()
        for out in outputs:
            all_keys.update(out.keys())

        if not all_keys:
            return 0.0

        total_score = 0.0
        key_count = 0

        for key in all_keys:
            values = [str(out[key]) for out in outputs if key in out]
            if len(values) < 2:
                continue
            key_count += 1

            # Group by semantic similarity
            groups: list[list[str]] = []
            for v in values:
                placed = False
                for group in groups:
                    if self._values_match(v, group[0]):
                        group.append(v)
                        placed = True
                        break
                if not placed:
                    groups.append([v])

            # Largest group / total = agreement ratio
            largest = max(len(g) for g in groups)
            total_score += largest / len(values)

        return total_score / key_count if key_count > 0 else 0.0

    # ------------------------------------------------------------------
    # Main evaluate method
    # Main evaluate method
    # ------------------------------------------------------------------

    def evaluate(self, outputs: list[dict], context: dict | None = None) -> JudgeResult:
        """Evaluate agreement across multiple model outputs.

        Enhanced evaluation with semantic comparison, contradiction detection,
        and factual verification heuristics.

        Args:
            outputs: List of output dicts from each model
            context: Evaluation context
        """
        if len(outputs) < 2:
            return JudgeResult(
                verdict=JudgeVerdict.WARN,
                score=0.5,
                reasons=["Cross-model verification requires 2 or more outputs"],
                suggestions=["Verification with additional models is recommended"],
                policy_violations=[],
                requires_human_review=False,
            )

        # ---- Structural agreement (unchanged for backward compat) ----
        all_keys: set[str] = set()
        for out in outputs:
            all_keys.update(out.keys())

        if not all_keys:
            return JudgeResult(
                verdict=JudgeVerdict.WARN,
                score=0.5,
                reasons=["Output is empty"],
                suggestions=[],
                policy_violations=[],
            )

        common_keys = all_keys.copy()
        for out in outputs:
            common_keys &= set(out.keys())
        structural_score = len(common_keys) / len(all_keys) if all_keys else 0.0

        # ---- Semantic value agreement (enhanced) ----
        matching_values = 0
        for key in common_keys:
            values = [str(out.get(key, "")) for out in outputs]
            # Check if all values match semantically
            all_match = True
            for idx in range(1, len(values)):
                if not self._values_match(values[0], values[idx]):
                    all_match = False
                    break
            if all_match:
                matching_values += 1
        semantic_value_score = matching_values / len(common_keys) if common_keys else 0.0

        # ---- Majority-vote confidence score ----
        majority_score = self._majority_agreement_score(outputs)

        # ---- Contradiction detection ----
        contradictions = self.detect_contradictions(outputs)

        # ---- Factual verification ----
        factual_issues = self._check_factual_patterns(outputs)
        all_issues = contradictions + factual_issues

        # ---- Overall score computation ----
        # Weighted combination: structural 20%, semantic value 40%, majority 40%
        raw_score = 0.2 * structural_score + 0.4 * semantic_value_score + 0.4 * majority_score

        # Penalize for contradictions
        contradiction_penalty = min(len(contradictions) * 0.1, 0.5)
        factual_penalty = min(len(factual_issues) * 0.05, 0.2)
        overall_score = max(0.0, raw_score - contradiction_penalty - factual_penalty)
        overall_score = round(overall_score, 3)

        # ---- Build reasons and suggestions ----
        reasons: list[str] = []
        suggestions: list[str] = []

        if structural_score < self.agreement_threshold:
            reasons.append(
                f"Low structural agreement: {structural_score:.0%} (threshold {self.agreement_threshold:.0%})"
            )

        if semantic_value_score < self.agreement_threshold:
            reasons.append(
                f"Low semantic value agreement: {semantic_value_score:.0%} "
                f"(threshold {self.agreement_threshold:.0%})"
            )

        if contradictions:
            reasons.append(f"{len(contradictions)} contradiction(s) detected")
            for c in contradictions[:5]:  # Show first 5
                reasons.append(f"  - [{c['type']}] {c['description']}")
            suggestions.append("Please focus review on keys where contradictions were detected")

        if factual_issues:
            reasons.append(f"{len(factual_issues)} factual verification issue(s) detected")
            for fi in factual_issues[:3]:
                reasons.append(f"  - [{fi['type']}] {fi['description']}")

        # ---- Determine verdict ----
        if overall_score < self.agreement_threshold or len(contradictions) >= 3:
            verdict = JudgeVerdict.NEEDS_REVIEW
            suggestions.append("Human review for final judgment is recommended")
        elif contradictions or reasons:
            verdict = JudgeVerdict.WARN
        else:
            verdict = JudgeVerdict.PASS

        return JudgeResult(
            verdict=verdict,
            score=overall_score,
            reasons=reasons,
            suggestions=suggestions,
            policy_violations=[],
            requires_human_review=verdict == JudgeVerdict.NEEDS_REVIEW,
            contradiction_details=all_issues,
        )


# ---------------------------------------------------------------------------
# Tiered Judge Configuration
# ---------------------------------------------------------------------------


class JudgeTier(str, Enum):
    """Judge evaluation tier — determines which judges run for a given operation."""

    LIGHTWEIGHT = "lightweight"
    STANDARD = "standard"
    HEAVY = "heavy"


# Operation types mapped to lightweight tier (read-only, informational)
_LIGHTWEIGHT_OPERATIONS: frozenset[str] = frozenset(
    {
        "read",
        "info",
        "status",
        "list",
        "get",
        "search",
        "query",
        "view",
        "describe",
        "health",
        "ping",
        "count",
    }
)

# Operation types mapped to heavy tier (dangerous, external, financial)
_HEAVY_OPERATIONS: frozenset[str] = frozenset(
    {
        "send",
        "delete",
        "billing",
        "charge",
        "permission_change",
        "external_api",
        "publish",
        "post",
        "git_push",
        "git_release",
        "credential_update",
        "api_key_update",
        "deploy",
        "external_send",
        "file_overwrite_important",
    }
)

# Risk levels that force heavy tier regardless of operation type
_HEAVY_RISK_LEVELS: frozenset[str] = frozenset({"high", "critical"})


def determine_judge_tier(
    operation_type: str,
    risk_level: str = "low",
) -> JudgeTier:
    """Determine the appropriate judge tier for an operation.

    Args:
        operation_type: The type of operation being performed.
        risk_level: The assessed risk level ("low", "medium", "high", "critical").

    Returns:
        The JudgeTier that should be used for evaluation.

    Tier mapping:
        LIGHTWEIGHT — read operations, info queries, status checks
                      -> only RuleBasedJudge
        STANDARD    — write operations, file changes, internal actions
                      -> RuleBasedJudge + PolicyPackJudge
        HEAVY       — send, delete, billing, permission changes, external API calls
                      -> all judges including CrossModelJudge
    """
    op = operation_type.lower().strip()

    # High/critical risk always gets heavy tier
    if risk_level.lower() in _HEAVY_RISK_LEVELS:
        return JudgeTier.HEAVY

    # Check heavy operations
    if op in _HEAVY_OPERATIONS:
        return JudgeTier.HEAVY

    # Check lightweight operations
    if op in _LIGHTWEIGHT_OPERATIONS:
        return JudgeTier.LIGHTWEIGHT

    # Everything else (write, update, create, edit, etc.) is standard
    return JudgeTier.STANDARD


def judge_with_tier(
    content: dict,
    tier: JudgeTier,
    *,
    operations: list[str] | None = None,
    context: dict | None = None,
    cross_model_outputs: list[dict] | None = None,
) -> JudgeResult:
    """Run only the appropriate judges based on the tier.

    Args:
        content: The output dict to evaluate.
        tier: The JudgeTier determining which judges to invoke.
        operations: Optional list of operation names (for PolicyPackJudge).
        context: Optional context dict (for RuleBasedJudge).
        cross_model_outputs: Optional list of outputs from multiple models
            (for CrossModelJudge in HEAVY tier).

    Returns:
        Combined JudgeResult from all judges in the tier.
    """
    results: list[JudgeResult] = []

    # LIGHTWEIGHT / STANDARD / HEAVY: always run RuleBasedJudge
    rule_result = rule_judge.evaluate(content, context)
    results.append(rule_result)
    if rule_result.verdict == JudgeVerdict.FAIL:
        return rule_result

    # STANDARD / HEAVY: add PolicyPackJudge
    if tier in (JudgeTier.STANDARD, JudgeTier.HEAVY):
        policy_result = policy_judge.evaluate(content, operations)
        results.append(policy_result)
        if policy_result.verdict == JudgeVerdict.FAIL:
            return policy_result

    # HEAVY: add CrossModelJudge
    if tier == JudgeTier.HEAVY:
        outputs = cross_model_outputs or [content]
        if len(outputs) >= 2:
            cross_result = cross_model_judge.evaluate(outputs, context)
            results.append(cross_result)

    # Combine all results
    if len(results) == 1:
        return results[0]

    combined_score = sum(r.score for r in results) / len(results)
    combined_reasons: list[str] = []
    combined_suggestions: list[str] = []
    combined_violations: list[str] = []
    combined_contradictions: list[dict] = []
    needs_review = False

    for r in results:
        combined_reasons.extend(r.reasons)
        combined_suggestions.extend(r.suggestions)
        combined_violations.extend(r.policy_violations)
        combined_contradictions.extend(r.contradiction_details)
        if r.requires_human_review:
            needs_review = True

    # Worst verdict wins
    if any(r.verdict == JudgeVerdict.FAIL for r in results):
        verdict = JudgeVerdict.FAIL
    elif any(r.verdict == JudgeVerdict.NEEDS_REVIEW for r in results):
        verdict = JudgeVerdict.NEEDS_REVIEW
    elif any(r.verdict == JudgeVerdict.WARN for r in results):
        verdict = JudgeVerdict.WARN
    else:
        verdict = JudgeVerdict.PASS

    return JudgeResult(
        verdict=verdict,
        score=round(combined_score, 3),
        reasons=combined_reasons,
        suggestions=combined_suggestions,
        policy_violations=combined_violations,
        requires_human_review=needs_review,
        contradiction_details=combined_contradictions,
    )


# Default judge instances
rule_judge = RuleBasedJudge()
policy_judge = PolicyPackJudge()
cross_model_judge = CrossModelJudge()


def judge_output(
    output: dict,
    operations: list[str] | None = None,
    context: dict | None = None,
) -> JudgeResult:
    """Two-stage judge: rule-based first, then policy check."""
    # Stage 1
    rule_result = rule_judge.evaluate(output, context)
    if rule_result.verdict == JudgeVerdict.FAIL:
        return rule_result

    # Stage 2
    policy_result = policy_judge.evaluate(output, operations)
    if policy_result.verdict == JudgeVerdict.FAIL:
        return policy_result

    # Combine
    combined_score = (rule_result.score + policy_result.score) / 2
    combined_reasons = rule_result.reasons + policy_result.reasons
    combined_suggestions = rule_result.suggestions + policy_result.suggestions

    return JudgeResult(
        verdict=JudgeVerdict.PASS if not combined_reasons else JudgeVerdict.WARN,
        score=combined_score,
        reasons=combined_reasons,
        suggestions=combined_suggestions,
        policy_violations=rule_result.policy_violations + policy_result.policy_violations,
        requires_human_review=rule_result.requires_human_review
        or policy_result.requires_human_review,
    )
