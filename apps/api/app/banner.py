"""Zero-Employee Orchestrator — バナー表示.

CLI / TUI 起動時に表示するロゴ・バナー。
vibe-local のTUIデザインを参考に、モデル情報・エンジン状態・
モード表示をステータスラインとして表示する。

カラーテーマ: シアン〜ブルーのグラデーション
（vibe-local のマゼンタ系とは差別化）
"""

import os
import shutil

# ANSI カラーコード
_CYAN = "\033[38;5;51m"
_CYAN_DARK = "\033[38;5;38m"
_BLUE = "\033[38;5;33m"
_BLUE_LIGHT = "\033[38;5;75m"
_TEAL = "\033[38;5;43m"
_GREEN = "\033[38;5;78m"
_YELLOW = "\033[38;5;220m"
_WHITE = "\033[38;5;255m"
_GRAY = "\033[38;5;245m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

# ステータスラインのアイコン
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
    return f"  {_TEAL}{'─' * width}{_RESET}"


def print_banner(compact: bool = False) -> None:
    """ターミナルにカラーバナーを表示する."""
    from app.core.i18n import t

    art = BANNER_ASCII_COMPACT if compact else BANNER_ASCII
    lines = art.strip("\n").split("\n")
    colors = [
        _CYAN,
        _CYAN,
        _CYAN_DARK,
        _BLUE_LIGHT,
        _BLUE,
        _BLUE,
        _CYAN_DARK,
        _CYAN_DARK,
        _CYAN,
    ]

    print()
    for i, line in enumerate(lines):
        color = colors[i] if i < len(colors) else _BLUE
        print(f"  {color}{line}{_RESET}")
    print()
    print(f"  {_BOLD}{_WHITE}{t('banner_subtitle')}{_RESET}")
    print(f"  {_DIM}{t('banner_tagline')}{_RESET}")
    print()


def print_local_banner(
    model: str = "",
    engine_url: str = "http://localhost:11434",
    mode: str = "orchestrator",
    language: str = "ja",
    ollama_available: bool = False,
) -> None:
    """ローカルモード用の詳細バナーを表示する.

    vibe-local のステータス表示を参考にしつつ、
    Zero-Employee Orchestrator の業務遂行モードに適合させた表示。
    """
    from app.core.i18n import t

    lines = BANNER_ASCII_COMPACT.strip("\n").split("\n")
    colors = [_CYAN, _CYAN, _CYAN_DARK, _BLUE_LIGHT, _BLUE, _BLUE]

    print()
    for i, line in enumerate(lines):
        color = colors[i] if i < len(colors) else _BLUE
        print(f"  {color}{line}{_RESET}")

    print()
    print(f"  {_BOLD}{_CYAN}{t('banner_offline')}{_RESET}")
    print(f"  {_DIM}{t('banner_desc')}{_RESET}")

    print(_separator())

    # Status lines (vibe-local style)
    status_icon = f"{_GREEN}{_ICON_STATUS}{_RESET}" if ollama_available else f"{_YELLOW}✗{_RESET}"
    model_display = model or "(auto-detect)"
    mode_display = t(f"mode_{mode}") if f"mode_{mode}" in _mode_keys() else mode

    lang_names = {"ja": "日本語", "en": "English", "zh": "中文"}
    lang_display = lang_names.get(language, language)

    cwd = os.getcwd()
    # Truncate CWD if too long
    term_width = shutil.get_terminal_size((80, 24)).columns
    max_cwd = term_width - 30
    if len(cwd) > max_cwd:
        cwd = "..." + cwd[-(max_cwd - 3) :]

    print(
        f"  {_CYAN}{_ICON_MODEL}{_RESET} {_BOLD}{t('label_model')}{_RESET}    {_WHITE}{model_display}{_RESET}"
    )
    print(
        f"  {_BLUE}{_ICON_ENGINE}{_RESET}  {_BOLD}{t('label_engine')}{_RESET}  Ollama ({engine_url})"
    )
    print(
        f"  {_TEAL}{_ICON_MODE}{_RESET} {_BOLD}{t('label_mode')}{_RESET}    {_GREEN}{mode_display}{_RESET}"
    )
    print(
        f"  {_BLUE_LIGHT}{_ICON_LANG}{_RESET} {_BOLD}{t('label_language')}{_RESET}  {lang_display}"
    )
    print(f"  {_GRAY}{_ICON_CWD}{_RESET} {_BOLD}{t('label_cwd')}{_RESET}  {_DIM}{cwd}{_RESET}")
    print(f"  {_GRAY}   {t('label_status')}{_RESET}  {status_icon} Ollama")

    print(_separator())
    print()
    print(f"  {t('chat_help_hint')}")
    print()
    print(f"  {_GREEN}{t('chat_first_time')}{_RESET}")
    print(f"  {_DIM}{t('chat_welcome')}{_RESET}")
    print()


def _mode_keys() -> set[str]:
    """Return known mode translation keys."""
    return {"mode_orchestrator", "mode_auto_approve", "mode_manual_approve"}
