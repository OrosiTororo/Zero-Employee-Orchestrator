"""Skill Registry (community) テスト"""

import pytest
import tempfile
from pathlib import Path

from app.skills.registry import (
    search_registry,
    publish_skill,
    install_skill,
    get_popular,
)


@pytest.mark.asyncio
async def test_search_empty():
    results = await search_registry("nonexistent-skill")
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_get_popular():
    results = await get_popular()
    assert isinstance(results, list)
