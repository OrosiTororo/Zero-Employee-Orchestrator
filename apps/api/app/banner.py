"""Zero-Employee Orchestrator -- Banner display.

Logo and banner displayed at CLI / TUI startup.
Uses MIT-licensed palette colors and Neovim-inspired status line layout.
"""

import os
import shutil

# ANSI color codes — ZEO palette (#007ACC accent, #D4D4D4 foreground)
_ACCENT = "\033[38;2;0;122;204m"  # #007ACC  accent
_ACCENT_DIM = "\033[38;2;0;90;160m"  # dimmed accent
_FG = "\033[38;2;212;212;212m"  # #D4D4D4  foreground
_FG_SEC = "\033[38;2;187;187;187m"  # #BBBBBB  secondary
_MUTED = "\033[38;2;110;118;129m"  # #6E7681  muted
_SUCCESS = "\033[38;2;86;186;159m"  # #56BA9F  Zed success
_WARNING = "\033[38;2;243;215;104m"  # #F3D768  Zed warning
_ERROR = "\033[38;2;229;72;77m"  # #E5484D  Zed error
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"

# Status line icons
_ICON_MODEL = "\u25cf"  # ● (filled circle)
_ICON_ENGINE = "\u2699"  # ⚙ (gear)
_ICON_MODE = "\u26a1"  # ⚡ (lightning)
_ICON_CWD = "\U0001f4c2"  # 📂 (folder)
_ICON_LANG = "\U0001f310"  # 🌐 (globe)
_ICON_STATUS = "\u2714"  # ✔ (checkmark)

BANNER_ASCII = r"""
  ╔═══════════════════════════════════════════════╗
  ║  ███████╗███████╗ ██████╗                     ║
  ║  ╚══███╔╝██╔════╝██╔═══██╗                    ║
  ║    ███╔╝ █████╗  ██║   ██║                    ║
  ║   ███╔╝  ██╔══╝  ██║   ██║                    ║
  ║  ███████╗███████╗╚██████╔╝                    ║
  ║  ╚══════╝╚══════╝ ╚═════╝                     ║
  ╚═══════════════════════════════════════════════╝
"""

BANNER_ASCII_COMPACT = r"""
    ███████╗███████╗ ██████╗
    ╚══███╔╝██╔════╝██╔═══██╗
      ███╔╝ █████╗  ██║   ██║
     ███╔╝  ██╔══╝  ██║   ██║
    ███████╗███████╗╚██████╔╝
    ╚══════╝╚══════╝ ╚═════╝
"""


def _separator(width: int = 50) -> str:
    return f"  {_MUTED}{'─' * width}{_RESET}"


def _status_line(
    mode: str = "NORMAL",
    provider: str = "",
    ctx_pct: int = 0,
    language: str = "ja",
    exec_mode: str = "quality",
    connected: bool = True,
) -> str:
    """Neovim lualine-inspired status line: A | B | C    X | Y | Z."""
    # Section colors (Neovim-inspired)
    mode_colors = {
        "NORMAL": _SUCCESS,
        "INSERT": _ACCENT,
        "COMMAND": _WARNING,
    }
    mode_color = mode_colors.get(mode, _FG)

    conn_icon = f"{_SUCCESS}●{_RESET}" if connected else f"{_ERROR}○{_RESET}"

    left = f"{mode_color}{_BOLD} {mode} {_RESET}{_MUTED}│{_RESET} {_FG_SEC}{provider}{_RESET} {_MUTED}│{_RESET} {_MUTED}ctx:{ctx_pct}%{_RESET}"
    right = f"{_MUTED}{language}{_RESET} {_MUTED}│{_RESET} {_MUTED}{exec_mode}{_RESET} {_MUTED}│{_RESET} {conn_icon}"

    term_width = shutil.get_terminal_size((80, 24)).columns
    # Calculate visible length (strip ANSI)
    import re

    ansi_re = re.compile(r"\033\[[0-9;]*m")
    left_len = len(ansi_re.sub("", left))
    right_len = len(ansi_re.sub("", right))
    padding = max(1, term_width - left_len - right_len - 4)

    return f"  {left}{' ' * padding}{right}"


