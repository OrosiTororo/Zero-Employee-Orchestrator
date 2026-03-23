"""Tests for version_check module."""

from unittest.mock import MagicMock, patch

from app.core.version_check import (
    get_current_version,
    is_newer_version,
)


def test_get_current_version_returns_string():
    version = get_current_version()
    assert isinstance(version, str)
    assert len(version) > 0


def test_is_newer_version_true():
    assert is_newer_version("0.1.0", "0.2.0") is True
    assert is_newer_version("0.1.0", "1.0.0") is True


def test_is_newer_version_false():
    assert is_newer_version("0.2.0", "0.1.0") is False
    assert is_newer_version("0.1.0", "0.1.0") is False


def test_check_latest_version_sync_network_failure():
    """ネットワーク不通時は None を返す."""
    with patch("app.core.version_check.httpx") as mock_httpx:
        mock_httpx.get.side_effect = Exception("network error")
        from app.core.version_check import check_latest_version_sync

        result = check_latest_version_sync(timeout=1.0)
        assert result is None


def test_check_latest_version_sync_success():
    """PyPI レスポンスからバージョンを取得する."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"info": {"version": "99.0.0"}}

    with patch("app.core.version_check.httpx") as mock_httpx:
        mock_httpx.get.return_value = mock_resp
        from app.core.version_check import check_latest_version_sync

        result = check_latest_version_sync()
        assert result == "99.0.0"
