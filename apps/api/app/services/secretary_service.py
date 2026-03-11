"""秘書サービス — CEO の思考吐き出し・整理・蓄積.

CEO が脳内の思考やアイデア、ToDo をすべて投げ込む場所として機能し、
情報を分類・整理・蓄積して「資産」として活用する。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, String, Text, Uuid, func, select, Boolean, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ThoughtCategory(str, Enum):
    """思考の分類."""

    IDEA = "idea"  # アイデア・ひらめき
    TODO = "todo"  # やるべきこと
    DECISION = "decision"  # 意思決定・判断
    REFLECTION = "reflection"  # 振り返り・気づき
    STRATEGY = "strategy"  # 戦略・方針
    PROBLEM = "problem"  # 課題・困りごと
    OPPORTUNITY = "opportunity"  # 機会・チャンス
    MEMO = "memo"  # メモ・雑記
    DAILY_LOG = "daily_log"  # その日の記録


class ThoughtPriority(str, Enum):
    """思考の優先度."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BrainDumpRecord(Base):
    """CEO のブレインダンプ記録."""

    __tablename__ = "brain_dumps"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(60), default="memo")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    action_items_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    linked_ticket_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )


class DailySummaryRecord(Base):
    """1 日のブレインダンプの要約."""

    __tablename__ = "daily_summaries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    summary_date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    total_dumps: Mapped[int] = mapped_column(Integer, default=0)
    ideas_count: Mapped[int] = mapped_column(Integer, default=0)
    todos_count: Mapped[int] = mapped_column(Integer, default=0)
    key_decisions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    action_items: Mapped[list | None] = mapped_column(JSON, nullable=True)
    insights: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# キーワードベース自動分類
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    ThoughtCategory.IDEA: [
        "アイデア",
        "思いつき",
        "ひらめき",
        "こうしたら",
        "〜したい",
        "idea",
        "思いついた",
        "面白い",
        "新しく",
    ],
    ThoughtCategory.TODO: [
        "やる",
        "やること",
        "todo",
        "タスク",
        "やらないと",
        "忘れずに",
        "明日",
        "今日中",
        "対応する",
        "確認する",
    ],
    ThoughtCategory.DECISION: [
        "決定",
        "決めた",
        "判断",
        "方針",
        "決断",
        "〜にする",
        "これでいく",
        "採用",
        "却下",
    ],
    ThoughtCategory.PROBLEM: [
        "課題",
        "問題",
        "困って",
        "困った",
        "うまくいかない",
        "ボトルネック",
        "改善",
        "修正",
        "バグ",
    ],
    ThoughtCategory.STRATEGY: [
        "戦略",
        "方針",
        "ロードマップ",
        "計画",
        "長期",
        "ビジョン",
        "目標",
        "KPI",
        "OKR",
    ],
    ThoughtCategory.OPPORTUNITY: [
        "チャンス",
        "機会",
        "可能性",
        "パートナー",
        "提携",
        "市場",
        "トレンド",
        "需要",
    ],
    ThoughtCategory.REFLECTION: [
        "振り返り",
        "反省",
        "学び",
        "気づき",
        "教訓",
        "よかった",
        "改善点",
        "次回",
    ],
}

_PRIORITY_KEYWORDS: dict[str, list[str]] = {
    ThoughtPriority.HIGH: [
        "緊急",
        "至急",
        "重要",
        "urgent",
        "ASAP",
        "今すぐ",
        "最優先",
        "マスト",
        "must",
    ],
    ThoughtPriority.LOW: [
        "いつか",
        "余裕あれば",
        "低優先",
        "nice to have",
        "そのうち",
        "暇なとき",
    ],
}


def auto_classify(text: str) -> tuple[str, str]:
    """テキストからカテゴリと優先度を自動推定する."""
    text_lower = text.lower()

    category = ThoughtCategory.MEMO
    max_matches = 0
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > max_matches:
            max_matches = matches
            category = cat

    priority = ThoughtPriority.MEDIUM
    for prio, keywords in _PRIORITY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            priority = prio
            break

    return category, priority


def extract_action_items(text: str) -> list[str]:
    """テキストからアクションアイテムを抽出する."""
    action_items: list[str] = []
    lines = text.split("\n")
    action_markers = [
        "- [ ]",
        "□",
        "TODO:",
        "やること:",
        "対応:",
        "確認:",
        "タスク:",
        "アクション:",
    ]
    for line in lines:
        stripped = line.strip()
        if any(
            stripped.startswith(m) or stripped.startswith(m.lower())
            for m in action_markers
        ):
            # マーカーを除去してアクションアイテムとして追加
            for m in action_markers:
                if stripped.startswith(m):
                    stripped = stripped[len(m) :].strip()
                    break
            if stripped:
                action_items.append(stripped)
    return action_items


def generate_title(text: str, max_len: int = 60) -> str:
    """テキストからタイトルを生成する."""
    first_line = text.strip().split("\n")[0].strip()
    if len(first_line) <= max_len:
        return first_line
    return first_line[: max_len - 3] + "..."


# ---------------------------------------------------------------------------
# Secretary Service
# ---------------------------------------------------------------------------