def print_banner(compact: bool = False) -> None:
    """Display a colored banner in the terminal."""
    from app.core.i18n import t

    art = BANNER_ASCII_COMPACT if compact else BANNER_ASCII
    lines = art.strip("\n").split("\n")

    print()
    for line in lines:
        print(f"  {_ACCENT}{line}{_RESET}")
    print()
    print(f"  {_BOLD}{_FG}{t('banner_subtitle')}{_RESET}")
    print(f"  {_DIM}{t('banner_tagline')}{_RESET}")
    print()


def print_local_banner(
    model: str = "",
    engine_url: str = "http://localhost:11434",
    mode: str = "orchestrator",
    language: str = "ja",
    ollama_available: bool = False,
) -> None:
    """Display a detailed banner for local mode.

    Uses Neovim-inspired status layout with ZEO palette colors.
    """
    from app.core.i18n import t

    lines = BANNER_ASCII_COMPACT.strip("\n").split("\n")

    print()
    for line in lines:
        print(f"  {_ACCENT}{line}{_RESET}")

    print()
    print(f"  {_BOLD}{_ACCENT}{t('banner_offline')}{_RESET}")
    print(f"  {_DIM}{t('banner_desc')}{_RESET}")

    print(_separator())

    # Status lines — ZEO palette
    status_icon = (
        f"{_SUCCESS}{_ICON_STATUS}{_RESET}" if ollama_available else f"{_WARNING}✗{_RESET}"
    )
    model_display = model or "(auto-detect)"
    mode_display = t(f"mode_{mode}") if f"mode_{mode}" in _mode_keys() else mode

    lang_names = {"ja": "日本語", "en": "English", "zh": "中文"}
    lang_display = lang_names.get(language, language)

    cwd = os.getcwd()
    term_width = shutil.get_terminal_size((80, 24)).columns
    max_cwd = term_width - 30
    if len(cwd) > max_cwd:
        cwd = "..." + cwd[-(max_cwd - 3) :]

    print(
        f"  {_ACCENT}{_ICON_MODEL}{_RESET} {_BOLD}{t('label_model')}{_RESET}    {_FG}{model_display}{_RESET}"
    )
    print(
        f"  {_ACCENT_DIM}{_ICON_ENGINE}{_RESET}  {_BOLD}{t('label_engine')}{_RESET}  Ollama ({engine_url})"
    )
    print(
        f"  {_ACCENT}{_ICON_MODE}{_RESET} {_BOLD}{t('label_mode')}{_RESET}    {_SUCCESS}{mode_display}{_RESET}"
    )
    print(
        f"  {_ACCENT_DIM}{_ICON_LANG}{_RESET} {_BOLD}{t('label_language')}{_RESET}  {lang_display}"
    )
    print(f"  {_MUTED}{_ICON_CWD}{_RESET} {_BOLD}{t('label_cwd')}{_RESET}  {_DIM}{cwd}{_RESET}")
    print(f"  {_MUTED}   {t('label_status')}{_RESET}  {status_icon} Ollama")

    print(_separator())

    # Neovim-style status line
    print(
        _status_line(
            mode="NORMAL",
            provider="ollama" if ollama_available else "offline",
            ctx_pct=0,
            language=language,
            exec_mode="quality",
            connected=ollama_available,
        )
    )

    print(_separator())
    print()
    print(f"  {t('chat_help_hint')}")
    print()
    print(f"  {_SUCCESS}{t('chat_first_time')}{_RESET}")
    print(f"  {_DIM}{t('chat_welcome')}{_RESET}")
    print()


def _mode_keys() -> set[str]:
    """Return known mode translation keys."""
    return {"mode_orchestrator", "mode_auto_approve", "mode_manual_approve"}
