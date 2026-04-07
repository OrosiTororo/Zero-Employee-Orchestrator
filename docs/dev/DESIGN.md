# Zero-Employee Orchestrator Design Document

> Created: 2026-03-08
> Reference document: `docs/ja-JP/Zero-Employee Orchestrator.md`
> Role of this document: A design document that organizes the structure needed for implementation decisions to a granularity that AI coding agents can begin working with

---

## 0. Position of This Document

This document is the core design document for translating `docs/ja-JP/Zero-Employee Orchestrator.md` into implementation design.
The reference document retains the comprehensive coverage of philosophy, background, and improvement requests; this document clarifies:

1. What to include in the core system
2. What to extract as Skill / Plugin / Extension
3. How far to build for MVP
4. In what order to implement
5. What structures AI agents can directly translate into code

This document is not a README; it serves as the standard for implementation, review, task allocation, and rejection decisions.

---

## 1. System Definition

### 1.1 One-line Definition

Zero-Employee Orchestrator is the AI meta-orchestrator — a platform that unifies every AI framework, LLM provider, and business tool under a single approval gate, audit trail, and security layer. Define workflows in natural language, delegate across AI teams, and orchestrate orchestrators (CrewAI, AutoGen, LangChain, Dify, n8n, Zapier) as sub-workers.

### 1.2 Target State

- **Meta-orchestration**: Integrate and command other AI frameworks and automation platforms, not replace them
- **Tool-of-tools**: Connect to tools that connect to other tools (e.g., n8n → 400+ apps → ZEO controls all through one integration)
- Treat AI not as one-shot chat but as a team with defined roles
- Save spec / plan / tasks as intermediate artifacts
- Automate most execution while maintaining human final approval
- Handle local context, external APIs, credentials, and audit logs in a single platform
- Incorporate new models and business capabilities through extensions rather than core updates

### 1.3 User Segments

- Non-engineer practitioners and executives
- Engineers and R&D personnel
- Organizations requiring audit, approval, and permission management

---

## 2. Design Principles

1. **Treat AI as an organization**
   Use a team structure with role-based delegation for planning, execution, verification, and improvement rather than a single agent.

2. **Never remove human final approval**
   Ensure posting, sending, billing, deletion, and permission changes always have an approvable structure.

3. **Reduce black boxes**
   Visualize who did what, why, and with which model/Skill/permissions.

4. **Ensure currency through extensions**
   Core prioritizes stability; business differences are absorbed by Skill / Plugin / Extension.

5. **Treat local context as a key asset**
   Place the ability to safely handle local files, business data, and work history at the center of differentiation.

6. **Enable replanning, not just stopping, on failure**
   Design with Self-Healing, Re-Propose, and Plan Diff as prerequisites.

7. **Design as a general-purpose business platform**
   YouTube is one representative validation theme; the essence is an execution platform for overall company business.

---

## 3. Terminology

### 3.1 Skill

The minimum capability unit for executing a single task.
Includes prompts, procedures, scripts, constraints, and tools used.

Examples:
- Competitive analysis
- Script generation
- File organization
- Local context reading

### 3.2 Plugin

A business capability package bundling multiple Skills and auxiliary functions.
Distributed and installed as a cohesive set for enabling specific business operations.

