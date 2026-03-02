"""TokenStore テスト"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.auth.token_store import save_token, load_token, delete_token, has_token


@pytest.fixture(autouse=True)
def mock_keyring_and_paths(tmp_path):
    """keyring をモックしてファイルベースで動作。"""
    mock_keyring = {}

    def mock_get(service, username):
        return mock_keyring.get(f"{service}:{username}")

    def mock_set(service, username, password):
        mock_keyring[f"{service}:{username}"] = password

    def mock_delete(service, username):
        mock_keyring.pop(f"{service}:{username}", None)

    with patch("keyring.get_password", side_effect=mock_get), \
         patch("keyring.set_password", side_effect=mock_set), \
         patch("keyring.delete_password", side_effect=mock_delete), \
         patch("app.auth.token_store._tokens_dir", return_value=tmp_path):
        yield


@pytest.mark.asyncio
async def test_store_and_retrieve():
    await save_token("test_service", {"access_token": "abc123", "refresh_token": "xyz"})
    data = await load_token("test_service")
    assert data is not None
    assert data["access_token"] == "abc123"
    assert data["refresh_token"] == "xyz"


@pytest.mark.asyncio
async def test_load_nonexistent():
    data = await load_token("nonexistent")
    assert data is None


@pytest.mark.asyncio
async def test_delete():
    await save_token("delete_me", {"token": "value"})
    data = await load_token("delete_me")
    assert data is not None
    await delete_token("delete_me")
    data = await load_token("delete_me")
    assert data is None


@pytest.mark.asyncio
async def test_has_token():
    assert not await has_token("not_here")
    await save_token("here", {"token": "val"})
    assert await has_token("here")
