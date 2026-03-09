"""Zero-Employee Orchestrator — バナー表示.

CLI / TUI 起動時に表示するロゴ・バナー。
"""

# ANSI カラーコード
_PURPLE = "\033[38;5;99m"
_INDIGO = "\033[38;5;105m"
_VIOLET = "\033[38;5;141m"
_LAVENDER = "\033[38;5;183m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

BANNER_ASCII = r"""
    ███████╗███████╗ ██████╗
    ╚══███╔╝██╔════╝██╔═══██╗
      ███╔╝ █████╗  ██║   ██║
     ███╔╝  ██╔══╝  ██║   ██║
    ███████╗███████╗╚██████╔╝
    ╚══════╝╚══════╝ ╚═════╝
"""

BANNER_SUBTITLE = "Zero-Employee Orchestrator"
BANNER_TAGLINE = "AI Orchestration Platform"


def print_banner() -> None:
    """ターミナルにカラーバナーを表示する."""
    lines = BANNER_ASCII.strip("\n").split("\n")
    colors = [_PURPLE, _PURPLE, _INDIGO, _INDIGO, _VIOLET, _VIOLET]

    print()
    for i, line in enumerate(lines):
        color = colors[i] if i < len(colors) else _VIOLET
        print(f"  {color}{line}{_RESET}")
    print()
    print(f"  {_BOLD}{_LAVENDER}{BANNER_SUBTITLE}{_RESET}")
    print(f"  {_DIM}{BANNER_TAGLINE}{_RESET}")
    print()
