"""Zero-Employee Orchestrator API package."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("zero-employee-orchestrator")
except PackageNotFoundError:
    __version__ = "0.1.7"

__all__ = ["__version__"]
