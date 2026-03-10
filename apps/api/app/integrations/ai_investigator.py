"""AI Investigator — AIによるログ・DB参照で調査を完結させる.

AIがログやデータベースを参照できることで、最初から最後まで
試行錯誤のループが完結し、調査が瞬時に終わる。

提供機能:
  - 監査ログの検索と分析
  - DB直接クエリ（読み取り専用・安全なサブセット）
  - エラーログの集約と分析
  - パフォーマンスメトリクスの取得
  - 実行トレースの横断検索
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# AIがアクセス可能なテーブル（読み取り専用）
ALLOWED_TABLES = frozenset(
    {
        "tickets",
        "tasks",
        "task_runs",
        "agents",
        "skills",
        "audit_logs",
        "experience_memory",
        "failure_taxonomy",
        "knowledge_store",
        "change_detections",
        "agent_sessions",
        "specs",
        "plans",
        "artifacts",
        "reviews",
        "heartbeat_runs",
        "cost_ledgers",
    }
)

# SQLインジェクション防止: 禁止キーワード
FORBIDDEN_SQL_KEYWORDS = frozenset(
    {
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "EXEC",
        "EXECUTE",
        "GRANT",
        "REVOKE",
        "INTO OUTFILE",
        "INTO DUMPFILE",
        "LOAD_FILE",
    }
)


@dataclass
class InvestigationResult:
    """調査結果."""

    query: str
    success: bool
    data: list[dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    error: str | None = None
    duration_ms: int = 0
    analysis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "success": self.success,
            "data": self.data[:100],  # 最大100行
            "row_count": self.row_count,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "analysis": self.analysis,
        }


@dataclass
class LogEntry:
    """ログエントリ."""

    timestamp: float
    level: str
    source: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)


class AIInvestigator:
    """AIエージェント用のDB/ログ調査ツール."""

    def __init__(self, max_rows: int = 500) -> None:
        self._max_rows = max_rows
        self._investigation_log: list[dict[str, Any]] = []

    def _validate_query(self, query: str) -> tuple[bool, str]:
        """クエリの安全性を検証."""
        upper = query.upper().strip()

        # SELECT文のみ許可
        if not upper.startswith("SELECT"):
            return False, "SELECT文のみ実行可能です"

        # 禁止キーワードチェック
        for kw in FORBIDDEN_SQL_KEYWORDS:
            if kw in upper:
                return False, f"禁止されたキーワード '{kw}' が含まれています"

        # テーブル名検証（FROM句から抽出）
        # 簡易的なチェック — 本番ではSQLパーサーを使用
        return True, ""

    async def query_db(
        self,
        db: AsyncSession,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> InvestigationResult:
        """安全なDB読み取りクエリを実行."""
        valid, err = self._validate_query(query)
        if not valid:
            return InvestigationResult(
                query=query,
                success=False,
                error=err,
            )

        start = time.time()
        try:
            result = await db.execute(text(query), params or {})
            rows = result.mappings().all()
            duration_ms = int((time.time() - start) * 1000)

            data = [dict(row) for row in rows[: self._max_rows]]
            # datetime等をシリアライズ可能にする
            for row in data:
                for k, v in row.items():
                    if hasattr(v, "isoformat"):
                        row[k] = v.isoformat()
                    elif isinstance(v, bytes):
                        row[k] = v.hex()

            inv_result = InvestigationResult(
                query=query,
                success=True,
                data=data,
                row_count=len(rows),
                duration_ms=duration_ms,
            )

            self._log_investigation("db_query", query, inv_result)
            return inv_result

        except Exception as exc:
            duration_ms = int((time.time() - start) * 1000)
            return InvestigationResult(
                query=query,
                success=False,
                error=str(exc),
                duration_ms=duration_ms,
            )

    async def search_audit_logs(
        self,
        db: AsyncSession,
        *,
        action_type: str | None = None,
        entity_type: str | None = None,
        actor_id: str | None = None,
        since_hours: int = 24,
        limit: int = 100,
    ) -> InvestigationResult:
        """監査ログを検索."""
        conditions = []
        params: dict[str, Any] = {"limit": min(limit, self._max_rows)}

        if action_type:
            conditions.append("action = :action")
            params["action"] = action_type
        if entity_type:
            conditions.append("entity_type = :entity_type")
            params["entity_type"] = entity_type
        if actor_id:
            conditions.append("actor_id = :actor_id")
            params["actor_id"] = actor_id

        where = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM audit_logs WHERE {where} ORDER BY created_at DESC LIMIT :limit"

        return await self.query_db(db, query, params)

    async def analyze_errors(
        self,
        db: AsyncSession,
        since_hours: int = 24,
        limit: int = 50,
    ) -> InvestigationResult:
        """エラーパターンを分析."""
        query = """
            SELECT
                category,
                subcategory,
                description,
                occurrence_count,
                recovery_success_rate,
                last_occurred
            FROM failure_taxonomy
            ORDER BY occurrence_count DESC, last_occurred DESC
            LIMIT :limit
        """
        return await self.query_db(db, query, {"limit": limit})

    async def get_task_execution_history(
        self,
        db: AsyncSession,
        task_id: str | None = None,
        limit: int = 50,
    ) -> InvestigationResult:
        """タスク実行履歴を取得."""
        if task_id:
            query = """
                SELECT * FROM task_runs
                WHERE task_id = :task_id
                ORDER BY created_at DESC
                LIMIT :limit
            """
            params = {"task_id": task_id, "limit": limit}
        else:
            query = """
                SELECT * FROM task_runs
                ORDER BY created_at DESC
                LIMIT :limit
            """
            params = {"limit": limit}
        return await self.query_db(db, query, params)

    async def search_knowledge(
        self,
        db: AsyncSession,
        search_query: str,
        category: str | None = None,
        limit: int = 50,
    ) -> InvestigationResult:
        """ナレッジストアを検索."""
        conditions = ["is_active = 1"]
        params: dict[str, Any] = {"limit": limit, "query": f"%{search_query}%"}

        conditions.append("(key LIKE :query OR value LIKE :query)")
        if category:
            conditions.append("category = :category")
            params["category"] = category

        where = " AND ".join(conditions)
        query = f"SELECT * FROM knowledge_store WHERE {where} ORDER BY use_count DESC LIMIT :limit"

        return await self.query_db(db, query, params)

    async def get_system_metrics(self, db: AsyncSession) -> dict[str, Any]:
        """システムメトリクスを取得."""
        metrics: dict[str, Any] = {}

        # テーブル行数カウント (allowed tables whitelist - no dynamic SQL)
        _ALLOWED_TABLES = frozenset(
            ["tickets", "tasks", "agents", "skills", "audit_logs"]
        )
        for table in _ALLOWED_TABLES:
            try:
                # Use SQLAlchemy text with literal_column to avoid f-string SQL injection
                from sqlalchemy import literal_column
                result = await db.execute(
                    select(func.count()).select_from(literal_column(table))
                )
                row = result.one_or_none()
                metrics[f"{table}_count"] = row[0] if row else 0
            except Exception:
                metrics[f"{table}_count"] = "N/A"

        return metrics

    def _log_investigation(
        self, inv_type: str, query: str, result: InvestigationResult
    ) -> None:
        """調査の記録."""
        self._investigation_log.append(
            {
                "type": inv_type,
                "query": query,
                "success": result.success,
                "row_count": result.row_count,
                "duration_ms": result.duration_ms,
                "timestamp": time.time(),
            }
        )
        # 古いログを削除
        if len(self._investigation_log) > 1000:
            self._investigation_log = self._investigation_log[-500:]

    def get_investigation_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """調査履歴を取得."""
        return self._investigation_log[-limit:]


# Global singleton
ai_investigator = AIInvestigator()
