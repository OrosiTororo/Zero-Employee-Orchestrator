"""Shared test fixtures."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure app package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use temp dir for all data during tests
_test_dir = tempfile.mkdtemp(prefix="zpcos_test_")
os.environ["APPDATA"] = _test_dir


@pytest.fixture
def tmp_dir():
    """Provide a temporary directory for tests."""
    d = tempfile.mkdtemp(prefix="zpcos_")
    yield Path(d)


@pytest.fixture
def sample_text():
    return "ZPCOSは複数のLLMを自動的に使い分けるシステムです。精度は99%以上です。"
