> [日本語](../FEATURES.md) | English | [中文](../zh/FEATURES.md)

# Zero-Employee Orchestrator — Feature List

> Last updated: 2026-03-10
> Target version: v0.1

---

## Overview

Zero-Employee Orchestrator is an **AI orchestration platform** that enables you to define business operations in natural language, assign roles to multiple AI agents, and execute, re-plan, and improve operations with human approval and auditability as prerequisites.

This document provides a comprehensive summary of currently implemented features and capabilities.

---

## Table of Contents

1. [9-Layer Architecture](#1-9-layer-architecture)
2. [Natural Language Input and Design Interview](#2-natural-language-input-and-design-interview)
3. [Spec / Plan / Tasks — Structured Intermediate Artifacts](#3-spec--plan--tasks--structured-intermediate-artifacts)
4. [DAG-Based Task Orchestrator](#4-dag-based-task-orchestrator)
5. [Strict Lifecycle Management via State Machines](#5-strict-lifecycle-management-via-state-machines)
6. [Judge Layer — Quality Assurance and Verification](#6-judge-layer--quality-assurance-and-verification)
7. [Cost Guard — Cost Estimation and Budget Control](#7-cost-guard--cost-estimation-and-budget-control)
8. [Quality SLA — Quality Modes and Model Selection](#8-quality-sla--quality-modes-and-model-selection)
9. [Self-Healing / Re-Propose — Automatic Recovery and Re-Planning on Failure](#9-self-healing--re-propose--automatic-recovery-and-re-planning-on-failure)
10. [Failure Taxonomy — Failure Classification and Learning](#10-failure-taxonomy--failure-classification-and-learning)
11. [Experience Memory — Accumulation and Reuse of Experiential Knowledge](#11-experience-memory--accumulation-and-reuse-of-experiential-knowledge)
12. [Approval Flow](#12-approval-flow)
13. [Audit Log](#13-audit-log)
14. [Agent Management](#14-agent-management)
15. [Skill / Plugin / Extension — 3-Tier Extension System](#15-skill--plugin--extension--3-tier-extension-system)
16. [LLM Gateway — Multi-Provider Support](#16-llm-gateway--multi-provider-support)
17. [Background Worker](#17-background-worker)
18. [Heartbeat — Scheduled Execution and Health Monitoring](#18-heartbeat--scheduled-execution-and-health-monitoring)
19. [Organization Management (Company / Department / Team)](#19-organization-management-company--department--team)
20. [Permission Model](#20-permission-model)
21. [Frontend UI](#21-frontend-ui)
22. [REST API](#22-rest-api)
23. [WebSocket Real-Time Communication](#23-websocket-real-time-communication)
24. [Observability — Reasoning Traces, Communication Logs, Execution Monitoring](#24-observability--reasoning-traces-communication-logs-execution-monitoring)
25. [Cloudflare Workers Deployment](#25-cloudflare-workers-deployment)
26. [Desktop Application (Tauri)](#26-desktop-application-tauri)
27. [CLI / TUI](#27-cli--tui)

---

## 1. 9-Layer Architecture

Zero-Employee Orchestrator is designed and implemented with the following 9-layer structure.

| Layer | Name | Role |
|-------|------|------|
| Layer 1 | **User Layer** | GUI / CLI / TUI / Chat input. Launch AI organization via natural language |
| Layer 2 | **Design Interview** | Generate questions to deeply explore requirements and accumulate answers. Structure the Spec |
| Layer 3 | **Task Orchestrator** | Plan/DAG generation, Skill assignment, cost estimation, re-planning |
| Layer 4 | **Skill Layer** | Single-purpose specialized Skill execution + Local Context Skill |
| Layer 5 | **Judge Layer** | Two-stage Detection + Cross-Model Verification |
| Layer 6 | **Re-Propose Layer** | Re-proposals on rejection + Dynamic DAG reconstruction |
| Layer 7 | **State & Memory** | State machine + Experience Memory + Failure Taxonomy |
| Layer 8 | **Provider Interface** | Multi-LLM connection via LiteLLM Gateway |
| Layer 9 | **Skill Registry** | Publishing, searching, and installing Skills / Plugins / Extensions |

---

## 2. Natural Language Input and Design Interview

### Natural Language Input

You can submit business requests in natural language from the dashboard.

```
Example: "Create a competitive analysis report and compile it into materials for next week's meeting"
```

The input is registered as a Ticket, and a Design Interview is automatically initiated.

### Design Interview

Requirements are explored structurally using 7 standard question templates.

| Category | Example Question |
|----------|-----------------|
| **Objective** | What is the ultimate goal of this task? |
| **Constraints** | Are there any constraints to follow? (budget, deadline, quality standards, etc.) |
| **Acceptance Criteria** | What are the completion conditions (acceptance criteria)? |
| **Risks** | Are there any anticipated risks or concerns? |
| **Priority** | What is the priority level? (High / Medium / Low) |
| **External Integration** | Is connection or transmission to external services required? |
| **Approval Steps** | Are there steps requiring human approval? |

Once answers are completed, a Spec (specification document) can be automatically generated from the Interview responses.

---

## 3. Spec / Plan / Tasks — Structured Intermediate Artifacts

All business requests are stored as structured intermediate artifacts rather than "conversation logs."

### Spec (Specification Document)

- **Objective** (`objective`): The ultimate goal of the task
- **Constraints** (`constraints_json`): Budget, deadline, quality standards
- **Acceptance Criteria** (`acceptance_criteria_json`): Criteria for judging completion
- **Risk Notes** (`risk_notes`): Anticipated risks
- **Version Control**: Records version on specification changes

### Plan (Execution Plan)

- Execution plan generated based on the Spec
- Includes cost estimates
- Includes approval flow (tasks are generated only after approval)

### Tasks (Individual Tasks)

- Individual execution units decomposed from the Plan
- Dependencies managed via DAG (Directed Acyclic Graph)
- Each task is assigned a responsible agent, estimated cost, and estimated time

---

## 4. DAG-Based Task Orchestrator

Task dependencies are managed via DAG (Directed Acyclic Graph), and optimal execution order is automatically determined.

### Key Features

| Feature | Description |
|---------|-------------|
| **Ready Node Detection** | Automatically marks tasks as executable when all dependency tasks are completed |
| **Critical Path Calculation** | Calculates the duration of the longest path and provides completion estimates |
| **Total Cost Estimation** | Aggregates the estimated cost across the entire DAG |
| **Approval Point Detection** | Identifies tasks that require human approval |
| **Self-Healing DAG** | Dynamically reconstructs the DAG on failure (retry / skip / replan) |

### Self-Healing Strategies

```
retry   -> Reset the failed node to pending and retry
skip    -> Skip the failed node and release dependency constraints on dependent nodes
replace -> Create an alternative path (requires external logic)
replan  -> Trigger a re-plan of the entire DAG
```

---

## 5. Strict Lifecycle Management via State Machines

4 types of state machines strictly manage the lifecycle of all resources.

### Ticket State Transitions

```
draft -> open -> interviewing -> planning -> ready -> in_progress -> review -> done -> closed
                                                          |              |         |
                                                       blocked        rework    reopened
```

### Task State Transitions

```
pending -> ready -> running -> succeeded -> verified -> archived
                      |            |
                 awaiting_approval failed -> retrying -> running
                      |
                   blocked
```

### Approval State Transitions

```
requested -> approved -> executed
          -> rejected -> superseded
          -> expired  -> requested (re-request)
          -> cancelled
```

### Agent State Transitions

```
provisioning -> idle -> busy -> idle
                 |      |
              paused   error -> idle / paused / decommissioned
                 |
          decommissioned
```

All state transitions are recorded as history, and invalid transitions are prevented as errors.

---

## 6. Judge Layer — Quality Assurance and Verification

A 3-stage quality verification mechanism is implemented.

### Stage 1: RuleBasedJudge (Rule-Based Primary Judgment)

- Dynamic addition of custom rules
- Fast primary filtering
- Severity-based scoring (error: -0.2 / warning: -0.05)

### Stage 2: PolicyPackJudge (Policy Compliance Check)

**Dangerous operation detection:**

| Detection Target |
|-----------------|
| `external_send` — External transmission |
| `publish` / `post` — Publishing / posting |
| `delete` — Deletion |
| `charge` — Billing |
| `git_push` / `git_release` — Git operations |
| `permission_change` — Permission changes |
| `credential_update` — Credential updates |

**Credential leak detection:**

- Detects patterns: `sk-`, `Bearer`, `api_key=`, `password=`, `secret=`, `token=`, `AKIA`

### Stage 3: CrossModelJudge (Cross-Model Verification)

- Compares outputs from multiple LLMs to verify reliability
- Scoring for structure consistency and value consistency
- Used in HIGH / CRITICAL quality modes

### Judgment Results

| Judgment | Meaning |
|----------|---------|
| `PASS` | Passed |
| `WARN` | Warning (can continue) |
| `FAIL` | Failed (execution stopped) |
| `NEEDS_REVIEW` | Human review required |

---

## 7. Cost Guard — Cost Estimation and Budget Control

### Cost Estimation

Token unit prices by model family are managed in `model_catalog.json`, and costs are estimated before execution.
Cost information is dynamically loaded from the model catalog, so no code changes are needed when models change.

| Model | Input ($/1K tokens) | Output ($/1K tokens) |
|-------|---------------------|----------------------|
| Claude Opus 4.6 | 0.015 | 0.075 |
| Claude Sonnet 4.6 | 0.003 | 0.015 |
| Claude Haiku 4.5 | 0.001 | 0.005 |
| GPT-5.4 | 0.005 | 0.015 |
| GPT-5 Mini | 0.00015 | 0.0006 |
| Gemini 2.5 Pro | 0.00125 | 0.005 |
| Gemini 2.5 Flash | 0.0001 | 0.0004 |
| Gemini 2.5 Flash Lite | 0.00005 | 0.0002 |
| DeepSeek Chat | 0.00014 | 0.00028 |
| Ollama (Local) | 0.0 | 0.0 |
| g4f (Free provider) | 0.0 | 0.0 |

> **Note**: The above are default values from `model_catalog.json`. They can be updated
> via the API (`POST /api/v1/models/update-cost`) or by directly editing the file
> to match provider pricing changes.

### Budget Check

| Judgment | Condition | Action |
|----------|-----------|--------|
| `ALLOW` | Usage < 80% | Execution permitted |
| `WARN` | 80% <= Usage < 100% | Permitted with warning |
| `BLOCK` | Usage >= 100% | Execution blocked |

### Budget Policy Management (UI)

- Daily / weekly / monthly budget cap settings
- Automatic task suspension on threshold breach
- Per-transaction tracking via cost ledger

---

## 8. Quality SLA — Quality Modes and Model Selection

4 quality modes are provided based on task importance.

| Mode | Recommended Models | Max Retries | Judge Threshold | Human Review | Cross-Model Verification |
|------|-------------------|-------------|-----------------|--------------|------------------------|
| **DRAFT** | GPT-5 Mini, Claude Haiku 4.5 | 1 | 50% | Not required | None |
| **STANDARD** | GPT-5.4, Claude Sonnet 4.6 | 2 | 70% | Not required | None |
| **HIGH** | GPT-5.4, Claude Sonnet 4.6 | 3 | 85% | Not required | **Enabled** |
| **CRITICAL** | Claude Opus 4.6, GPT-5.4 | 5 | 95% | **Required** | **Enabled** |

Model selection, retry strategy, and verification level are automatically adjusted based on the quality mode.
Recommended models are loaded from `model_catalog.json`, so only file editing is needed when updating models.

---

## 9. Self-Healing / Re-Propose — Automatic Recovery and Re-Planning on Failure

### Re-Propose

On failure or rejection, the cause is classified and alternative proposals are generated.

| Failure Category | Description |
|-----------------|-------------|
| `quality_insufficient` | Quality standards not met |
| `scope_mismatch` | Mismatch with requirements |
| `cost_exceeded` | Budget exceeded |
| `policy_violation` | Policy violation |
| `execution_error` | Runtime error |
| `timeout` | Timeout |
| `skill_gap` | Required Skill is missing |
| `dependency_broken` | Dependency chain broken |
| `model_incompatible` | Incompatibility due to model characteristics |

### Plan Diff

During re-proposals, a structured diff from the original plan (added, removed, and modified tasks, cost changes, and time changes) is presented.

---

## 10. Failure Taxonomy — Failure Classification and Learning

A failure classification system of 9 categories x 4 severity levels is implemented.

### Failure Categories

| Category | Description |
|----------|-------------|
| `LLM_ERROR` | LLM provider failure |
| `TOOL_ERROR` | Tool execution failure |
| `VALIDATION_ERROR` | Input/output validation failure |
| `BUDGET_ERROR` | Budget exceeded |
| `TIMEOUT_ERROR` | Timeout |
| `PERMISSION_ERROR` | Insufficient permissions |
| `DEPENDENCY_ERROR` | Dependency task failure |
| `HUMAN_REJECTION` | Rejection by human |
| `SYSTEM_ERROR` | Internal system error |

### Severity Levels

| Severity | Meaning | Response |
|----------|---------|----------|
| `LOW` | Minor | Recoverable via automatic retry |
| `MEDIUM` | Moderate | Recoverable via alternative means |
| `HIGH` | Serious | Human intervention required |
| `CRITICAL` | Fatal | Immediate escalation |

### Learning Features

- Tracks failure occurrence counts
- Automatically calculates recovery success rates
- Detects frequently occurring failure patterns
- Tracks effectiveness of preventive measures

---

## 11. Experience Memory — Accumulation and Reuse of Experiential Knowledge

Extracts and stores reusable knowledge from past execution history.

### Memory Types

| Type | Purpose |
|------|---------|
| `conversation_log` | Conversation log |
| `reusable_improvement` | Reusable improvement knowledge |
| `experimental_knowledge` | Experimental knowledge |
| `verified_knowledge` | Verified knowledge |

### Features

- Accumulation of success patterns (`add_success_pattern`)
- Learning from failure patterns (`add_failure`)
- Keyword/category search (`search`)
- Extraction of frequent failures (`get_frequent_failures`)

---

## 12. Approval Flow

Dangerous operations are not executed autonomously; human approval is always required.

### Operations Requiring Approval

| Operation | Example |
|-----------|---------|
| External transmission | Email sending, API calls |
| Publishing / posting | SNS posts, blog publishing |
| Deletion | Data deletion, file deletion |
| Billing | API usage charges |
| Permission changes | User permission changes |
| Git operations | push, release |
| Credential updates | API key changes |

### Approval UI

- List view of pending approvals
- Risk level display (Low / Medium / High / Critical)
- One-click approve/reject buttons
- Approval results are recorded in audit logs

---

## 13. Audit Log

All important operations are recorded in a traceable format.

### Recorded Information

| Field | Description |
|-------|-------------|
| `actor_type` | user / agent / system |
| `event_type` | Operation type (e.g., `task.started`, `approval.requested`) |
| `target_type` | Target resource type |
| `target_id` | Target resource ID |
| `details_json` | Additional details (JSON) |
| `trace_id` | Distributed tracing ID |

### Main Event Types

- `ticket.created` / `ticket.updated`
- `approval.requested` / `approval.granted` / `approval.rejected`
- `agent.assigned` / `agent.completed`
- `task.started` / `task.succeeded` / `task.failed`
- `cost.incurred`
- `auth.login` / `auth.logout`
- `dangerous_operation.*` (dangerous operations)
- `*.status_changed` (state transitions)

### Dedicated Helper Functions

- `record_audit_event` — General audit event recording
- `record_state_change` — State transition recording
- `record_dangerous_operation` — Dangerous operation recording

---

## 14. Agent Management

AI agents are managed as team members of the organization.

### Agent Attributes

| Attribute | Description |
|-----------|-------------|
| `agent_type` | Agent role type |
| `autonomy_level` | Autonomy level |
| `can_delegate` | Permission to delegate to other agents |
| `can_write_external` | Permission for external write operations |
| `can_spend_budget` | Permission to use budget |
| `budget_policy_id` | Associated budget policy |
| `heartbeat_policy_id` | Associated Heartbeat policy |

### Agent Operations

- Provisioning (new creation)
- Activation (enabling)
- Pause / Resume
- State transition validation

---

## 15. Skill / Plugin / Extension — 3-Tier Extension System

A 3-tier extension system that clearly separates the core from business logic is provided.

### Skill (Minimum Capability Unit)

The smallest unit that executes a single task. Includes prompts, procedures, scripts, and constraints.

```
Examples: Competitive analysis, script generation, file organization, local context comprehension
```

### Plugin (Business Function Package)

A business function package that bundles multiple Skills and auxiliary features.

| Plugin | Purpose | Status |
|--------|---------|--------|
| `ai-avatar` (AI Avatar) | Learns user's judgment criteria and writing style, acts as proxy | manifest available |
| `ai-secretary` (AI Secretary) | Briefing, priority suggestions, bridging with AI organization | manifest available |
| `discord-bot` | Multi-agent operation and interaction from Discord | manifest available (v0.2.0) |
| `slack-bot` | Multi-agent operation and interaction from Slack | manifest available (v0.2.0) |
| `line-bot` | Multi-agent operation from LINE | manifest available |
| `youtube` | YouTube channel management | manifest available |
| `research` | Competitive analysis, market research | manifest available |
| `backoffice` | Accounting, office administration, document management | manifest available |

### Extension (Environment Extension)

A mechanism to extend the core's runtime environment, UI, and connection targets.

| Extension | Purpose | Status |
|-----------|---------|--------|
| `oauth` | OAuth authentication for Google / GitHub, etc. | manifest available |
| `mcp` | Model Context Protocol compatible tool connections | manifest available |
| `notifications` | Slack / Discord / LINE / email notifications | manifest available |
| `obsidian` | Bidirectional integration with Obsidian Vault | manifest available |

### Registry Features

- Search for Skills / Plugins / Extensions
- Publish and install
- Status management (Verified / Experimental / Private / Deprecated)
- Version management

---

## 16. LLM Gateway — Multi-Provider Support

A unified LLM gateway based on LiteLLM supports multiple providers.

### Supported Providers

| Provider | Example Models |
|----------|---------------|
| **OpenRouter** | Access multiple models with a single API key (recommended) |
| **OpenAI** | GPT-5.4, GPT-5 Mini |
| **Anthropic** | Claude Opus 4.6, Sonnet 4.6, Haiku 4.5 |
| **Google** | Gemini 2.5 Pro, Flash, Flash Lite |
| **DeepSeek** | DeepSeek Chat |
| **Ollama** | Llama 3.2, Mistral, Phi-3, Qwen3, etc. (local, free) |
| **g4f** | Via free providers (no API key required) |

> **Supported models are managed in `model_catalog.json`.**
> Adding, removing, deprecating, and specifying successors for models can be done by editing
> this file or via the Model Registry API (`/api/v1/models/*`).

### Execution Modes

| Mode | Description | Recommended Models |
|------|-------------|-------------------|
| `QUALITY` | Highest quality | Claude Opus 4.6, GPT-5.4 |
| `SPEED` | Fast response | Claude Haiku 4.5, GPT-5 Mini |
| `COST` | Low cost | Claude Haiku 4.5, GPT-5 Mini, DeepSeek |
| `FREE` | Free (local + free APIs) | Ollama, Gemini free tier, g4f |
| `SUBSCRIPTION` | Free (no API key required) | Various models via g4f |

### Features

- **Dynamic Model Catalog** (`model_catalog.json`) — No code changes needed to add, deprecate, or update model costs
- **Automatic Fallback on Model Deprecation** — Automatic switch to successor model via deprecated flag + successor
- **Provider Health Check** — Periodically checks API availability and avoids unavailable models
- Automatic model selection (based on execution mode)
- Cost estimation (catalog-linked)
- Tool calling (Function Calling) support
- Vision (image input) support flag
- Fallback (mock responses when LiteLLM is not deployed)
- Ollama model auto-detection

---

## 17. Background Worker

A background task execution engine that runs as a separate process from the main API.

### Components

| Component | Role |
|-----------|------|
| **TaskRunner** | Polls and executes tasks in ready state |
| **HeartbeatRunner** | Periodic task execution based on scheduling policies |
| **EventDispatcher** | Real-time event delivery via WebSocket |

### TaskRunner Execution Pipeline

1. Retrieve tasks with `status='ready'` from DB
2. Select executor (LLM / Sandbox) based on `task_type`
3. Execute the task
4. Verify output quality with Judge
5. Success -> `succeeded` / Failure -> retry (up to 3 times)
6. Record audit log

### Executors

| Executor | Target Tasks |
|----------|-------------|
| **LLMExecutor** | Tasks using LLMs such as generation, analysis, and translation |
| **SandboxExecutor** | Safe execution of Python code (with memory, CPU, and time limits) |

### SandboxExecutor Limits

| Limit | Default Value |
|-------|--------------|
| Memory limit | 256 MB |
| CPU time limit | 30 seconds |
| Network access | Disabled |

---

## 18. Heartbeat — Scheduled Execution and Health Monitoring

### Heartbeat Policy

- Execution schedules defined via Cron expressions
- Jitter settings (variation in execution timing)
- Concurrent execution permission settings
- Enable / disable toggle

### Execution History

- Success / failure status for each execution
- Execution time recording
- Health indicator display on dashboard

---

## 19. Organization Management (Company / Department / Team)

### Organization Hierarchy

```
Company
├── Department
│   ├── Planning & Strategy
│   ├── Development
│   ├── Marketing
│   └── Customer Support
└── Team
    └── Dynamically organized per task
```

### Features

- Company creation and management
- Department and team creation
- Agent assignment to departments
- Organization chart (Org Chart) visualization
- Organization summary display on dashboard

---

## 20. Permission Model

Permissions are controlled through 5 roles.

| Role | Permissions |
|------|------------|
| **Owner** | Full permissions (including budget, approval, and publication settings) |
| **Admin** | Organization settings, some approvals, audit log viewing |
| **User** | Business requests, plan review, artifact review |
| **Auditor** | Execution history and audit log viewing only |
| **Developer** | Skill / Plugin / Extension development |

### Autonomous Execution Boundaries

| Autonomous Execution Allowed | Approval Required |
|-----------------------------|-------------------|
| Research / analysis | Publishing / posting |
| Draft creation | Billing / deletion |
| Information organization | Permission changes / external transmission |

---

## 21. Frontend UI

Over 20 screens built with React 19 + TypeScript + Tailwind CSS are provided.

### Main Screens

| Screen | Function |
|--------|----------|
| **Dashboard** | Statistics display, natural language input, quick navigation |
| **Login** | Email/password authentication |
| **Setup** | Initial onboarding |
| **Ticket List** | Ticket management with filtering |
| **Ticket Detail** | Individual ticket status and history |
| **Design Interview** | Structured interview UI |
| **Spec/Plan** | Specification and plan review/approval |
| **Approval Queue** | Approval management with risk levels |
| **Skill Management** | Skill browsing and creation |
| **Plugin Management** | Plugin browsing and installation |
| **Artifacts** | Management of generated outputs |
| **Audit Log** | Log viewer with advanced filtering |
| **Cost Management** | Budget policy and spending tracking |
| **Heartbeat** | Scheduled execution policy and history |
| **Org Chart** | Visualization of departments, teams, and agents |
| **Settings** | User settings and external connection management |
| **Releases** | Version history |
| **Downloads** | Desktop application downloads |

---

## 22. REST API

Over 40 endpoints are provided under the `/api/v1` prefix.

### Endpoint Groups

| Group | Endpoint Count | Main Operations |
|-------|---------------|-----------------|
| `/auth` | 6 | Registration, login, OAuth, logout, user info |
| `/companies` | 10+ | Company CRUD, dashboard, org chart, departments/teams |
| `/tickets` | 10+ | Ticket CRUD, state transitions, comments, threads |
| `/tickets/{id}/interview` | 3 | Interview retrieval, answers, auto Spec generation |
| `/tickets/{id}/specs` | 2 | Spec list and creation |
| `/tickets/{id}/plans` | 2 | Plan list and creation |
| `/plans/{id}` | 3 | Approval, rejection, task list |
| `/tasks` | 6 | Creation, start, completion, retry, approval request, execution history |
| `/agents` | 5 | List, creation, details, pause, resume |
| `/approvals` | 3 | List, approve, reject |
| `/artifacts` | 2 | List, creation |
| `/audit` | 1 | Log retrieval with filtering |
| `/heartbeats` | 3 | Policy CRUD, execution history |
| `/budgets` | 3 | Policy CRUD, cost summary |
| `/registry` | 6 | Skill / Plugin / Extension search and installation |
| `/projects` | 4 | Project CRUD, goal management |
| `/settings` | 6 | LLM API key settings, execution mode, company settings, tool connection management |
| `/health` | 2 | Health check (liveness / readiness) |
| `/models` | 7 | Model catalog management, health check, deprecation management |
| `/traces` | 4 | Reasoning trace list, details, decision extraction |
| `/communications` | 5 | Inter-agent communication, escalations, threads |
| `/monitor` | 4 | Execution monitoring dashboard, active tasks, events |

---

## 23. WebSocket Real-Time Communication

The `/ws/events` endpoint provides real-time event streaming.

- Task progress updates
- Approval request notifications
- Agent state changes
- Immediate error and failure notifications
- **Real-time delivery of reasoning traces** — Agent thought processes delivered step by step
- **Inter-agent communication delivery** — Real-time display of delegation, feedback, and escalation
- **Execution monitoring events** — Real-time display of task progress, model selection, and Judge verdicts

---

## 24. Observability — Reasoning Traces, Communication Logs, Execution Monitoring

A set of observability features to eliminate the black-box nature of multi-agent business operations.

### 24.1 Reasoning Trace

Records **why an agent made a particular decision** step by step.

| Step Type | Description |
|-----------|-------------|
| `context_gathering` | Context collection from information sources |
| `knowledge_retrieval` | Knowledge search from Experience Memory / RAG |
| `option_enumeration` | Enumeration of options |
| `option_evaluation` | Evaluation and scoring of each option |
| `decision` | Final decision-making (including selected option, reason, and confidence level) |
| `model_selection` | Reason for LLM model selection |
| `judge_result` | Judge Layer verdict result |
| `error_analysis` | Error cause analysis |
| `fallback_decision` | Fallback strategy selection |

Each step has a **confidence level** (high / medium / low / uncertain),
enabling quantitative assessment of decision reliability.

### 24.2 Agent Communication Log

Records **all message exchanges** during multi-agent collaboration.

| Message Type | Description |
|-------------|-------------|
| `delegation` / `delegation_accept` / `delegation_reject` | Task delegation |
| `artifact_handoff` | Artifact handover |
| `feedback` / `question` / `answer` | Communication |
| `quality_review` | Quality review results |
| `escalation` | Escalation (delegation to humans) |
| `error_report` / `help_request` | Anomaly reporting |

Conversations are grouped into **threads**, enabling conversation tracking per task.

### 24.3 Execution Monitor

Monitors **running tasks** in real time and delivers updates to the frontend via WebSocket.

- Progress rate, current step, token usage, and cost of running tasks
- Real-time delivery of each reasoning trace step
- Immediate notification of errors and escalations
- Activity summary per agent

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /traces` | Reasoning trace list (filterable by task/agent) |
| `GET /traces/{id}` | Reasoning trace details (including all steps) |
| `GET /traces/{id}/decisions` | Extract decision steps only |
| `GET /communications` | Inter-agent communication log |
| `GET /communications/escalations` | Escalation list |
| `GET /communications/agent/{id}/interactions` | Aggregation by communication partner |
| `GET /monitor/dashboard` | Monitoring dashboard (summary + active + events) |
| `GET /monitor/active` | List of running tasks |
| `GET /monitor/agent/{id}` | Agent activity |

---

## 25. Cloudflare Workers Deployment

In addition to local execution, edge deployment on Cloudflare Workers is supported.

### Method A: Proxy

- Reverse proxy placed in front of existing FastAPI
- Framework: Hono
- Requires an external server

### Method B: Full Workers

- Major APIs fully re-implemented with Hono + D1 (Cloudflare's SQLite)
- JWT authentication (jose)
- Fully serverless with no external server required
- Provides authentication, company management, tickets, agents, tasks, approvals, Spec/Plan, audit logs, budgets, projects, registry, artifacts, Heartbeat, reviews, and health checks

### Frontend Deployment

```bash
cd apps/desktop/ui && npm run build
npx wrangler pages deploy dist --project-name=zeo-ui
```

---

## 26. Desktop Application (Tauri)

A cross-platform desktop application based on Tauri v2 (Rust) is provided.

| OS | Format |
|----|--------|
| Windows | `.msi` / `.exe` |
| macOS | `.dmg` |
| Linux | `.AppImage` / `.deb` |

- Python backend bundled as a sidecar
- Local file access, session management, and UI run locally
- LLM APIs and external SaaS accessed via the cloud

---

## 27. CLI / TUI

A CLI tool installable via pip is provided.

```bash
pip install zero-employee-orchestrator
# or
uv pip install zero-employee-orchestrator
```

Entry point: `zero-employee` command

### CLI Command List

| Command | Description |
|---------|-------------|
| `zero-employee serve` | Start the API server |
| `zero-employee config list` | Display all configuration values |
| `zero-employee config set <KEY> [VALUE]` | Save a configuration value (prompt input if VALUE is omitted; sensitive values are not echoed) |
| `zero-employee config get <KEY>` | Retrieve a configuration value |
| `zero-employee config delete <KEY>` | Delete a configuration value (reset to default) |
| `zero-employee config keys` | List configurable keys |
| `zero-employee local` | Local chat mode (Ollama) |
| `zero-employee models` | List installed Ollama models |
| `zero-employee pull <model>` | Download an Ollama model |
| `zero-employee db upgrade` | Run DB migration |
| `zero-employee health` | Health check |

### Runtime Configuration Management

API keys and execution modes can be configured without directly editing the `.env` file.

**3 configuration methods:**
1. **Settings Screen**: Enter via "Settings" -> "LLM API Key Settings" in the app
2. **CLI**: `zero-employee config set GEMINI_API_KEY` (sensitive values entered securely via prompt)
3. **.env File**: Directly edit `apps/api/.env` as before

Configuration priority: Environment variables > `~/.zero-employee/config.json` > `.env` > Default values

---

## Database

### Main Tables (29+)

`companies`, `users`, `company_members`, `agents`, `tickets`, `ticket_threads`, `specs`, `plans`, `tasks`, `task_runs`, `task_dependencies`, `artifacts`, `reviews`, `approvals`, `budget_policies`, `cost_ledgers`, `heartbeat_policies`, `heartbeat_runs`, `skills`, `plugins`, `extensions`, `tool_connections`, `tool_call_traces`, `policy_packs`, `secret_refs`, `audit_logs`, `projects`, `goals`, `departments`, `teams`

### Supported Databases

| Environment | Database |
|-------------|----------|
| Development | SQLite (aiosqlite) |
| Production | PostgreSQL (asyncpg) recommended |
| Edge | Cloudflare D1 |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Desktop | Tauri v2 (Rust) |
| Frontend | React 19, TypeScript 5.9, Vite 7.3 |
| UI Library | Tailwind CSS 4.2, shadcn/ui, Recharts 3.7, Lucide Icons |
| State Management | TanStack Query 5.62, Zustand 5.0 |
| Routing | React Router 7.13 |
| Backend | Python 3.12+, FastAPI 0.115+ |
| ORM | SQLAlchemy 2.x (async) |
| Migration | Alembic |
| LLM Connection | LiteLLM 1.60+ |
| Authentication | OAuth PKCE, python-jose (JWT) |
| Validation | Pydantic 2.10+ |
| Scheduler | APScheduler 3.10+ |
| Logging | structlog 24.0+ |
| Edge | Cloudflare Workers, Hono 4.12, D1 |
| Package Management | uv (Python), pnpm (Node.js) |

---

## Additional Features (Provided via Plugin / Extension)

The following features are not included in the core and are added via Plugin / Extension.

### AI Avatar Plugin

An AI agent that acts as the user's "avatar." It learns the user's judgment criteria, writing style, and expertise as a profile.

| Feature | Description |
|---------|-------------|
| **Profile Learning** | Builds a profile by analyzing past approval/rejection patterns, comment history, and writing style |
| **Judge Layer Integration** | Provides user's judgment criteria as custom rules for the Judge Layer |
| **Proxy Review** | Task review and priority judgment when the user is absent (final approval authority always belongs to the user) |
| **Writing Style Reproduction** | Draft creation in the user's writing style and tone |
| **Approval Pattern Suggestions** | Suggests autonomous execution scope based on past approval patterns |

### AI Secretary Plugin

An AI agent that functions as a "hub" connecting the user with the AI organization.

| Feature | Description |
|---------|-------------|
| **Morning Briefing** | Summarizes pending approvals, in-progress tasks, and today's schedule |
| **Next Action Suggestions** | Assesses task urgency and importance to suggest recommended order |
| **Progress Summary** | Reports AI organization activity status to the user in an easy-to-understand format |
| **Reminders** | Notifications for tasks approaching deadlines and pending approvals |
| **Delegation Routing** | Routes user instructions to the appropriate agent |
| **Chat Integration** | Integrates with Discord / Slack / LINE Bot Plugin to deliver briefings |

### Chat Tool Integration (Discord / Slack / LINE Bot Plugin)

Send instructions to the AI organization from external chat tools and receive results.

| Command | Action |
|---------|--------|
| `/zeo ticket <description>` | Create a new ticket |
| `/zeo status [ticket_id]` | Check ticket/task status |
| `/zeo approve <approval_id>` | Approve operation |
| `/zeo reject <approval_id>` | Reject operation |
| `/zeo briefing` | Get current business summary |
| `/zeo ask <question>` | Ask the AI organization a question |

Approval dialogs are displayed in the chat tool for operations requiring approval. Can also be used as a delivery destination for periodic briefings in conjunction with the AI Secretary Plugin.

---

## 28. External Tool Integration (v0.1)

### CLI Tool Connection

`tools/connector.py` supports the following connection types:

| Connection Type | Description | Example |
|----------------|-------------|---------|
| `rest_api` | REST API calls | SaaS APIs, internal APIs |
| `webhook` | Webhook send/receive | Slack / Discord notifications |
| `mcp` | Model Context Protocol | Claude Desktop, VS Code integration |
| `oauth` | OAuth 2.0 authentication flow | Google / GitHub authentication |
| `websocket` | WebSocket bidirectional communication | Real-time data streams |
| `file_system` | File system connection | Local / NFS / S3 |
| `database` | Database connection | PostgreSQL, MySQL |
| `cli_tool` | CLI tool connection | gws, gh, aws CLI, etc. |
| `grpc` | gRPC service connection | Microservice communication |
| `graphql` | GraphQL API connection | GitHub GraphQL API, etc. |

### Supported CLI Tool Examples

| Tool | Description | Repository |
|------|-------------|------------|
| **gws** | Google Workspace CLI (Unified terminal operations for all Google Workspace APIs) | `googleworkspace/cli` |
| **gh** | GitHub CLI (Repository, Issue, PR operations) | `cli/cli` |
| **aws** | AWS CLI (All AWS service operations) | `aws/aws-cli` |
| **gcloud** | Google Cloud CLI (GCP service operations) | Google Cloud SDK |
| **az** | Azure CLI (Azure service operations) | `Azure/azure-cli` |

These CLI tools can be called from Skills by registering them with `ToolConnector`. It is also possible to provide CLI tool integration packages as Plugins.

---

## 29. Community Plugin Sharing (v0.1)

### Plugin Sharing and Publishing

Users can publish their custom plugins as GitHub repositories, allowing other users to easily install them. No action by developers to add them to the core is required.

### Plugin Sharing Mechanism

```
User A: Develops a plugin
  -> Pushes to a GitHub repository (topic: zeo-plugin)
  -> Includes a plugin.json manifest

User B: Searches for and installs the plugin
  -> POST /api/v1/registry/plugins/search-external?query=keyword
  -> POST /api/v1/registry/plugins/import?source_uri=https://github.com/user/plugin
  -> Plugin is automatically installed and available for use
```

### Plugin Manifest Format (`plugin.json`)

```json
{
  "name": "my-awesome-plugin",
  "slug": "my-awesome-plugin",
  "description": "Plugin description",
  "version": "0.1.0",
  "author": "Author name",
  "license": "MIT",
  "tags": ["productivity", "automation"],
  "skills": ["skill-a", "skill-b"],
  "config_schema": {}
}
```

### Community Plugin API

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/registry/plugins/search-external` | Search external plugins from GitHub, etc. |
| `POST /api/v1/registry/plugins/import` | Import and install plugins from GitHub repositories |
| `POST /api/v1/registry/plugins` | Create plugins locally |
| `POST /api/v1/registry/plugins/install` | Install plugins |

### Safety Checks

The following safety checks are performed when installing shared plugins:

- Detection of dangerous code patterns (16 types)
- Detection and warning of external communication
- Detection of credential access
- Detection of destructive operations
- Risk level assessment (low / medium / high)

---

## 30. v0.1 Feature Bloat Review — Boundary Between Core and Extensions

In v0.1, the following features are bundled in the codebase, but based on **core feature criteria** ("Would approval, auditing, and execution control fail without it?"), they are classified as **extension features**. They are planned to be separated as independent packages in future versions.

| Feature | Current Location | Classification | Status |
|---------|-----------------|----------------|--------|
| **Sentry Integration** | `integrations/sentry_integration.py` | Extension | Bundled in v0.1, to be separated |
| **AI Investigation Tool** | `integrations/ai_investigator.py` | Skill | Bundled in v0.1, to be separated |
| **Hypothesis Verification Engine** | `orchestration/hypothesis_engine.py` | Plugin | Bundled in v0.1, to be separated |
| **MCP Server** | `integrations/mcp_server.py` | Extension | Bundled in v0.1, to be separated |
| **External Skill Import** | `integrations/external_skills.py` | Extension | Bundled in v0.1, to be separated |

> **Note**: The above features are available in v0.1, but are planned to be separated as
> Extensions / Skills / Plugins in future versions to maintain core stability.
> See [FEATURE_BOUNDARY.md](../dev/FEATURE_BOUNDARY.md) for details.

---

## 31. Meta-Skill Concept (v0.1)

A design concept that gives AI agents the ability to "learn how to learn."

### 5 Elements of Meta-Skills

| Element | Implementation in AI Agent |
|---------|--------------------------|
| **Feeling** | Inference of user intent and emotion, context understanding |
| **Seeing** | Systems thinking, understanding business-wide dependencies |
| **Dreaming** | Creative alternative proposals, Re-Propose Layer |
| **Making** | Consistent execution from planning to implementation, DAG construction |
| **Learning** | Learning via Experience Memory and Failure Taxonomy |

Traditional AI agents possess hard skills (execution of specific tasks) and soft skills (communication), but lack meta-skills (the ability to manage and learn skills). Zero-Employee Orchestrator provides the foundation for meta-skills through Experience Memory and Failure Taxonomy.
