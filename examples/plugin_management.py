"""Plugin management example — Search, install, and use plugins.

This example demonstrates the VS Code-style plugin management system,
including searching for plugins, checking environment requirements,
and installing them.

Prerequisites:
  - Server running: zero-employee serve
  - Authenticated session (API token)

Usage:
  python examples/plugin_management.py
"""

from __future__ import annotations

import httpx

BASE_URL = "http://localhost:18234/api/v1"


def main():
    with httpx.Client(base_url=BASE_URL, timeout=60) as client:
        # 1. List available plugins across all categories
        resp = client.get("/browser-automation/plugins/available")
        resp.raise_for_status()
        plugins = resp.json()
        print("Available plugins:")
        for plugin in plugins:
            print(f"  - {plugin['name']} ({plugin['category']}): {plugin['description']}")

        # 2. Search for a specific plugin by natural language
        resp = client.post(
            "/browser-automation/plugins/search",
            json={"query": "browser automation"},
        )
        resp.raise_for_status()
        results = resp.json()
        print(f"\nSearch results for 'browser automation': {len(results)} found")

        # 3. Check environment requirements before installing
        if results:
            slug = results[0]["slug"]
            resp = client.post(
                "/browser-automation/plugins/check-env",
                json={"slug": slug},
            )
            resp.raise_for_status()
            env_report = resp.json()
            print(f"\nEnvironment check for '{slug}':")
            print(f"  All requirements met: {env_report['all_satisfied']}")
            for check in env_report.get("checks", []):
                print(f"  - {check['name']}: {check['status']}")

        # 4. List available tool categories
        resp = client.get("/browser-automation/tools/categories")
        resp.raise_for_status()
        categories = resp.json()
        print(f"\nTool categories: {len(categories)} categories")
        for cat in categories:
            print(f"  - {cat['category']}: {cat.get('active_tool', 'none')}")

        # 5. Auto-resolve the best tool for a task
        resp = client.post(
            "/browser-automation/tools/resolve",
            json={"task_description": "Take a screenshot of a web page and extract data"},
        )
        resp.raise_for_status()
        resolved = resp.json()
        if resolved["resolved"]:
            print(f"\nResolved tool: {resolved['tool']}")
        else:
            print(f"\n{resolved['message']}")


if __name__ == "__main__":
    main()
