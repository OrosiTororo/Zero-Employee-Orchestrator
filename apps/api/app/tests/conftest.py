"""Test configuration and fixtures."""

import logging
import os
import pathlib
import sys
import uuid
from collections.abc import AsyncGenerator

# Ensure the repository root is importable so ``skills.builtin.*`` resolves
# during tests; production code reaches the same path via app/cli.py's
# bootstrap. apps/api/app/tests/conftest.py -> repo root is parents[4]
# (tests -> app -> api -> apps -> repo root).
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Allow tests to run with the default SECRET_KEY by enabling DEBUG mode.
# config.py raises RuntimeError when SECRET_KEY is an insecure placeholder
# and DEBUG=false, preventing accidental production use of default secrets.
# Must be set before importing any app module that reads settings at import time.
os.environ.setdefault("DEBUG", "true")

# Suppress litellm's cleanup handler that tries to open a new event loop after
# the session loop has been closed, producing a harmless "I/O operation on
# closed file" log error at the end of the test suite.
logging.getLogger("litellm").setLevel(logging.CRITICAL)

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool  # noqa: E402

# Ensure all ORM models are registered with Base before create_all
import app.models as _models  # noqa: E402, F401
from app.api.deps.database import get_db  # noqa: E402
from app.api.routes.auth import get_current_user  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.multi_model_service import BrainstormSessionRecord as _BSR  # noqa: E402, F401

# slowapi rate limiting is disabled by default during tests — per-endpoint
# limits like `5/minute` on /auth/register otherwise leak across tests because
# the limiter key is the client IP and ASGITransport always reports the same
# one. Tests that specifically verify rate-limit behaviour must opt back in via
# the ``rate_limit_enabled`` fixture (see below).
limiter.enabled = False


@pytest_asyncio.fixture
async def rate_limit_enabled():
    """Opt-in fixture for tests that exercise real rate-limit enforcement.

    Usage::

        async def test_something(client, rate_limit_enabled):
            ...

    The fixture flips the shared slowapi limiter on for the test body, resets
    its internal storage to avoid leakage from previous requests, and flips it
    back off on teardown so unrelated tests keep their blanket bypass.
    """
    limiter.enabled = True
    try:
        # Best-effort reset so prior requests in the same session do not
        # pre-consume the test's budget.
        reset = getattr(limiter, "reset", None)
        if callable(reset):
            reset()
        yield
    finally:
        limiter.enabled = False


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def setup_db():
    """Create tables before each test and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
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


@pytest_asyncio.fixture(loop_scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture(loop_scope="session")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
