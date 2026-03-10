"""Sentry Integration — バグ・エラー・パフォーマンス監視.

Sentry と連携してリアルタイムのエラー検出、パフォーマンス監視、
開発者通知を行う。Sentry SDK を使用したクラッシュレポーティングと
カスタムイベントトラッキングを提供。

参考: https://github.com/getsentry/sentry
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SeverityLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class EventType(str, Enum):
    ERROR = "error"
    PERFORMANCE = "performance"
    CRASH = "crash"
    CUSTOM = "custom"


@dataclass
class SentryEvent:
    """Sentry互換のイベント."""
    event_id: str = ""
    event_type: EventType = EventType.ERROR
    level: SeverityLevel = SeverityLevel.ERROR
    message: str = ""
    exception_type: str | None = None
    exception_value: str | None = None
    stacktrace: list[dict[str, Any]] = field(default_factory=list)
    tags: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)
    breadcrumbs: list[dict[str, Any]] = field(default_factory=list)
    contexts: dict[str, Any] = field(default_factory=dict)
    user: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    transaction: str | None = None
    duration_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "level": self.level.value,
            "message": self.message,
            "exception": {
                "type": self.exception_type,
                "value": self.exception_value,
            } if self.exception_type else None,
            "tags": self.tags,
            "extra": self.extra,
            "breadcrumbs": self.breadcrumbs,
            "contexts": self.contexts,
            "user": self.user,
            "timestamp": self.timestamp,
            "transaction": self.transaction,
            "duration_ms": self.duration_ms,
        }


class SentryIntegration:
    """Sentry互換のエラー監視プラットフォーム連携.

    Sentry SDK がインストールされている場合はそれを使用し、
    なければ内蔵のイベントストアに記録する。
    """

    def __init__(self, dsn: str | None = None, environment: str = "development") -> None:
        self._dsn = dsn
        self._environment = environment
        self._sdk_available = False
        self._events: list[SentryEvent] = []
        self._max_events = 5000
        self._alert_callbacks: list[Any] = []

        if dsn:
            self._try_init_sdk(dsn, environment)

    def _try_init_sdk(self, dsn: str, environment: str) -> None:
        """Sentry SDK の初期化を試行."""
        try:
            import sentry_sdk  # type: ignore[import-untyped]
            sentry_sdk.init(
                dsn=dsn,
                environment=environment,
                traces_sample_rate=0.2,
                profiles_sample_rate=0.1,
                enable_tracing=True,
            )
            self._sdk_available = True
            logger.info("Sentry SDK initialized (env: %s)", environment)
        except ImportError:
            logger.info("Sentry SDK not installed, using built-in event store")
        except Exception as exc:
            logger.warning("Sentry SDK init failed: %s", exc)

    def capture_exception(
        self,
        exc: Exception,
        *,
        tags: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
        user: dict[str, str] | None = None,
        level: SeverityLevel = SeverityLevel.ERROR,
    ) -> str:
        """例外をキャプチャ."""
        import traceback as tb
        import uuid

        event_id = str(uuid.uuid4())

        if self._sdk_available:
            try:
                import sentry_sdk  # type: ignore[import-untyped]
                with sentry_sdk.push_scope() as scope:
                    if tags:
                        for k, v in tags.items():
                            scope.set_tag(k, v)
                    if extra:
                        for k, v in extra.items():
                            scope.set_extra(k, v)
                    if user:
                        scope.set_user(user)
                    sentry_sdk.capture_exception(exc)
            except Exception as send_err:
                logger.debug("Sentry SDK send failed: %s", send_err)

        # 内蔵ストアにも記録
        event = SentryEvent(
            event_id=event_id,
            event_type=EventType.ERROR,
            level=level,
            message=str(exc),
            exception_type=type(exc).__name__,
            exception_value=str(exc),
            stacktrace=[
                {"filename": f.filename, "lineno": f.lineno, "function": f.name}
                for f in tb.extract_tb(exc.__traceback__)
            ] if exc.__traceback__ else [],
            tags=tags or {},
            extra=extra or {},
            user=user or {},
        )
        self._store_event(event)
        self._check_alerts(event)

        return event_id

    def capture_message(
        self,
        message: str,
        level: SeverityLevel = SeverityLevel.INFO,
        *,
        tags: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> str:
        """メッセージイベントをキャプチャ."""
        import uuid

        event_id = str(uuid.uuid4())

        if self._sdk_available:
            try:
                import sentry_sdk  # type: ignore[import-untyped]
                sentry_sdk.capture_message(message, level=level.value)
            except Exception:
                pass

        event = SentryEvent(
            event_id=event_id,
            event_type=EventType.CUSTOM,
            level=level,
            message=message,
            tags=tags or {},
            extra=extra or {},
        )
        self._store_event(event)
        return event_id

    def start_transaction(self, name: str, op: str = "task") -> TransactionContext:
        """パフォーマンストランザクションを開始."""
        return TransactionContext(
            integration=self,
            name=name,
            op=op,
            sdk_available=self._sdk_available,
        )

    def add_breadcrumb(
        self,
        message: str,
        category: str = "default",
        level: str = "info",
        data: dict[str, Any] | None = None,
    ) -> None:
        """パンくずリストに記録."""
        if self._sdk_available:
            try:
                import sentry_sdk  # type: ignore[import-untyped]
                sentry_sdk.add_breadcrumb(
                    message=message, category=category, level=level, data=data
                )
            except Exception:
                pass

    def on_alert(self, callback: Any) -> None:
        """アラートコールバックを登録."""
        self._alert_callbacks.append(callback)

    def get_recent_events(
        self,
        level: SeverityLevel | None = None,
        event_type: EventType | None = None,
        limit: int = 50,
    ) -> list[SentryEvent]:
        """最近のイベントを取得."""
        result = self._events
        if level:
            result = [e for e in result if e.level == level]
        if event_type:
            result = [e for e in result if e.event_type == event_type]
        return result[-limit:]

    def get_error_stats(self) -> dict[str, Any]:
        """エラー統計を取得."""
        now = time.time()
        hour_ago = now - 3600
        day_ago = now - 86400

        errors = [e for e in self._events if e.level in (SeverityLevel.ERROR, SeverityLevel.FATAL)]
        errors_1h = [e for e in errors if e.timestamp > hour_ago]
        errors_24h = [e for e in errors if e.timestamp > day_ago]

        # エラータイプ別集計
        by_type: dict[str, int] = {}
        for e in errors_24h:
            key = e.exception_type or "unknown"
            by_type[key] = by_type.get(key, 0) + 1

        return {
            "total_events": len(self._events),
            "errors_last_hour": len(errors_1h),
            "errors_last_24h": len(errors_24h),
            "error_types": by_type,
            "sdk_available": self._sdk_available,
            "environment": self._environment,
        }

    def _store_event(self, event: SentryEvent) -> None:
        if len(self._events) >= self._max_events:
            self._events = self._events[-(self._max_events // 2):]
        self._events.append(event)

    def _check_alerts(self, event: SentryEvent) -> None:
        if event.level in (SeverityLevel.ERROR, SeverityLevel.FATAL):
            for cb in self._alert_callbacks:
                try:
                    cb(event)
                except Exception as exc:
                    logger.debug("Alert callback failed: %s", exc)


class TransactionContext:
    """パフォーマンス計測用トランザクション."""

    def __init__(
        self,
        integration: SentryIntegration,
        name: str,
        op: str,
        sdk_available: bool,
    ) -> None:
        self._integration = integration
        self._name = name
        self._op = op
        self._sdk_available = sdk_available
        self._start_time: float = 0.0
        self._sdk_transaction: Any = None

    def __enter__(self) -> TransactionContext:
        self._start_time = time.time()
        if self._sdk_available:
            try:
                import sentry_sdk  # type: ignore[import-untyped]
                self._sdk_transaction = sentry_sdk.start_transaction(
                    name=self._name, op=self._op
                )
                self._sdk_transaction.__enter__()
            except Exception:
                pass
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        duration_ms = int((time.time() - self._start_time) * 1000)

        if self._sdk_transaction:
            try:
                self._sdk_transaction.__exit__(exc_type, exc_val, exc_tb)
            except Exception:
                pass

        import uuid
        event = SentryEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.PERFORMANCE,
            level=SeverityLevel.INFO,
            message=f"Transaction: {self._name}",
            transaction=self._name,
            duration_ms=duration_ms,
            tags={"op": self._op},
        )
        self._integration._store_event(event)

        if exc_val:
            self._integration.capture_exception(
                exc_val,
                tags={"transaction": self._name},
            )


def create_sentry_integration(
    dsn: str | None = None,
    environment: str = "development",
) -> SentryIntegration:
    """Sentry連携インスタンスを作成."""
    return SentryIntegration(dsn=dsn, environment=environment)


# Global instance (configure via settings)
sentry = SentryIntegration()
