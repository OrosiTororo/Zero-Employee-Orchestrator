"""iPaaS integration — workflow orchestration with n8n / Zapier / Make.

Integrates with external iPaaS (Integration Platform as a Service) platforms,
handling workflow registration, execution, and status sync via webhook triggers.

Supported platforms:
- n8n: Self-hosted open-source automation
- Zapier: Cloud-based iPaaS (webhook trigger)
- Make (Integromat): Visual automation
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IPaaSProvider(str, Enum):
    """iPaaS provider."""

    N8N = "n8n"
    ZAPIER = "zapier"
    MAKE = "make"


class WorkflowStatus(str, Enum):
    """Workflow status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    RUNNING = "running"
    COMPLETED = "completed"


@dataclass
class WebhookTrigger:
    """Webhook trigger configuration."""

    url: str
    method: str = "POST"
    headers: dict[str, str] = field(default_factory=dict)
    payload_template: dict[str, Any] = field(default_factory=dict)


@dataclass
class IPaaSWorkflow:
    """iPaaS workflow definition."""

    id: str
    name: str
    provider: IPaaSProvider
    triggers: list[WebhookTrigger] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    description: str = ""
    created_at: str = ""
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    last_run_at: str = ""
    run_count: int = 0


@dataclass
class WorkflowRunResult:
    """Workflow run result."""

    workflow_id: str
    run_id: str
    success: bool
    status_code: int = 0
    response_body: Any = None
    error: str = ""
    triggered_at: str = ""
    latency_ms: int = 0


