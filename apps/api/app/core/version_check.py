"""PyPI バージョンチェック — 起動時に最新バージョンを通知する.

ネットワーク不通時やタイムアウト時はサイレントにスキップし、
ユーザー体験を妨げない。
"""

from __future__ import annotations

import importlib.metadata
import logging

logger = logging.getLogger(__name__)

PACKAGE_NAME = "zero-employee-orchestrator"

# ANSI colors
_YELLOW = "\033[38;5;220m"
_GREEN = "\033[38;5;78m"
_CYAN = "\033[38;5;51m"
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"


def get_current_version() -> str:
    """現在インストールされているバージョンを取得する."""
    try:
        return importlib.metadata.version(PACKAGE_NAME)
    except importlib.metadata.PackageNotFoundError:
        # 開発モード（editable install でない場合）はpyproject.tomlから取得
        return _read_version_from_pyproject()


def _read_version_from_pyproject() -> str:
    """pyproject.toml からバージョンを読み取る (フォールバック)."""
    import pathlib

    for candidate in [
        pathlib.Path(__file__).parents[3] / "pyproject.toml",  # apps/api/pyproject.toml
        pathlib.Path(__file__).parents[4] / "pyproject.toml",  # root pyproject.toml
    ]:
        if candidate.exists():
            for line in candidate.read_text().splitlines():
                if line.strip().startswith("version"):
                    # version = "0.1.0"
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "0.0.0"


def check_latest_version_sync(timeout: float = 3.0) -> str | None:
    """PyPI から最新バージョンを同期的に取得する.

    タイムアウトやエラー時は None を返す。
    """
    try:
        import httpx

        resp = httpx.get(
            f"https://pypi.org/pypi/{PACKAGE_NAME}/json",
            timeout=timeout,
            follow_redirects=True,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("info", {}).get("version")
    except Exception:
        # ネットワーク不通、タイムアウト等 — サイレントにスキップ
        logger.debug("PyPI version check failed (network unavailable or timeout)")
    return None


def is_newer_version(current: str, latest: str) -> bool:
    """latest が current より新しいかどうかを判定する."""
    try:
        from packaging.version import Version

        return Version(latest) > Version(current)
    except Exception:
        # packaging がない場合は単純な文字列比較
        return latest != current and latest > current


def print_update_notice(current: str, latest: str) -> None:
    """ターミナルにアップデート通知を表示する."""
    print()
    print(f"  {_YELLOW}╔══════════════════════════════════════════════╗{_RESET}")
    print(
        f"  {_YELLOW}║{_RESET}  {_BOLD}Update available!{_RESET}  "
        f"{_DIM}{current}{_RESET} → {_GREEN}{latest}{_RESET}            {_YELLOW}║{_RESET}"
    )
    print(f"  {_YELLOW}║{_RESET}                                              {_YELLOW}║{_RESET}")
    print(
        f"  {_YELLOW}║{_RESET}  Run: {_CYAN}zero-employee update{_RESET}"
        f"                   {_YELLOW}║{_RESET}"
    )
    print(
        f"  {_YELLOW}║{_RESET}   or: {_CYAN}pip install -U {PACKAGE_NAME}{_RESET}"
        f"  {_YELLOW}║{_RESET}"
    )
    print(f"  {_YELLOW}╚══════════════════════════════════════════════╝{_RESET}")
    print()


def check_and_notify(quiet: bool = False) -> None:
    """バージョンチェックを実行し、更新があれば通知する.

    quiet=True の場合、更新がなければ何も表示しない。
    """
    current = get_current_version()
    latest = check_latest_version_sync()

    if latest is None:
        if not quiet:
            print(f"  {_DIM}Version check: could not reach PyPI{_RESET}")
        return

    if is_newer_version(current, latest):
        print_update_notice(current, latest)
    elif not quiet:
        print(f"  {_GREEN}✔{_RESET} {_DIM}You are using the latest version ({current}){_RESET}")
