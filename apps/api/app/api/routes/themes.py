"""Theme API — CSS variable overrides for extensions.

Extensions can register custom themes by providing CSS variable overrides.
The frontend loads the active theme's overrides and applies them.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.routes.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory theme store — persisted per-session.
# Production: store in DB via Extension manifest_json.
_custom_themes: dict[str, dict[str, Any]] = {}
_active_theme: str = "dark"  # "dark" | "light" | "high-contrast" | custom slug


class ThemeInfo(BaseModel):
    slug: str
    name: str
    description: str = ""
    is_builtin: bool = False
    variables: dict[str, str] = {}


class ThemeSetRequest(BaseModel):
    slug: str


class CurrentThemeResponse(BaseModel):
    slug: str


class ThemeVariablesResponse(BaseModel):
    slug: str
    variables: dict[str, str] = {}


class ThemeSetResponse(BaseModel):
    slug: str
    applied: bool


BUILTIN_THEMES = [
    ThemeInfo(slug="dark", name="Dark Default", is_builtin=True),
    ThemeInfo(slug="light", name="Light Default", is_builtin=True),
    ThemeInfo(slug="high-contrast", name="High Contrast", is_builtin=True),
]


@router.get("/themes", response_model=list[ThemeInfo])
async def list_themes(_user: User = Depends(get_current_user)):
    """List all available themes (built-in + extension-provided)."""
    custom = [
        ThemeInfo(slug=slug, name=data.get("name", slug), variables=data.get("variables", {}))
        for slug, data in _custom_themes.items()
    ]
    return BUILTIN_THEMES + custom


@router.get("/themes/current", response_model=CurrentThemeResponse)
async def get_current_theme(_user: User = Depends(get_current_user)):
    """Get the currently active theme slug."""
    return {"slug": _active_theme}


@router.post("/themes/set", response_model=ThemeSetResponse)
async def set_theme(req: ThemeSetRequest, _user: User = Depends(get_current_user)):
    """Set the active theme by slug."""
    global _active_theme
    valid_slugs = {"dark", "light", "high-contrast"} | set(_custom_themes.keys())
    if req.slug not in valid_slugs:
        return ThemeSetResponse(slug=req.slug, applied=False)
    _active_theme = req.slug
    logger.info("Theme changed to: %s", req.slug)
    return ThemeSetResponse(slug=req.slug, applied=True)


@router.post("/themes/register", response_model=ThemeInfo)
async def register_theme(theme: ThemeInfo, _user: User = Depends(get_current_user)):
    """Register a custom theme from an extension.

    Extensions provide CSS variable overrides (e.g. {"--bg-base": "#000"}).
    The frontend applies these as inline CSS variables on the root element.
    """
    _custom_themes[theme.slug] = {
        "name": theme.name,
        "description": theme.description,
        "variables": theme.variables,
    }
    logger.info("Custom theme registered: %s (%d variables)", theme.slug, len(theme.variables))
    return theme


@router.get("/themes/{slug}/variables", response_model=ThemeVariablesResponse)
async def get_theme_variables(slug: str):
    """Get CSS variable overrides for a specific theme."""
    if slug in ("dark", "light", "high-contrast"):
        return {"slug": slug, "variables": {}}  # Built-in, no overrides needed
    if slug in _custom_themes:
        return {"slug": slug, "variables": _custom_themes[slug].get("variables", {})}
    return {"slug": slug, "variables": {}}
