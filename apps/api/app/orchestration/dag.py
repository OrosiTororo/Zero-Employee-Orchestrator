"""Task Orchestrator Layer (Layer 3) - DAG planning and Self-Healing.

Handles plan generation, task decomposition into DAGs, cost estimation,
and self-healing on failures.
"""

from dataclasses import dataclass, field
from enum import Enum


class TaskNodeStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class TaskNode:
    id: str
    title: str
    task_type: str = "execute"
    assignee_agent_id: str | None = None
    depends_on: list[str] = field(default_factory=list)
    status: TaskNodeStatus = TaskNodeStatus.PENDING
    requires_approval: bool = False
    estimated_cost_usd: float = 0.0
    estimated_minutes: int = 0
    verification_criteria: str | None = None


@dataclass
class ExecutionDAG:
    plan_id: str
    nodes: list[TaskNode] = field(default_factory=list)
    _node_map: dict[str, TaskNode] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._node_map = {n.id: n for n in self.nodes}

    def add_node(self, node: TaskNode) -> None:
        self.nodes.append(node)
        self._node_map[node.id] = node

    def get_ready_nodes(self) -> list[TaskNode]:
        """Return nodes whose dependencies are all satisfied."""
        ready = []
        for node in self.nodes:
            if node.status != TaskNodeStatus.PENDING:
                continue
            deps_satisfied = all(
                self._node_map.get(dep_id, TaskNode(id="")).status == TaskNodeStatus.SUCCEEDED
                for dep_id in node.depends_on
            )
            if deps_satisfied:
                ready.append(node)
        return ready

    def mark_completed(self, node_id: str, success: bool = True) -> list[TaskNode]:
        """Mark a node as completed and return newly ready nodes."""
        node = self._node_map.get(node_id)
        if node:
            node.status = TaskNodeStatus.SUCCEEDED if success else TaskNodeStatus.FAILED
        return self.get_ready_nodes()

    def get_total_estimated_cost(self) -> float:
        return sum(n.estimated_cost_usd for n in self.nodes)

    def get_total_estimated_minutes(self) -> int:
        return sum(n.estimated_minutes for n in self.nodes)

    def get_critical_path_minutes(self) -> int:
        """Estimate critical path duration (simplified)."""
        if not self.nodes:
            return 0
        # Simple topological sort-based critical path
        longest = {}
        for node in self.nodes:
            dep_max = max(
                (longest.get(d, 0) for d in node.depends_on),
                default=0,
            )
            longest[node.id] = dep_max + node.estimated_minutes
        return max(longest.values()) if longest else 0

    def get_approval_points(self) -> list[TaskNode]:
        """Return nodes that require human approval before execution."""
        return [n for n in self.nodes if n.requires_approval]

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "total_cost_usd": self.get_total_estimated_cost(),
            "total_minutes": self.get_total_estimated_minutes(),
            "critical_path_minutes": self.get_critical_path_minutes(),
            "approval_points": len(self.get_approval_points()),
            "nodes": [
                {
                    "id": n.id,
                    "title": n.title,
                    "task_type": n.task_type,
                    "depends_on": n.depends_on,
                    "status": n.status.value,
                    "requires_approval": n.requires_approval,
                    "estimated_cost_usd": n.estimated_cost_usd,
                    "estimated_minutes": n.estimated_minutes,
                }
                for n in self.nodes
            ],
        }


def rebuild_dag_after_failure(
    dag: ExecutionDAG,
    failed_node_id: str,
    strategy: str = "retry",
) -> ExecutionDAG:
    """Self-Healing DAG: rebuild or patch the DAG after a failure.

    Strategies:
    - retry: Reset the failed node to pending
    - skip: Mark failed node as skipped, unblock dependents
    - replace: Create alternative path (requires external logic)
    - replan: Signal that full replanning is needed
    """
    node = dag._node_map.get(failed_node_id)
    if not node:
        return dag

    if strategy == "retry":
        node.status = TaskNodeStatus.PENDING
    elif strategy == "skip":
        node.status = TaskNodeStatus.SKIPPED
        # Mark as succeeded for dependency resolution
        for n in dag.nodes:
            if failed_node_id in n.depends_on:
                n.depends_on.remove(failed_node_id)
    elif strategy == "replan":
        # Signal that the entire plan needs rebuilding
        for n in dag.nodes:
            if n.status == TaskNodeStatus.PENDING:
                n.status = TaskNodeStatus.BLOCKED

    return dag
