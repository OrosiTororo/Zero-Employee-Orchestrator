"""End-to-end test: ticket creation → execution → result verification.

This test exercises the full orchestration pipeline:
  1. Create a company
  2. Create a ticket with a description
  3. Execute the ticket (generate plan → run DAG → Judge)
  4. Verify execution result with cost/token/quality metrics
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.orchestration.dag import ExecutionDAG, TaskNode
from app.orchestration.executor import TaskExecutor
from app.providers.gateway import CompletionResponse


@pytest.fixture
def mock_gateway():
    """Create a mock LLM Gateway that returns predictable responses."""
    gateway = AsyncMock()

    # Plan generation response: a simple 2-step plan
    plan_response = CompletionResponse(
        content='[{"id":"step_1","title":"Research","depends_on":[],'
        '"prompt":"Research the topic","estimated_minutes":5},'
        '{"id":"step_2","title":"Write report","depends_on":["step_1"],'
        '"prompt":"Write a summary report","estimated_minutes":10}]',
        model_used="test-model",
        tokens_input=100,
        tokens_output=200,
        cost_usd=0.001,
    )

    # Execution responses for each step
    exec_response = CompletionResponse(
        content="This is a well-researched analysis of the topic with detailed findings "
        "and actionable recommendations for the team.",
        model_used="test-model",
        tokens_input=150,
        tokens_output=300,
        cost_usd=0.002,
    )

    gateway.complete = AsyncMock(side_effect=[plan_response, exec_response, exec_response])
    return gateway


@pytest.mark.asyncio
async def test_e2e_ticket_create_execute(client: AsyncClient, mock_gateway):
    """Full e2e flow: create company → create ticket → execute → verify result."""

    # Step 1: Create a company
    company_data = {
        "name": "E2E Test Corp",
        "description": "Company for end-to-end testing",
    }
    resp = await client.post("/api/v1/companies", json=company_data)
    assert resp.status_code == 200, f"Company creation failed: {resp.text}"
    company = resp.json()
    company_id = company["id"]

    # Step 2: Create a ticket
    ticket_data = {
        "title": "Analyze competitor landscape",
        "description": "Research our top 3 competitors and produce a summary report "
        "with strengths, weaknesses, and market positioning.",
        "priority": "high",
    }
    resp = await client.post(f"/api/v1/companies/{company_id}/tickets", json=ticket_data)
    assert resp.status_code == 200, f"Ticket creation failed: {resp.text}"
    ticket = resp.json()
    ticket_id = ticket["id"]
    assert ticket["status"] == "open"

    # Step 3: Execute the ticket (with mocked LLM gateway)
    with patch("app.orchestration.executor.LLMGateway", return_value=mock_gateway):
        # Reset the executor singleton so it picks up our mock
        import app.orchestration.executor as executor_mod

        executor_mod._executor = None

        resp = await client.post(f"/api/v1/tickets/{ticket_id}/execute")
        assert resp.status_code == 200, f"Execution failed: {resp.text}"
        result = resp.json()

    # Step 4: Verify execution result
    assert result["status"] == "succeeded", f"Expected succeeded, got {result['status']}"
    assert result["plan_id"]  # Plan ID should be present
    assert result["total_cost_usd"] > 0  # Cost should be tracked
    assert result["total_tokens"] > 0  # Tokens should be tracked
    assert len(result["node_results"]) >= 1  # At least one node executed

    # Verify node results have quality metrics
    for nr in result["node_results"]:
        assert "node_id" in nr
        assert "judge_score" in nr
        assert "judge_verdict" in nr

    # Step 5: Verify ticket status was updated
    resp = await client.get(f"/api/v1/tickets/{ticket_id}")
    assert resp.status_code == 200
    updated_ticket = resp.json()
    assert updated_ticket["status"] == "resolved"


@pytest.mark.asyncio
async def test_executor_parallel_independent_nodes(mock_gateway):
    """Verify that independent DAG nodes are executed in parallel."""

    executor = TaskExecutor(gateway=mock_gateway)

    # Create a DAG with 2 independent nodes (no dependencies)
    dag = ExecutionDAG(plan_id="test-parallel")
    dag.add_node(TaskNode(id="a", title="Task A", provider_override={"prompt": "Do A"}))
    dag.add_node(TaskNode(id="b", title="Task B", provider_override={"prompt": "Do B"}))

    # Reset mock to return fresh responses
    exec_resp = CompletionResponse(
        content="Completed task with sufficient detail for quality checks to pass.",
        model_used="test-model",
        tokens_input=50,
        tokens_output=100,
        cost_usd=0.001,
    )
    mock_gateway.complete = AsyncMock(return_value=exec_resp)

    result = await executor.execute_plan(dag)

    assert result.status == "succeeded"
    assert len(result.node_results) == 2
    # Both nodes should have been called (parallel via asyncio.gather)
    assert mock_gateway.complete.call_count == 2


@pytest.mark.asyncio
async def test_executor_sequential_dependent_nodes(mock_gateway):
    """Verify that dependent DAG nodes run in correct order."""

    executor = TaskExecutor(gateway=mock_gateway)

    # Create a DAG with sequential dependency: A → B
    dag = ExecutionDAG(plan_id="test-sequential")
    dag.add_node(TaskNode(id="a", title="Task A", provider_override={"prompt": "Do A"}))
    dag.add_node(
        TaskNode(id="b", title="Task B", depends_on=["a"], provider_override={"prompt": "Do B"})
    )

    exec_resp = CompletionResponse(
        content="Completed task with sufficient detail for quality checks to pass.",
        model_used="test-model",
        tokens_input=50,
        tokens_output=100,
        cost_usd=0.001,
    )
    mock_gateway.complete = AsyncMock(return_value=exec_resp)

    result = await executor.execute_plan(dag)

    assert result.status == "succeeded"
    assert len(result.node_results) == 2
    # Node A should complete before Node B
    assert result.node_results[0].node_id == "a"
    assert result.node_results[1].node_id == "b"
