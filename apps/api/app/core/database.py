"""SQLAlchemy 2.x async database setup.

Connection pooling:
- SQLite uses ``NullPool`` (no pooling) because SQLite's file locking
  doesn't benefit from it.
- PostgreSQL / MySQL use ``QueuePool`` with ``pool_pre_ping`` to verify
  connections before use.
"""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings

_is_sqlite = "sqlite" in settings.DATABASE_URL

_pool_kwargs: dict = {}
if _is_sqlite:
    _pool_kwargs["poolclass"] = NullPool
else:
    _pool_kwargs["poolclass"] = QueuePool
    _pool_kwargs["pool_pre_ping"] = True
    _pool_kwargs["pool_size"] = 20
    _pool_kwargs["max_overflow"] = 10
    _pool_kwargs["pool_recycle"] = 1800  # Recycle connections every 30 min

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    **_pool_kwargs,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base with common column helpers."""

    pass


class TimestampMixin:
    """Mixin that adds created_at / updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """Dependency that yields an async session."""
    async with async_session_factory() as session:
        yield session