class IPaaSIntegration:
    """iPaaS workflow management service.

    Registers, triggers, and syncs workflow status through
    n8n / Zapier / Make webhooks.
    """

    def __init__(self) -> None:
        self._workflows: dict[str, IPaaSWorkflow] = {}
        self._run_history: list[WorkflowRunResult] = []

    def register_workflow(self, workflow: IPaaSWorkflow) -> str:
        """Register a workflow.

        Returns
        -------
        str
            Registered workflow ID
        """
        if not workflow.id:
            workflow.id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        workflow.created_at = workflow.created_at or now
        workflow.updated_at = now
        self._workflows[workflow.id] = workflow
        logger.info(
            "iPaaS workflow registered: %s (provider=%s)",
            workflow.name,
            workflow.provider.value,
        )
        return workflow.id

    async def trigger_workflow(
        self,
        workflow_id: str,
        payload: dict[str, Any] | None = None,
    ) -> WorkflowRunResult:
        """Trigger a workflow — send an HTTP request to the webhook."""
        workflow = self._workflows.get(workflow_id)
        if workflow is None:
            return WorkflowRunResult(
                workflow_id=workflow_id,
                run_id="",
                success=False,
                error=f"Workflow not found: {workflow_id}",
            )

        if workflow.status == WorkflowStatus.INACTIVE:
            return WorkflowRunResult(
                workflow_id=workflow_id,
                run_id="",
                success=False,
                error="Workflow is inactive",
            )

        if not workflow.triggers:
            return WorkflowRunResult(
                workflow_id=workflow_id,
                run_id="",
                success=False,
                error="No triggers configured for this workflow",
            )

        run_id = str(uuid.uuid4())
        trigger = workflow.triggers[0]  # Use primary trigger
        started_at = datetime.now(UTC)

        try:
            import httpx
        except ImportError:
            return WorkflowRunResult(
                workflow_id=workflow_id,
                run_id=run_id,
                success=False,
                error="httpx is required. Install with: pip install httpx",
            )

        # Build payload: merge with template if available
        body = {**trigger.payload_template}
        if payload:
            body.update(payload)
        body.setdefault("triggered_by", "zero-employee-orchestrator")
        body.setdefault("timestamp", started_at.isoformat())

        headers = {"Content-Type": "application/json", **trigger.headers}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if trigger.method.upper() == "GET":
                    resp = await client.get(trigger.url, headers=headers, params=payload)
                else:
                    resp = await client.post(trigger.url, headers=headers, json=body)

            finished_at = datetime.now(UTC)
            latency = int((finished_at - started_at).total_seconds() * 1000)

            try:
                resp_body = resp.json()
            except Exception:
                resp_body = resp.text

            result = WorkflowRunResult(
                workflow_id=workflow_id,
                run_id=run_id,
                success=resp.is_success,
                status_code=resp.status_code,
                response_body=resp_body,
                triggered_at=started_at.isoformat(),
                latency_ms=latency,
            )

            # Update workflow statistics
            workflow.last_run_at = started_at.isoformat()
            workflow.run_count += 1
            workflow.updated_at = finished_at.isoformat()

            logger.info(
                "iPaaS workflow triggered: %s (status=%d, latency=%dms)",
                workflow.name,
                resp.status_code,
                latency,
            )

        except Exception as exc:
            logger.error("iPaaS workflow trigger failed: %s — %s", workflow.name, exc)
            result = WorkflowRunResult(
                workflow_id=workflow_id,
                run_id=run_id,
                success=False,
                error=str(exc),
                triggered_at=started_at.isoformat(),
            )
            workflow.status = WorkflowStatus.ERROR

        self._run_history.append(result)
        return result

    def list_workflows(self, provider: IPaaSProvider | None = None) -> list[IPaaSWorkflow]:
        """Return a list of registered workflows."""
        workflows = list(self._workflows.values())
        if provider is not None:
            workflows = [w for w in workflows if w.provider == provider]
        return workflows

    async def sync_status(self, workflow_id: str) -> dict[str, Any]:
        """Synchronize workflow execution status.

        Updates status based on recent run results.
        If provider-specific APIs (e.g., n8n /executions) are available,
        those are prioritized.
        """
        workflow = self._workflows.get(workflow_id)
        if workflow is None:
            return {"error": f"Workflow not found: {workflow_id}"}

        # Estimate status from recent run results
        recent_runs = [r for r in self._run_history if r.workflow_id == workflow_id]
        if not recent_runs:
            return {
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "run_count": 0,
                "message": "No run history available",
            }

        last_run = recent_runs[-1]
        if last_run.success:
            workflow.status = WorkflowStatus.ACTIVE
        else:
            workflow.status = WorkflowStatus.ERROR

        return {
            "workflow_id": workflow_id,
            "status": workflow.status.value,
            "run_count": workflow.run_count,
            "last_run_id": last_run.run_id,
            "last_run_success": last_run.success,
            "last_run_at": last_run.triggered_at,
        }

    def remove_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if workflow_id in self._workflows:
            wf = self._workflows.pop(workflow_id)
            logger.info("iPaaS workflow removed: %s", wf.name)
            return True
        return False

    def create_n8n_webhook(
        self,
        url: str,
        event_types: list[str] | None = None,
        workflow_name: str = "",
    ) -> str:
        """Quick-register an n8n webhook workflow.

        Parameters
        ----------
        url: n8n Webhook URL (e.g., https://n8n.example.com/webhook/xxx)
        event_types: Event types to trigger
        workflow_name: Workflow name

        Returns
        -------
        str
            Registered workflow ID
        """
        trigger = WebhookTrigger(
            url=url,
            method="POST",
            headers={"Content-Type": "application/json"},
            payload_template={
                "source": "zero-employee-orchestrator",
                "event_types": event_types or ["*"],
            },
        )
        workflow = IPaaSWorkflow(
            id=str(uuid.uuid4()),
            name=workflow_name or f"n8n-webhook-{uuid.uuid4().hex[:8]}",
            provider=IPaaSProvider.N8N,
            triggers=[trigger],
            description=f"n8n Webhook: {url}",
        )
        return self.register_workflow(workflow)

    def create_zapier_webhook(
        self,
        url: str,
        event_types: list[str] | None = None,
        workflow_name: str = "",
    ) -> str:
        """Quick-register a Zapier Webhook (Catch Hook) workflow.

        Parameters
        ----------
        url: Zapier Webhook URL
        event_types: Event types to trigger
        workflow_name: Workflow name

        Returns
        -------
        str
            Registered workflow ID
        """
        trigger = WebhookTrigger(
            url=url,
            method="POST",
            headers={"Content-Type": "application/json"},
            payload_template={
                "source": "zero-employee-orchestrator",
                "event_types": event_types or ["*"],
            },
        )
        workflow = IPaaSWorkflow(
            id=str(uuid.uuid4()),
            name=workflow_name or f"zapier-hook-{uuid.uuid4().hex[:8]}",
            provider=IPaaSProvider.ZAPIER,
            triggers=[trigger],
            description=f"Zapier Catch Hook: {url}",
        )
        return self.register_workflow(workflow)

    def get_run_history(
        self,
        workflow_id: str | None = None,
        limit: int = 50,
    ) -> list[WorkflowRunResult]:
        """Get run history."""
        runs = self._run_history
        if workflow_id:
            runs = [r for r in runs if r.workflow_id == workflow_id]
        return runs[-limit:]


# Global instance
ipaas_service = IPaaSIntegration()
