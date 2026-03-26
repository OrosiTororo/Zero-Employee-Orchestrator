"""PyPI version check -- Notify of the latest version at startup.

Silently skips on network failures or timeouts so as not to
disrupt the user experience.
"""

from __future__ import annotations

import importlib.metadata
import logging

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[assignment]

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
    """Get the currently installed version."""
    try:
        return importlib.metadata.version(PACKAGE_NAME)
    except importlib.metadata.PackageNotFoundError:
        # Development mode (when not an editable install) falls back to pyproject.toml
        return _read_version_from_pyproject()


def _read_version_from_pyproject() -> str:
    """Read version from pyproject.toml (fallback)."""
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
    """Synchronously fetch the latest version from PyPI.

    Returns None on timeout or error.
    """
    if httpx is None:
        return None
    try:
        resp = httpx.get(
            f"https://pypi.org/pypi/{PACKAGE_NAME}/json",
            timeout=timeout,
            follow_redirects=True,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("info", {}).get("version")
    except Exception:
        # Network unavailable, timeout, etc. -- silently skip
        logger.debug("PyPI version check failed (network unavailable or timeout)")
    return None


def is_newer_version(current: str, latest: str) -> bool:
    """Determine whether latest is newer than current."""
    try:
        from packaging.version import Version

        return Version(latest) > Version(current)
    except Exception:
        # Fall back to simple string comparison if packaging is unavailable
        return latest != current and latest > current


def print_update_notice(current: str, latest: str) -> None:
    """Display an update notice in the terminal."""
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
    """Run the version check and notify if an update is available.

    If quiet=True, nothing is displayed when already up to date.
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
