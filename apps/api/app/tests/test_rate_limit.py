"""Verify the rate_limit_enabled fixture turns the slowapi limiter back on.

The conftest disables slowapi globally during tests to stop per-endpoint
limits from leaking across the suite. This test ensures that
``rate_limit_enabled`` re-enables enforcement for the duration of the test
(and for nothing else).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.rate_limit import limiter


@pytest.mark.asyncio
async def test_limiter_is_disabled_by_default(client: AsyncClient):
    assert limiter.enabled is False


@pytest.mark.asyncio
async def test_rate_limit_fixture_enables_limiter(rate_limit_enabled):
    assert limiter.enabled is True


@pytest.mark.asyncio
async def test_limiter_restores_after_fixture_teardown():
    # Running after the opt-in fixture test above, the blanket-disable should
    # still be in effect because the fixture tears down on exit.
    assert limiter.enabled is False


@pytest.mark.asyncio
async def test_register_blocks_after_five_requests(
    client: AsyncClient,
    rate_limit_enabled,
):
    """/auth/register is annotated `5/minute` — the sixth call must 429."""
    base = {"password": "test-password-long"}
    results: list[int] = []
    for i in range(6):
        resp = await client.post(
            "/api/v1/auth/register",
            json={**base, "email": f"u{i}@example.com", "display_name": f"U{i}"},
        )
        results.append(resp.status_code)

    assert 429 in results, f"Expected a 429 within the first 6 requests, got {results}"