class SecretaryService:
    """秘書サービス — CEO の思考を整理・蓄積する."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def brain_dump(
        self,
        company_id: str,
        raw_text: str,
        *,
        user_id: str | None = None,
        category: str | None = None,
        priority: str | None = None,
        tags: list[str] | None = None,
    ) -> BrainDumpRecord:
        """思考を受け取り、分類・整理して保存する."""
        cid = uuid.UUID(company_id)
        uid = uuid.UUID(user_id) if user_id else None

        # 自動分類
        auto_cat, auto_prio = auto_classify(raw_text)
        final_category = category or auto_cat
        final_priority = priority or auto_prio

        # アクションアイテム抽出
        action_items = extract_action_items(raw_text)

        # タイトル生成
        title = generate_title(raw_text)

        record = BrainDumpRecord(
            id=uuid.uuid4(),
            company_id=cid,
            user_id=uid,
            raw_text=raw_text,
            category=final_category,
            priority=final_priority,
            title=title,
            tags_json=tags or [],
            action_items_json=action_items if action_items else None,
            is_processed=False,
        )
        self._db.add(record)
        await self._db.flush()
        return record

    async def list_dumps(
        self,
        company_id: str,
        *,
        category: str | None = None,
        priority: str | None = None,
        is_archived: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[BrainDumpRecord]:
        """ブレインダンプ一覧を取得."""
        cid = uuid.UUID(company_id)
        stmt = select(BrainDumpRecord).where(
            BrainDumpRecord.company_id == cid,
            BrainDumpRecord.is_archived == is_archived,
        )
        if category:
            stmt = stmt.where(BrainDumpRecord.category == category)
        if priority:
            stmt = stmt.where(BrainDumpRecord.priority == priority)

        stmt = (
            stmt.order_by(BrainDumpRecord.created_at.desc()).offset(offset).limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_dump(self, dump_id: str) -> BrainDumpRecord | None:
        """単一のブレインダンプを取得."""
        result = await self._db.execute(
            select(BrainDumpRecord).where(BrainDumpRecord.id == uuid.UUID(dump_id))
        )
        return result.scalar_one_or_none()

    async def update_dump(
        self,
        dump_id: str,
        *,
        category: str | None = None,
        priority: str | None = None,
        tags: list[str] | None = None,
        is_archived: bool | None = None,
        is_processed: bool | None = None,
    ) -> BrainDumpRecord | None:
        """ブレインダンプを更新."""
        record = await self.get_dump(dump_id)
        if not record:
            return None

        if category is not None:
            record.category = category
        if priority is not None:
            record.priority = priority
        if tags is not None:
            record.tags_json = tags
        if is_archived is not None:
            record.is_archived = is_archived
        if is_processed is not None:
            record.is_processed = is_processed

        await self._db.flush()
        return record

    async def search_dumps(
        self,
        company_id: str,
        query: str,
        *,
        limit: int = 20,
    ) -> list[BrainDumpRecord]:
        """ブレインダンプをキーワード検索."""
        cid = uuid.UUID(company_id)
        pattern = f"%{query}%"
        stmt = (
            select(BrainDumpRecord)
            .where(
                BrainDumpRecord.company_id == cid,
                BrainDumpRecord.is_archived.is_(False),
                (
                    BrainDumpRecord.raw_text.ilike(pattern)
                    | BrainDumpRecord.title.ilike(pattern)
                ),
            )
            .order_by(BrainDumpRecord.created_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_action_items(
        self,
        company_id: str,
        *,
        unprocessed_only: bool = True,
    ) -> list[dict]:
        """全ブレインダンプからアクションアイテムを集約."""
        cid = uuid.UUID(company_id)
        stmt = select(BrainDumpRecord).where(
            BrainDumpRecord.company_id == cid,
            BrainDumpRecord.is_archived.is_(False),
            BrainDumpRecord.action_items_json.isnot(None),
        )
        if unprocessed_only:
            stmt = stmt.where(BrainDumpRecord.is_processed.is_(False))

        stmt = stmt.order_by(BrainDumpRecord.created_at.desc())
        result = await self._db.execute(stmt)
        records = result.scalars().all()

        items: list[dict] = []
        for record in records:
            if record.action_items_json:
                for item in record.action_items_json:
                    items.append(
                        {
                            "action": item,
                            "source_dump_id": str(record.id),
                            "priority": record.priority,
                            "category": record.category,
                            "created_at": record.created_at.isoformat()
                            if record.created_at
                            else None,
                        }
                    )
        return items

    async def get_daily_stats(
        self,
        company_id: str,
        date_str: str,
    ) -> dict:
        """指定日のブレインダンプ統計を取得."""
        cid = uuid.UUID(company_id)

        stmt = select(BrainDumpRecord).where(
            BrainDumpRecord.company_id == cid,
            func.date(BrainDumpRecord.created_at) == date_str,
        )
        result = await self._db.execute(stmt)
        records = list(result.scalars().all())

        category_counts: dict[str, int] = {}
        total_action_items = 0
        for r in records:
            category_counts[r.category] = category_counts.get(r.category, 0) + 1
            if r.action_items_json:
                total_action_items += len(r.action_items_json)

        return {
            "date": date_str,
            "total_dumps": len(records),
            "category_breakdown": category_counts,
            "total_action_items": total_action_items,
            "ideas_count": category_counts.get(ThoughtCategory.IDEA, 0),
            "todos_count": category_counts.get(ThoughtCategory.TODO, 0),
        }
