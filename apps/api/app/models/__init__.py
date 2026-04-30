"""Import all models so Alembic and Base.metadata can discover them.

In addition to the ORM classes under ``app/models/*.py``, a handful of
long-lived runtime tables are declared in service / orchestration modules
(knowledge store, experience memory, agent sessions, multi-model comparison
records, secretary summaries, …). They are imported here so that
``Base.metadata.create_all`` (used by ``zero-employee db upgrade``) and
Alembic autogenerate can see every table without loading the full FastAPI app.
"""

from app.models.agent import Agent
from app.models.artifact import Artifact
from app.models.audit import AuditLog
from app.models.autonomy_override import AutonomySessionOverride
from app.models.budget import BudgetPolicy, CostLedger
from app.models.company import Company
from app.models.connection import ToolCallTrace, ToolConnection
from app.models.heartbeat import HeartbeatPolicy, HeartbeatRun
from app.models.organization import Department, Team
from app.models.plan import Plan
from app.models.policy import PolicyPack, SecretRef
from app.models.project import Goal, Project
from app.models.review import ApprovalRequest, Review
from app.models.skill import Extension, Plugin, Skill
from app.models.spec import Spec
from app.models.task import Task, TaskRun
from app.models.ticket import Ticket, TicketThread
from app.models.user import CompanyMember, User

# Side-effect imports: register ORM tables declared outside app/models/.
# These modules attach classes to ``Base.metadata`` on import.
from app.orchestration import agent_session as _agent_session  # noqa: F401
from app.orchestration import experience_memory as _experience_memory  # noqa: F401
from app.orchestration import knowledge_store as _knowledge_store  # noqa: F401
from app.security import iam as _iam  # noqa: F401
from app.services import agent_org_service as _agent_org_service  # noqa: F401
from app.services import multi_model_service as _multi_model_service  # noqa: F401
from app.services import secretary_service as _secretary_service  # noqa: F401

__all__ = [
    "Agent",
    "ApprovalRequest",
    "Artifact",
    "AuditLog",
    "AutonomySessionOverride",
    "BudgetPolicy",
    "Company",
    "CompanyMember",
    "CostLedger",
    "Department",
    "Extension",
    "Goal",
    "HeartbeatPolicy",
    "HeartbeatRun",
    "Plan",
    "Plugin",
    "PolicyPack",
    "Project",
    "Review",
    "SecretRef",
    "Skill",
    "Spec",
    "Task",
    "TaskRun",
    "Team",
    "Ticket",
    "TicketThread",
    "ToolCallTrace",
    "ToolConnection",
    "User",
]
