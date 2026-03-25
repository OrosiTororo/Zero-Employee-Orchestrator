"""透明性・ファクトチェック・情報開示レイヤー.

AI がブラックボックスにならないために:
1. AI が参考にしたソース・情報をユーザーに開示する
2. ユーザーが正確な承認判断をするための情報を提示する
3. AI とユーザー間のファクトチェックを双方向で行う
4. 計画段階での対話・すり合わせを促進する

このモジュールは全ての AI 出力に透明性メタデータを付与し、
承認リクエスト時にユーザーが判断に必要な情報を確実に得られるようにする。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# データ型
# ---------------------------------------------------------------------------


class SourceType(str, Enum):
    """AI が参照した情報のソース種別."""

    WEB_PAGE = "web_page"  # Web ページ
    DOCUMENTATION = "documentation"  # 公式ドキュメント
    API_RESPONSE = "api_response"  # API レスポンス
    DATABASE = "database"  # 内部データベース
    USER_INPUT = "user_input"  # ユーザー入力
    LLM_KNOWLEDGE = "llm_knowledge"  # LLM の内部知識（カットオフ日付付き）
    FILE_CONTENT = "file_content"  # ローカルファイル
    PLUGIN_MANIFEST = "plugin_manifest"  # プラグインマニフェスト
    COMMUNITY_REGISTRY = "community_registry"  # コミュニティレジストリ


class ConfidenceLevel(str, Enum):
    """情報の確信度."""

    VERIFIED = "verified"  # ファクトチェック済み
    HIGH = "high"  # 高い確信度
    MEDIUM = "medium"  # 中程度
    LOW = "low"  # 低い（推測を含む）
    UNVERIFIED = "unverified"  # 未検証


class ApprovalInfoType(str, Enum):
    """承認時にユーザーに提示する情報の種別."""

    COST = "cost"  # コスト・料金
    RISK = "risk"  # リスク
    PERMISSION = "permission"  # 必要な権限
    EXTERNAL_ACCESS = "external_access"  # 外部アクセス
    DATA_FLOW = "data_flow"  # データの流れ
    REVERSIBILITY = "reversibility"  # 操作の取り消し可否
    DEPENDENCY = "dependency"  # 依存関係
    SOURCE_REFERENCE = "source_reference"  # 参考ソース


@dataclass
class SourceReference:
    """AI が参照した情報のソース参照."""

    source_type: SourceType
    title: str
    uri: str = ""  # URL やファイルパス
    snippet: str = ""  # 参照した部分の抜粋
    accessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    note: str = ""  # 補足情報


@dataclass
class FactCheckItem:
    """ファクトチェック項目."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    claim: str = ""  # AI の主張
    sources: list[SourceReference] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    verified_by_user: bool = False
    user_feedback: str = ""  # ユーザーからのフィードバック
    needs_verification: bool = False  # ユーザーの確認が必要


@dataclass
class ApprovalInfo:
    """承認判断に必要な情報."""

    info_type: ApprovalInfoType
    title: str
    detail: str
    severity: str = "info"  # info, warning, critical


