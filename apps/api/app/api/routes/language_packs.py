"""Language pack API endpoints.

Manages UI and AI agent output languages as lightweight extensions.
Built-in languages are bundled; additional languages can be added via extensions.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.i18n import get_language, set_language

logger = logging.getLogger(__name__)

router = APIRouter()

# Built-in languages bundled with the application
BUILTIN_LANGUAGES = {
    "en": {"name": "English", "native_name": "English", "direction": "ltr"},
    "ja": {"name": "Japanese", "native_name": "日本語", "direction": "ltr"},
    "zh": {"name": "Chinese", "native_name": "中文", "direction": "ltr"},
    "ko": {"name": "Korean", "native_name": "한국어", "direction": "ltr"},
    "pt": {"name": "Portuguese", "native_name": "Português", "direction": "ltr"},
    "tr": {"name": "Turkish", "native_name": "Türkçe", "direction": "ltr"},
}


class LanguageInfo(BaseModel):
    code: str
    name: str
    native_name: str
    direction: str = "ltr"
    is_builtin: bool = True
    is_active: bool = False


class LanguageSetRequest(BaseModel):
    language: str


class CurrentLanguageResponse(BaseModel):
    language: str
    name: str
    native_name: str


class LanguageSetResponse(BaseModel):
    language: str
    requires_restart: bool = False
    message: str = ""


@router.get("/language-packs", response_model=list[LanguageInfo])
async def list_language_packs():
    """List all available language packs (built-in and installed extensions)."""
    current = get_language()
    result = []
    for code, info in BUILTIN_LANGUAGES.items():
        result.append(
            LanguageInfo(
                code=code,
                name=info["name"],
                native_name=info["native_name"],
                direction=info["direction"],
                is_builtin=True,
                is_active=(code == current),
            )
        )
    return result


@router.get("/language-packs/current", response_model=CurrentLanguageResponse)
async def get_current_language():
    """Get the currently active language."""
    lang = get_language()
    info = BUILTIN_LANGUAGES.get(lang, {"name": lang, "native_name": lang, "direction": "ltr"})
    return {
        "language": lang,
        "name": info["name"],
        "native_name": info["native_name"],
    }


@router.post("/language-packs/set", response_model=LanguageSetResponse)
async def set_active_language(request: LanguageSetRequest):
    """Set the active language for UI and AI agent output.

    Some features may require restart to fully apply the language change.
    AI agent output language is updated immediately for new conversations.
    """
    code = request.language.lower().strip()

    if code not in BUILTIN_LANGUAGES:
        raise HTTPException(
            status_code=404,
            detail=f"Language '{code}' not available. Install a language pack extension first.",
        )

    set_language(code)
    info = BUILTIN_LANGUAGES[code]

    return LanguageSetResponse(
        language=code,
        requires_restart=True,
        message=f"Language set to {info['native_name']}. Some features may require restart.",
    )
