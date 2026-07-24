#!/usr/bin/env python3
"""Count the documented REST endpoints and route modules.

An endpoint is an ``@router.get``, ``post``, ``put``, ``patch``, or ``delete``
decorator in a direct ``apps/api/app/api/routes/*.py`` file. A route module is
one of those Python files excluding ``__init__.py``. WebSocket decorators and
routes outside that directory are intentionally excluded from both counts.
"""

from __future__ import annotations

import re
from pathlib import Path

ROUTES_DIR = Path(__file__).resolve().parents[1] / "apps" / "api" / "app" / "api" / "routes"
ENDPOINT_PATTERN = re.compile(r"@router\.(?:get|post|put|patch|delete)\(")


def count_endpoints(routes_dir: Path = ROUTES_DIR) -> tuple[int, int]:
    """Return the REST endpoint and route-module counts."""
    route_files = sorted(routes_dir.glob("*.py"))
    endpoint_count = sum(
        len(ENDPOINT_PATTERN.findall(path.read_text(encoding="utf-8"))) for path in route_files
    )
    module_count = sum(path.name != "__init__.py" for path in route_files)
    return endpoint_count, module_count


def main() -> None:
    """Print counts in the format used by repository documentation."""
    endpoint_count, module_count = count_endpoints()
    print(f"REST endpoints: {endpoint_count}")
    print(f"Route modules: {module_count}")


if __name__ == "__main__":
    main()