Examples:
- Avatar AI Plugin (learns user's decision criteria and acts as proxy)
- Secretary AI Plugin (briefing, bridge between user and AI organization)
- Discord / Slack / LINE Bot Plugin (operations via chat)
- YouTube Operations Plugin
- Research Plugin

### 3.3 Extension

A mechanism for extending the core system's runtime environment, UI, connections, and developer experience.

Examples:
- MCP connection
- OAuth integration
- Notification features
- Cowork-style UI theme

### 3.4 Implementation Boundaries

- Core: Authentication, permissions, audit, execution control, state management, observability
- Skill / Plugin: Business-specific logic
- Extension: Connection, UI, and developer experience expansion

---

## 4. Architecture

Zero-Employee Orchestrator is based on a 9-layer structure.

1. **User Layer**
   GUI / CLI (with file/shell operations) / TUI / Chat input / Dashboard
   - CLI provides Claude Code-like interactive mode with file read/write/edit and shell execution
   - Both CLI and Desktop/Web offer equivalent operational capabilities
   - Language is configurable and affects both UI display and AI agent output

2. **Design Interview Layer**
   Purpose clarification, constraint organization, Spec creation

3. **Task Orchestrator Layer**
   Plan generation, DAG creation, approval waiting, cost estimation, replanning

4. **Skill Layer**
   Skill execution, Skill Gap detection, Skill generation, business-specific plugin execution

5. **Judge Layer**
   Two-stage Detection, Cross-Model Judge, Policy Pack.
   Tiered verification: LIGHTWEIGHT (rules only for reads) → STANDARD (+policy for writes) → HEAVY (+cross-model for send/delete/billing). Reduces API cost while maintaining safety for high-risk operations.

6. **Re-Propose Layer**
   Rejection, Plan Diff, partial re-execution, Self-Healing

7. **State & Memory Layer**
   State machine, history, artifacts, failure classification, experience knowledge storage.
   Memory trust levels: each ExperienceMemoryEntry tracks source_type, trust_level (0.0-1.0), verified status, and expiry. Only memories with trust ≥ 0.7 and not expired are used for decisions.

   **Operational Safety:**
   - Kill switch: Emergency halt of all executions via UI or API (`/kill-switch/activate`). Blocks new task starts until resumed.
   - Role-based tool permissions: 5 default policies (secretary, researcher, reviewer, executor, admin) enforce least privilege per agent role via `check_tool_permission()`.

8. **Provider Interface Layer**
   LiteLLM Gateway, model catalog, external APIs, OAuth, Webhook

9. **Registry Layer**
   Skill / Plugin / Extension publishing, search, installation, verification status display

---

## 5. Execution Flow

### 5.1 Basic Flow

1. User inputs objective in natural language
2. Design Interview supplements missing information
3. Generate Spec, finalize constraints and acceptance criteria
4. Generate Plan, present workflow, assigned AI, costs, and permissions
5. User approves or rejects
6. Only after approval, decompose into Tasks and execute
7. During execution, display progress, logs, artifacts, failures, and retry history
8. Judge inspects quality, evidence, and prohibited items
9. Re-Propose / Self-Healing as needed
10. After completion, save artifacts, decision rationale, and history

### 5.2 Intermediate Artifacts

All projects are stored in the following units as a rule.

```text
project/
├─ spec/
├─ plan/
├─ tasks/
├─ outputs/
├─ review/
└─ logs/
```

### 5.3 Event-Driven Execution

Supports Webhook, scheduled execution, and external event triggers.
However, trigger conditions, auto-execution scope, approval-required steps, and failure-stop conditions must be explicitly specified.

---

## 6. MVP Scope

### 6.1 MVP Purpose

Establish the core of Zero-Employee Orchestrator as a complete flow:

- Natural language input
- Design Interview
- spec / plan / tasks storage
- Execution with approval
- Judge
- Re-proposal
- Local context utilization
- Audit logs

### 6.2 MVP Required Features

- Authentication and local session management
- Design Interview
- Spec Writer
- Task Orchestrator
- Cost Guard
- Quality SLA
- Skill execution foundation
- Judge foundation
- Re-Propose / Plan Diff
- State Machine
- Experience Memory
- Failure Taxonomy
- Local Context Skill
- Basic dashboard
- Core APIs and audit logs

### 6.3 Items Excluded from MVP

- Full Marketplace features
- Large-scale Registry operations for external publishing
- Complex multi-tenant billing
- Complete advanced organizational governance
- Full robot integration or large-scale external operations

---

## 7. Permission Model

At minimum, the following roles exist:

- **Owner**: Full permissions, budget/approval/publishing settings
- **Admin**: Operations management, connection management, audit viewing
- **User**: Execution requests, artifact review, limited approvals
- **Auditor**: Primarily read-only, audit log and history viewing
- **Developer**: Skill / Plugin / Extension development and verification

Operations requiring approval are defined by combinations of role and operation type.

---

## 8. Data and Memory Policy

### 8.1 Items to Store

- Conversation and decision history
- spec / plan / tasks
- Artifact metadata
- Audit logs
- Failure classification and retry history
- Improvement knowledge and success factors
- Connection settings metadata

### 8.2 Items Under Strict Control

- Raw credentials
- Sensitive personal information
- Unnecessary full-text storage
- Internal documents not suitable for public sharing

### 8.3 Policy

- Sanitize before storage
- Separately store shareable improvement knowledge and confidential information
- Ensure traceability between execution rationale and artifacts

---

## 9. Execution Environment

### 9.1 Basic Policy

- Center on local applications
- Use cloud APIs as needed
- Base candidate is Tauri + frontend + local backend configuration

### 9.2 Role Distribution

**Local Side**
- File access
- Session and cache
- UI
- State management
- Partial execution control

**Cloud / External Side**
- LLM APIs
- External SaaS
- OAuth connection targets
- Notification, distribution, and posting targets

### 9.3 Initial Technology Stack

- Desktop: Tauri
- Frontend: React / Next.js family
- Backend: Python FastAPI
- Local DB: SQLite
- Queue / Worker: Start with lightweight Python-based implementation
- LLM Gateway: LiteLLM-compatible layer
- Authentication: OAuth + local session

### 9.4 Cloudflare Workers Deployment

In addition to local execution, supports execution on Cloudflare Workers.
Two deployment methods are provided:

| | Method A: Proxy | Method B: Full Workers |
|---|---|---|
| Directory | `apps/edge/proxy/` | `apps/edge/full/` |
| Overview | Reverse proxy in front of existing FastAPI | Full re-implementation of major APIs with Hono + D1 on edge |
| Database | Not needed (uses existing DB) | D1 (SQLite compatible) |
| Authentication | Delegated to backend | JWT (jose) |
| Framework | Hono | Hono + jose |
| External server | Required | Not required |

Method B (Full Workers) provides the following APIs on the edge:

- Authentication (register / login / me)
- Company management (CRUD / dashboard)
- Ticket management (list / create / detail)
- Agent management (list / create / pause / resume)
- Task management (create / start / complete)
- Approval management (list / approve / reject)
- Spec / Plan management (create / detail / approve)
- Audit logs (list / filter)
- Budget management (policy creation / cost list)
- Project management (CRUD)
- Registry (Skills / Plugins / Extensions search)
- Artifact management (list / create / detail)
- Heartbeat (policy creation / execution history)
- Review (create / list / detail)
- Health check

Frontend can be deployed to Cloudflare Pages.
Manual deployment via GitHub Actions (`.github/workflows/deploy-workers.yml`) is also supported.

---

## 10. Implementation Specifications for AI Agent Consumption

### 10.1 Initial DB Schema

Core tables start from the following:

- companies
- workspaces
- users
- roles
- agents
- teams
- skills
- plugins
- extensions
- projects
- tickets
- specs
- plans
- tasks (provider_override_json: JSON nullable -- per-task LLM provider specification)
- task_dependencies
- executions
- outputs
- reviews
- approvals
- budgets
- audit_logs
- provider_connections
- credentials_meta
- memories
- failure_records
- heartbeat_runs
- registry_packages
- registry_versions
- installs

### 10.2 Initial API Endpoint Groups

> **Note**: All endpoints use the `/api/v1/` prefix in the actual implementation (e.g., `POST /api/v1/auth/login`). The paths below show the design-level structure.

#### Authentication & Session
- `POST /api/auth/login`
- `GET /api/auth/status`
- `POST /api/auth/logout`
- `POST /api/auth/connect/{service}`
- `GET /api/auth/connections`
- `DELETE /api/auth/disconnect/{service}`

#### Organization & Company
- `GET /api/companies`
- `POST /api/companies`
- `GET /api/org-chart`
- `POST /api/teams`
- `POST /api/agents`

#### spec / plan / tasks
- `POST /api/interview/start`
- `POST /api/interview/respond`
- `POST /api/interview/finalize`
- `POST /api/specs`
- `POST /api/plans`
- `GET /api/plans/{id}`
- `POST /api/plans/{id}/approve`
- `POST /api/plans/{id}/repropose`
- `GET /api/plans/{id}/diff`
- `POST /api/tasks`
- `GET /api/tasks/{id}`
- `POST /api/tasks/{id}/transition`
- `PATCH /api/v1/tasks/{id}/provider` -- Update per-task provider specification

#### Execution & Review
- `POST /api/orchestrate`
- `GET /api/orchestrate/{id}`
- `GET /api/orchestrate/{id}/cost`
- `POST /api/orchestrate/{id}/self-heal`
- `GET /api/orchestrate/{id}/heal-history`
- `POST /api/reviews`
- `POST /api/approvals`

#### Skills / Plugins / Extensions (Implemented in v0.1)
- `GET /api/v1/registry/skills` -- Skill list (status, skill_type, include_disabled filters)
- `GET /api/v1/registry/skills/{id}` -- Individual Skill retrieval
- `POST /api/v1/registry/skills` -- Skill creation
- `POST /api/v1/registry/skills/install` -- Skill installation
- `PATCH /api/v1/registry/skills/{id}` -- Skill update (protected skill disable rejected)
- `DELETE /api/v1/registry/skills/{id}` -- Skill deletion (protected skill deletion rejected)
- `POST /api/v1/registry/skills/generate` -- Natural language skill generation (with safety check)
- `POST /api/skills/execute` -- Skill execution
- `GET /api/skills/gaps` -- Skill gap detection
- `GET /api/v1/registry/plugins` -- Plugin list
- `GET /api/v1/registry/plugins/{id}` -- Individual Plugin retrieval
- `POST /api/v1/registry/plugins` -- Plugin creation
- `PATCH /api/v1/registry/plugins/{id}` -- Plugin update
- `DELETE /api/v1/registry/plugins/{id}` -- Plugin deletion (protected plugin deletion rejected)
- `GET /api/v1/registry/extensions` -- Extension list
- `GET /api/v1/registry/extensions/{id}` -- Individual Extension retrieval
- `POST /api/v1/registry/extensions` -- Extension creation
- `PATCH /api/v1/registry/extensions/{id}` -- Extension update
- `DELETE /api/v1/registry/extensions/{id}` -- Extension deletion (protected extension deletion rejected)

#### Registry / Audit / Settings
- `GET /api/registry/search`
- `POST /api/registry/publish`
- `POST /api/registry/install`
- `GET /api/registry/popular`
- `GET /api/audit/logs`
- `GET /api/settings`
- `PUT /api/settings`
- `GET /api/health`

#### Media Generation & Provider Registry (Implemented in v0.1)
- `GET /api/v1/media/providers` -- Media generation provider list (built-in + user-registered)
- `GET /api/v1/media/providers/{media_type}` -- Providers by media type
- `POST /api/v1/media/providers` -- New provider registration (3D, etc.)
- `DELETE /api/v1/media/providers/{id}` -- User-registered provider deletion
- `POST /api/v1/media/generate` -- Media generation (arbitrary provider ID can be specified)

#### Runtime Configuration Management (Implemented in v0.1)
- `GET /api/v1/config` -- All configuration values (sensitive values masked)
- `GET /api/v1/config/providers` -- Provider connection status
- `PUT /api/v1/config` -- Update configuration values (API keys, execution mode, etc.)
- `PUT /api/v1/config/batch` -- Batch update
- `DELETE /api/v1/config/{key}` -- Delete configuration value (revert to default)
- `GET /api/v1/config/keys` -- List of configurable keys

### 10.3 State Transitions (Implemented)

#### Ticket
- draft -> open -> interviewing -> planning -> ready -> in_progress -> review -> done -> closed
- rework, blocked, cancelled can transition from each state
- reopened: can reopen from done / closed / cancelled

#### Task
- pending -> ready -> running -> succeeded -> verified -> archived
- running -> failed -> retrying -> running
- running -> awaiting_approval -> running
- running -> blocked -> ready
- rework_requested -> ready / running

#### Approval
- requested -> approved / rejected / expired / cancelled
- approved -> executed
- rejected -> superseded

#### Agent
- provisioning -> active -> busy -> paused -> archived
- active -> budget_blocked / policy_blocked / error
- error -> active / paused

### 10.4 Initial Screen List

- Sign In
- Workspace Selector
- Dashboard
- Interview / Spec Editor
- Plan Review / Diff
- Task Board / Execution Timeline
- Output / Review
- Skill / Plugin / Extension Manager
- Registry / Marketplace
- Audit Log Viewer
- Settings / Connections / Policies

### 10.5 Directory Structure (Implemented)

```text
Zero-Employee-Orchestrator/
├─ apps/
│  ├─ api/                    # FastAPI backend
│  │  ├─ app/
│  │  │  ├─ core/             # Config, DB, security
│  │  │  ├─ api/routes/       # REST API endpoints
│  │  │  ├─ api/ws/           # WebSocket
│  │  │  ├─ api/deps/         # Dependency injection
│  │  │  ├─ models/           # SQLAlchemy ORM models
│  │  │  ├─ schemas/          # Pydantic DTO
│  │  │  ├─ services/         # Business logic
│  │  │  ├─ repositories/     # DB I/O abstraction
│  │  │  ├─ orchestration/    # DAG, Judge, state machine, Knowledge, Memory
│  │  │  ├─ heartbeat/        # Heartbeat scheduler
│  │  │  ├─ providers/        # LLM gateway, Ollama, g4f, RAG
│  │  │  ├─ tools/            # External tool connectors (MCP/Webhook/API/CLI)
│  │  │  ├─ policies/         # Approval gates, autonomy boundaries
│  │  │  ├─ security/         # Secret management, sanitization, IAM
│  │  │  ├─ integrations/     # Sentry, MCP Server, external skills (extensions)
│  │  │  ├─ audit/            # Audit logging
│  │  │  └─ tests/            # Tests
│  │  └─ alembic/             # DB migrations
│  ├─ desktop/                # Tauri + React UI
│  │  ├─ src-tauri/           # Rust (Tauri v2)
│  │  └─ ui/src/
│  │     ├─ pages/            # 27 screen components
│  │     ├─ features/         # Feature-based modules
│  │     ├─ shared/           # Common API, types, hooks, UI
│  │     └─ app/              # Routing, entry point
│  ├─ edge/                   # Cloudflare Workers
│  └─ worker/                 # Background workers
│     ├─ runners/             # Task, Heartbeat execution
│     ├─ executors/           # LLM, sandbox execution
│     ├─ dispatchers/         # Event dispatch
│     └─ sandbox/             # Isolated execution environment
├─ skills/builtin/            # Built-in Skills
├─ plugins/                   # Plugin definitions
├─ extensions/                # Extension definitions
├─ packages/                  # Shared packages
├─ docs/                      # Documentation
├─ scripts/                   # Development and deployment scripts
└─ docker/                    # Docker configuration
```

---

## 11. Implementation Order

### Phase 0: Development Foundation
- Monorepo structure
- Python / Node / Tauri development foundation
- Lint / Format / Test / CI
- Environment variables and secret management

### Phase 1: Authentication and Company Scope
- Local authentication
- OAuth connection foundation
- workspace / company scope

### Phase 2: Design Interview and Spec
- Interview sessions
- Spec Writer
- Spec storage and editing

### Phase 3: Plan and Approval
- Plan generation
- Cost Guard
- Quality SLA
- Approval flow
- Plan Diff

### Phase 4: Task Execution Foundation
- Task decomposition
- State machine
- Execution history
- Progress visualization

### Phase 5: Judge and Replanning
- Two-stage Detection
- Cross-Model Judge
- Re-Propose
- Self-Healing
- Failure Taxonomy

### Phase 6: Skill / Local Context
- Skill execution foundation
- Skill Gap detection
- Local Context Skill
- Experience Memory

### Phase 7: UI Enhancement
- Dashboard
- Execution timeline
- Audit screen
- Registry UI

### Phase 8: Registry / Sharing
- Packaging
- Installation
- Version management
- Verification status display

### Phase 9: Advanced Features
- Heartbeat
- Goal Alignment
- Ticket / Org Chart-centered operations
- Multi-company support
- BYOA/BYOAgent-style connectivity enhancement

---

## 12. Test Strategy

### 12.1 Unit Tests
- Interview logic
- Spec Writer
- Cost Guard
- Policy Pack
- Failure Taxonomy
- Plan Diff
- Skill Gap detection

### 12.2 Integration Tests
- interview -> spec -> plan -> approval -> execute
- Skill execution -> Judge -> Re-Propose
- Local Context reading -> artifact generation

### 12.3 E2E Tests
- Natural language input from GUI through to final artifact approval
- Whether Self-Healing triggers on failure
- Whether audit logs are consistently saved

### 12.4 Security Tests
- Permission escalation
- Unauthorized connections
- Secret exposure
- Pre-detection of prohibited operations

### 12.5 LLM-Specific Tests
- Hallucination suppression
- Detection of weakly grounded responses
- Replanning quality on rejection
- Degradation detection on model changes

---

## 13. Critical Implementation Decisions

1. YouTube is a validation theme, not part of the core definition
2. The core is a business OS; individual business operations are expressed as Skill / Plugin
3. SQLite-centered approach is acceptable for MVP for rapid development
4. However, state machine, audit logs, and approval flows are included from the start
5. Autonomous execution boundaries are strict; dangerous operations require explicit approval
6. Implementation instruction groups from Sections 2-7 are maintained in a reusable state following this document's structure

---

## 14. Relationship Between This Document and Reference Documents

- `docs/ja-JP/Zero-Employee Orchestrator.md`: Reference for philosophy, requests, background, improvement proposals, and overall vision
- `docs/dev/DESIGN.md`: Reference for implementation design
- `docs/dev/MASTER_GUIDE.md`: Reference for execution order, reference relationships, and task allocation for AI agents

This document is not a summary of the reference document but a derived design document that codifies the structures needed for implementation.
