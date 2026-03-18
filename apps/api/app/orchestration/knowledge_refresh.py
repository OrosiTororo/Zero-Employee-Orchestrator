"""Knowledge Refresh — コンテキストウィンドウ制限への対応.

Zero-Employee Orchestrator.md §5, §11.4.2 に基づき、コンテキストウィンドウの
制限に対応するため、履歴管理機構と必要情報の再取得機構を設ける。

Knowledge Pipeline の段階:
1. 取得
2. 抽出
3. 分割
4. インデックス化
5. 検索
6. 引用・要約
7. 検証済み知識への昇格または却下
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class KnowledgeStatus(str, Enum):
    """知識のステータス."""

    RAW = "raw"  # 未処理
    EXTRACTED = "extracted"  # 抽出済み
    INDEXED = "indexed"  # インデックス済み
    VERIFIED = "verified"  # 検証済み
    EXPERIMENTAL = "experimental"  # 実験的
    REJECTED = "rejected"  # 却下


class KnowledgeType(str, Enum):
    """知識の種類（§8.0.1, §8.5）."""

    CONVERSATION_LOG = "conversation_log"  # 会話履歴
    REUSABLE_IMPROVEMENT = "reusable_improvement"  # 再利用可能な改善知識
    EXPERIMENTAL = "experimental_knowledge"  # 実験的知識
    VERIFIED = "verified_knowledge"  # 検証済み知識
    EXPERIENCE_MEMORY = "experience_memory"  # 成功パターン
    FAILURE_TAXONOMY = "failure_taxonomy"  # 失敗分類
    POLICY_MEMORY = "policy_memory"  # 承認条件・禁止事項
    SKILL_IMPROVEMENT = "skill_improvement"  # Skill 改善知識
    PLUGIN_OPERATION = "plugin_operation"  # Plugin 運用ノウハウ


@dataclass
class KnowledgeEntry:
    """知識エントリ."""

    id: str
    title: str
    content: str
    knowledge_type: KnowledgeType
    status: KnowledgeStatus = KnowledgeStatus.RAW
    source: str = ""
    tags: list[str] = field(default_factory=list)
    approved_by: str | None = None
    effective_conditions: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class KnowledgeRefreshResult:
    """Knowledge Refresh の結果."""

    context_entries: list[KnowledgeEntry]
    total_tokens_estimated: int
    truncated: bool
    summary: str


class KnowledgeStore:
    """知識の保存と検索.

    改善知識を用途ごとに分離して保存する（§8.5）:
    - Experience Memory: 成功した実行パターン
    - Failure Taxonomy: 失敗分類、再発防止策
    - Policy Memory: 承認条件、禁止事項
    - Skill Improvement Memory: Skill 改善知識
    - Plugin Operation Memory: 業務運用ノウハウ
    """

    def __init__(self) -> None:
        self._entries: list[KnowledgeEntry] = []

    def add(self, entry: KnowledgeEntry) -> None:
        self._entries.append(entry)

    def search(
        self,
        query: str,
        *,
        knowledge_type: KnowledgeType | None = None,
        status: KnowledgeStatus | None = None,
        limit: int = 10,
    ) -> list[KnowledgeEntry]:
        """知識を検索する."""
        results = []
        query_lower = query.lower()
        for entry in self._entries:
            if knowledge_type and entry.knowledge_type != knowledge_type:
                continue
            if status and entry.status != status:
                continue
            if query_lower in entry.title.lower() or query_lower in entry.content.lower():
                results.append(entry)
            if len(results) >= limit:
                break
        return results

    def promote_to_verified(self, entry_id: str, approved_by: str) -> bool:
        """知識を検証済みに昇格する."""
        for entry in self._entries:
            if entry.id == entry_id:
                entry.status = KnowledgeStatus.VERIFIED
                entry.approved_by = approved_by
                entry.updated_at = datetime.now(UTC)
                return True
        return False

    def reject(self, entry_id: str, reason: str = "") -> bool:
        """知識を却下する."""
        for entry in self._entries:
            if entry.id == entry_id:
                entry.status = KnowledgeStatus.REJECTED
                entry.updated_at = datetime.now(UTC)
                return True
        return False

    def get_by_type(self, knowledge_type: KnowledgeType) -> list[KnowledgeEntry]:
        return [e for e in self._entries if e.knowledge_type == knowledge_type]


def refresh_context(
    store: KnowledgeStore,
    task_context: str,
    max_tokens: int = 8000,
) -> KnowledgeRefreshResult:
    """タスク実行に必要な知識をリフレッシュする.

    コンテキストウィンドウの制限に対応し、関連する知識のみを取得する。
    """
    relevant = store.search(task_context, status=KnowledgeStatus.VERIFIED, limit=20)

    total_tokens = 0
    selected: list[KnowledgeEntry] = []
    truncated = False

    for entry in relevant:
        estimated = len(entry.content) // 4  # 簡易トークン推定
        if total_tokens + estimated > max_tokens:
            truncated = True
            break
        selected.append(entry)
        total_tokens += estimated

    return KnowledgeRefreshResult(
        context_entries=selected,
        total_tokens_estimated=total_tokens,
        truncated=truncated,
        summary=f"{len(selected)} 件の関連知識を取得 (推定 {total_tokens} トークン)",
    )


# グローバルインスタンス
knowledge_store = KnowledgeStore()
