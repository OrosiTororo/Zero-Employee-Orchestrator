"""Tests for the externalised plugin_registry.json catalog."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.plugin_loader import _KNOWN_PLUGIN_TEMPLATES, _REGISTRY_PATH


def test_registry_file_exists_alongside_module():
    assert _REGISTRY_PATH.is_file(), f"plugin_registry.json not found at {_REGISTRY_PATH}"


def test_registry_file_is_valid_json():
    raw = _REGISTRY_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert isinstance(data, dict)
    assert len(data) > 0


def test_loaded_registry_matches_file_on_disk():
    with _REGISTRY_PATH.open(encoding="utf-8") as fh:
        on_disk = json.load(fh)
    assert on_disk == _KNOWN_PLUGIN_TEMPLATES


@pytest.mark.parametrize("slug", list(_KNOWN_PLUGIN_TEMPLATES.keys()))
def test_each_template_has_required_fields(slug: str):
    tpl = _KNOWN_PLUGIN_TEMPLATES[slug]
    for field in ("slug", "name", "description", "version", "category"):
        assert field in tpl, f"{slug} missing {field}"
    assert tpl["slug"] == slug, f"manifest slug '{tpl['slug']}' != key '{slug}'"


def test_registry_path_resolves_relative_to_module():
    # The path must be deterministic regardless of cwd — it's derived from
    # __file__ in plugin_loader.py, not an os.getcwd() lookup.
    assert isinstance(_REGISTRY_PATH, Path)
    assert _REGISTRY_PATH.name == "plugin_registry.json"
