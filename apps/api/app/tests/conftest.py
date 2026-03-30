"""Test configuration and fixtures."""

import asyncio
import os
import uuid
from collections.abc import AsyncGenerator

# Allow tests to run with the default SECRET_KEY by enabling DEBUG mode.
# config.py raises RuntimeError when SECRET_KEY is an insecure placeholder
# and DEBUG=false, preventing accidental production use of default secrets.
os.environ.setdefault("DEBUG", "true")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure all ORM models are registered with Base before create_all
import app.models as _models  # noqa: F401
from app.api.deps.database import get_db
from app.api.routes.auth import get_current_user
from app.core.database import Base
from app.main import app
from app.models.user import User
from app.services.multi_model_service import BrainstormSessionRecord as _BSR  # noqa: F401

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_zero_employee_orchestrator.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


# Stub user returned by get_current_user in tests — bypasses JWT validation.
_TEST_USER = User(
    id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    email="test@example.com",
    display_name="Test User",
    role="admin",
    status="active",
)


async def override_get_current_user() -> User:
    return _TEST_USER


app.dependency_overrides[get_current_user] = override_get_current_user


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
