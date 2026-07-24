"""Regression tests for the brainstorm session ORM registration."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database import Base
from app.services.multi_model_service import BrainstormSessionRecord


@pytest.mark.asyncio
async def test_create_all_registers_brainstorm_sessions_table():
    """The compatibility import must register the brainstorm sessions table."""
    assert BrainstormSessionRecord.__tablename__ == "brainstorm_sessions"

    engine = create_async_engine("sqlite+aiosqlite://")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            table_names = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
    finally:
        await engine.dispose()

    assert "brainstorm_sessions" in table_names
