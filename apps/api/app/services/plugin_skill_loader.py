"""Plugin-skill YAML loader.

Plugins declare a list of skill slugs in ``manifest.json``. v0.1.7 adds a
convention where each slug has a matching YAML under
``plugins/<plugin-slug>/skills/<skill-slug>.yaml`` that carries the prompt,
input/output schema, approval requirements, security-layer opt-ins, and
telemetry hooks.

This loader is read-only — it does not mutate any models. Services that
want to register a skill call :func:`load_plugin_skills` and hand the
returned dicts to the existing Skill / SkillRegistry code paths.

The loader is strict about a small set of required fields so manifests
cannot go out of sync with the plugin's stated skills list without
``/lint`` raising a flag.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


# apps/api/app/services/plugin_skill_loader.py → repo root
_REPO_ROOT = Path(__file__).resolve().parents[4]
_PLUGINS_ROOT = _REPO_ROOT / "plugins"


REQUIRED_FIELDS = ("slug", "name", "version", "description")
REQUIRED_SECURITY_FIELDS = ("wrap_external_data", "pii_guard", "sandbox")


class PluginSkillValidationError(ValueError):
    """Raised when a plugin skill YAML violates the manifest contract."""


def _validate_skill_dict(plugin_slug: str, skill: dict[str, Any]) -> None:
    """Raise :class:`PluginSkillValidationError` on missing required fields."""
    missing = [f for f in REQUIRED_FIELDS if f not in skill]
    if missing:
        raise PluginSkillValidationError(
            f"{plugin_slug}/{skill.get('slug', '<no-slug>')}: missing required fields {missing}"
        )
    if skill.get("plugin") and skill["plugin"] != plugin_slug:
        raise PluginSkillValidationError(
            f"{plugin_slug}/{skill['slug']}: 'plugin' field says "
            f"{skill['plugin']!r}, expected {plugin_slug!r}"
        )
    security = skill.get("security", {})
    if not isinstance(security, dict):
        raise PluginSkillValidationError(
            f"{plugin_slug}/{skill['slug']}: 'security' must be a mapping"
        )
    sec_missing = [f for f in REQUIRED_SECURITY_FIELDS if f not in security]
    if sec_missing:
        raise PluginSkillValidationError(
            f"{plugin_slug}/{skill['slug']}: security block missing {sec_missing}"
        )


def load_plugin_skills(plugin_slug: str) -> list[dict[str, Any]]:
    """Return every skill manifest declared under ``plugins/<slug>/skills/``.

    Missing or empty skills directory returns ``[]`` silently — an
    unconfigured plugin is not an error at boot time.

    Order is deterministic (sorted by filename) so installer tests can pin
    on the sequence.
    """
    skills_dir = _PLUGINS_ROOT / plugin_slug / "skills"
    if not skills_dir.is_dir():
        return []

    out: list[dict[str, Any]] = []
    for yaml_path in sorted(skills_dir.glob("*.yaml")):
        try:
            raw = yaml_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Could not read %s: %s", yaml_path, exc)
            continue
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            logger.error("Invalid YAML in %s: %s", yaml_path, exc)
            continue
        if not isinstance(data, dict):
            logger.error("%s: top-level must be a mapping, got %s", yaml_path, type(data))
            continue
        try:
            _validate_skill_dict(plugin_slug, data)
        except PluginSkillValidationError as exc:
            logger.error("Skill validation failed: %s", exc)
            continue
        out.append(data)
    return out


def load_plugin_manifest_skills(plugin_slug: str) -> tuple[list[str], list[str]]:
    """Return (declared_slugs, loaded_slugs) for a plugin.

    ``declared_slugs`` is read from ``manifest.json``. ``loaded_slugs`` is
    the set of slugs whose YAML files passed validation. The CLI / /lint
    surfaces the symmetric difference so plugin authors see drift early.
    """
    manifest_path = _PLUGINS_ROOT / plugin_slug / "manifest.json"
    declared: list[str] = []
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            declared = list(manifest.get("skills", []))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not parse manifest for %s: %s", plugin_slug, exc)

    loaded = [s["slug"] for s in load_plugin_skills(plugin_slug)]
    return declared, loaded


def list_plugin_skill_drift(plugin_slug: str) -> dict[str, list[str]]:
    """Report slugs that are in manifest but not in skills/ and vice versa."""
    declared, loaded = load_plugin_manifest_skills(plugin_slug)
    declared_set = set(declared)
    loaded_set = set(loaded)
    return {
        "declared_in_manifest": sorted(declared_set),
        "loaded_from_yaml": sorted(loaded_set),
        "missing_yaml": sorted(declared_set - loaded_set),
        "extra_yaml": sorted(loaded_set - declared_set),
    }


__all__ = [
    "PluginSkillValidationError",
    "list_plugin_skill_drift",
    "load_plugin_manifest_skills",
    "load_plugin_skills",
]