@dataclass
class TransparencyReport:
    """AI 出力に付与する透明性レポート.

    AI のあらゆる出力（計画、提案、操作結果等）に付与し、
    ユーザーが AI の判断根拠を確認できるようにする。
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # AI が参照した情報源
    sources: list[SourceReference] = field(default_factory=list)

    # ファクトチェック項目
    fact_checks: list[FactCheckItem] = field(default_factory=list)

    # 承認に必要な情報
    approval_info: list[ApprovalInfo] = field(default_factory=list)

    # AI の推論プロセス概要
    reasoning_summary: str = ""

    # AI が判断に自信がない点
    uncertainties: list[str] = field(default_factory=list)

    # ユーザーへの質問・確認事項
    questions_for_user: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 透明性ビルダー — 各モジュールがレポートを構築するためのヘルパー
# ---------------------------------------------------------------------------


class TransparencyBuilder:
    """透明性レポートを段階的に構築するビルダー.

    各サービス・オーケストレーションモジュールがこのビルダーを使って
    AI の判断根拠を記録し、最終的にユーザーに提示する。
    """

    def __init__(self) -> None:
        self._report = TransparencyReport()

    def add_source(
        self,
        source_type: SourceType,
        title: str,
        uri: str = "",
        snippet: str = "",
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        note: str = "",
    ) -> TransparencyBuilder:
        """参照ソースを追加する."""
        self._report.sources.append(
            SourceReference(
                source_type=source_type,
                title=title,
                uri=uri,
                snippet=snippet,
                confidence=confidence,
                note=note,
            )
        )
        return self

    def add_fact_check(
        self,
        claim: str,
        sources: list[SourceReference] | None = None,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        needs_verification: bool = False,
    ) -> TransparencyBuilder:
        """ファクトチェック項目を追加する."""
        self._report.fact_checks.append(
            FactCheckItem(
                claim=claim,
                sources=sources or [],
                confidence=confidence,
                needs_verification=needs_verification,
            )
        )
        return self

    def add_approval_info(
        self,
        info_type: ApprovalInfoType | str,
        title: str,
        detail: str,
        severity: str = "info",
    ) -> TransparencyBuilder:
        """承認判断に必要な情報を追加する."""
        if isinstance(info_type, str):
            info_type = ApprovalInfoType(info_type)
        self._report.approval_info.append(
            ApprovalInfo(
                info_type=info_type,
                title=title,
                detail=detail,
                severity=severity,
            )
        )
        return self

    def set_reasoning(self, summary: str) -> TransparencyBuilder:
        """AI の推論概要を設定する."""
        self._report.reasoning_summary = summary
        return self

    def add_uncertainty(self, uncertainty: str) -> TransparencyBuilder:
        """AI が自信がない点を追加する."""
        self._report.uncertainties.append(uncertainty)
        return self

    def add_question(self, question: str) -> TransparencyBuilder:
        """ユーザーへの確認事項を追加する."""
        self._report.questions_for_user.append(question)
        return self

    def build(self) -> TransparencyReport:
        """レポートを生成する."""
        return self._report

    def to_dict(self) -> dict:
        """レポートを辞書に変換する（API レスポンス用）."""
        report = self._report
        return {
            "id": report.id,
            "created_at": report.created_at.isoformat(),
            "sources": [
                {
                    "type": s.source_type.value,
                    "title": s.title,
                    "uri": s.uri,
                    "snippet": s.snippet,
                    "confidence": s.confidence.value,
                    "note": s.note,
                }
                for s in report.sources
            ],
            "fact_checks": [
                {
                    "id": fc.id,
                    "claim": fc.claim,
                    "confidence": fc.confidence.value,
                    "needs_verification": fc.needs_verification,
                    "verified_by_user": fc.verified_by_user,
                    "sources": [
                        {"type": s.source_type.value, "title": s.title, "uri": s.uri}
                        for s in fc.sources
                    ],
                }
                for fc in report.fact_checks
            ],
            "approval_info": [
                {
                    "type": ai.info_type.value,
                    "title": ai.title,
                    "detail": ai.detail,
                    "severity": ai.severity,
                }
                for ai in report.approval_info
            ],
            "reasoning_summary": report.reasoning_summary,
            "uncertainties": report.uncertainties,
            "questions_for_user": report.questions_for_user,
        }


# ---------------------------------------------------------------------------
# プラグインインストール用の透明性レポート生成
# ---------------------------------------------------------------------------


def build_plugin_install_transparency(
    template: dict,
    env_report_dict: dict,
) -> dict:
    """プラグインインストール時の透明性レポートを生成する.

    ユーザーがプラグインをインストールする前に:
    - このプラグインが何をするか
    - どんな外部アクセスが必要か
    - どんなコストがかかるか
    - 何が安全で何がリスクか
    を明確に提示する。

    Args:
        template: プラグインテンプレート
        env_report_dict: 環境チェック結果

    Returns:
        透明性レポート辞書
    """
    builder = TransparencyBuilder()

    # ソース情報
    source_uri = template.get("source_uri", "")
    if source_uri:
        builder.add_source(
            source_type=SourceType.WEB_PAGE,
            title=f"{template['name']} の公式リポジトリ",
            uri=source_uri,
            confidence=ConfidenceLevel.VERIFIED,
            note="プラグイン情報の公式ソース",
        )

    pypi = template.get("pypi_package")
    if pypi:
        builder.add_source(
            source_type=SourceType.COMMUNITY_REGISTRY,
            title=f"PyPI: {pypi}",
            uri=f"https://pypi.org/project/{pypi}/",
            confidence=ConfidenceLevel.VERIFIED,
            note="パッケージの公開情報",
        )

    builder.add_source(
        source_type=SourceType.PLUGIN_MANIFEST,
        title="ZEO プラグインカタログ",
        uri="",
        confidence=ConfidenceLevel.HIGH,
        note="ZEO 内部のプラグインカタログから取得",
    )

    # ファクトチェック項目
    builder.add_fact_check(
        claim=f"{template['name']} はオープンソースで、ライセンスは {template.get('license', '不明')}",
        sources=[
            SourceReference(
                source_type=SourceType.WEB_PAGE,
                title="LICENSE",
                uri=source_uri,
                confidence=ConfidenceLevel.HIGH if source_uri else ConfidenceLevel.LOW,
            )
        ],
        confidence=ConfidenceLevel.HIGH if source_uri else ConfidenceLevel.LOW,
        needs_verification=not source_uri,
    )

    # 承認に必要な情報
    # コスト
    requirements = template.get("requirements", [])
    has_paid_api = any(
        r.get("type") == "api_key"
        and r.get("required", True)
        and "free" not in r.get("install_hint", "").lower()
        for r in requirements
    )
    if has_paid_api:
        builder.add_approval_info(
            info_type=ApprovalInfoType.COST,
            title="API 利用料金が発生する可能性",
            detail=(
                "このプラグインは外部 API キーが必要です。"
                "利用量に応じた API 料金が発生する場合があります。"
                "無料枠や代替手段がある場合はその情報も確認してください。"
            ),
            severity="warning",
        )
    else:
        builder.add_approval_info(
            info_type=ApprovalInfoType.COST,
            title="追加コストなし",
            detail="このプラグインは無料で利用できます（ローカル実行 or 無料 API）。",
            severity="info",
        )

    # 外部アクセス
    safety = template.get("safety", {})
    dangerous_ops = safety.get("dangerous_operations", [])
    if dangerous_ops:
        builder.add_approval_info(
            info_type=ApprovalInfoType.EXTERNAL_ACCESS,
            title="外部アクセスを行う操作",
            detail=f"以下の操作は承認が必要です: {', '.join(dangerous_ops)}",
            severity="warning",
        )

    # データフロー
    has_internet = any(
        r.get("type") in ("api_key", "env_var")
        or r.get("name", "") in ("SUNO_COOKIE", "SLACK_BOT_TOKEN")
        for r in requirements
    )
    if has_internet:
        builder.add_approval_info(
            info_type=ApprovalInfoType.DATA_FLOW,
            title="外部サービスとの通信",
            detail="このプラグインは外部サービスにデータを送信します。送信内容は監査ログに記録されます。",
            severity="warning",
        )

    # 権限
    required_perms = template.get("required_permissions", [])
    if required_perms:
        builder.add_approval_info(
            info_type=ApprovalInfoType.PERMISSION,
            title="必要な権限",
            detail=f"必要な権限: {', '.join(required_perms)}",
            severity="info",
        )

    # 可逆性
    builder.add_approval_info(
        info_type=ApprovalInfoType.REVERSIBILITY,
        title="アンインストール可能",
        detail="このプラグインはいつでもアンインストールできます。pip パッケージは残りますが、ZEO からの登録は解除されます。",
        severity="info",
    )

    # 推論概要
    builder.set_reasoning(
        f"プラグイン '{template['name']}' のインストールを提案しました。"
        f"カテゴリ: {template.get('category', '不明')}。"
        f"ソース: {source_uri or '内部カタログ'}。"
    )

    # 不確実性
    if not source_uri:
        builder.add_uncertainty("プラグインのソース URI が不明です。安全性の検証が困難です。")

    if template.get("adapter", {}).get("class") is None:
        builder.add_uncertainty(
            "このプラグインのアダプタは未実装です。"
            "コミュニティからの貢献を待つか、手動で実装が必要です。"
        )

    # ユーザーへの質問
    setup_instructions = env_report_dict.get("setup_instructions", [])
    if setup_instructions:
        builder.add_question(
            "以下のセットアップ手順を確認してください:\n"
            + "\n".join(f"  - {s}" for s in setup_instructions)
        )

    return builder.to_dict()
