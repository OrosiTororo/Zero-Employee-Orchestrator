"""Basic workflow example — Create a ticket and monitor its execution.

This example demonstrates how to use the Zero-Employee Orchestrator API
to create a business task (ticket), monitor its progress, and retrieve results.

Prerequisites:
  - Server running: zero-employee serve
  - At least one LLM provider configured (or subscription mode enabled)

Usage:
  python examples/basic_workflow.py
"""

from __future__ import annotations

import httpx

BASE_URL = "http://localhost:18234/api/v1"


def main():
    with httpx.Client(base_url=BASE_URL, timeout=60) as client:
        # 1. Health check
        resp = client.get("/health")
        resp.raise_for_status()
        print(f"Server status: {resp.json()}")

        # 2. Check available models
        resp = client.get("/models")
        resp.raise_for_status()
        models = resp.json()
        print(f"Available models: {len(models.get('models', []))} models")

        # 3. Create a ticket (business task)
        ticket_data = {
            "title": "Competitive Analysis Report",
            "description": (
                "Research the top 3 competitors in the AI orchestration space "
                "and create a summary report with strengths, weaknesses, and "
                "market positioning."
            ),
            "priority": "medium",
        }
        resp = client.post("/tickets", json=ticket_data)
        resp.raise_for_status()
        ticket = resp.json()
        print(f"Created ticket: {ticket['id']} — {ticket['title']}")

        # 4. Check ticket status
        resp = client.get(f"/tickets/{ticket['id']}")
        resp.raise_for_status()
        status = resp.json()
        print(f"Ticket status: {status['status']}")

        # 5. List pending approvals (if any tasks require human approval)
        resp = client.get("/approvals/pending")
        resp.raise_for_status()
        approvals = resp.json()
        print(f"Pending approvals: {len(approvals.get('items', []))}")


if __name__ == "__main__":
    main()
