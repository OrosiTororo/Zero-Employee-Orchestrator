> English | [日本語](ja-JP/OVERVIEW.md) | [中文](zh/OVERVIEW.md)

# Zero-Employee Orchestrator — Comprehensive Guide

> A document explaining the philosophy, features, and structure of this project for first-time visitors.

---

## Table of Contents

1. [What Is This](#1-what-is-this)
2. [Why Is It Needed](#2-why-is-it-needed)
3. [Basic Usage](#3-basic-usage)
4. [9-Layer Architecture](#4-9-layer-architecture)
5. [Technology Stack](#5-technology-stack)
6. [Implementation Status](#6-implementation-status)
7. [Offline Operation](#7-offline-operation)
8. [Boundary Between Core and Extension Features](#8-boundary-between-core-and-extension-features)
9. [External Tool Integration](#9-external-tool-integration)
10. [Design Considerations and Future Direction](#10-design-considerations-and-future-direction)
11. [Document Index](#11-document-index)

---

## 1. What Is This

### In One Sentence

**An "AI business orchestration platform" where you simply describe your task in natural language, and multiple AIs form a team to plan, execute, verify, and improve the work.**

### In More Detail

Zero-Employee Orchestrator (ZEO) achieves the following in a single piece of software:

- Just tell it what you want to do in natural language, and the AI will dig deeper into the requirements
- The AI breaks down tasks and assigns roles to multiple AI agents
- Dangerous operations (posting, sending, deleting, billing) always require human approval
- All operations are recorded in audit logs
- Even when failures occur, the AI automatically re-plans (Self-Healing)
- It learns from experience, improving accuracy with each iteration

### How It Differs from Other AI Agents

| | AI Agents (AutoGPT, CrewAI, etc.) | RPA / n8n / Make | **ZEO** |
|---|---|---|---|
| Input Method | Text / Code | Flow design / Node placement | **Natural language** |
| AI Team | Limited | None / API calls | **Multiple AIs with assigned roles** |
| Quality Assurance | None or single model | Rules | **Judge Layer two-stage verification** |
| Failure Recovery | Stop or simple retry | Stop | **Self-Healing DAG automatic re-planning** |
| Approval Flow | None (fully automated) | Manual configuration | **Automatic detection & forced blocking of dangerous operations** |
| Experience Learning | None | None | **Accumulated via Experience Memory** |
| Extensibility | Code changes | Plugins (limited) | **3-tier: Skill / Plugin / Extension** |
| Audit Logs | None or limited | Limited | **Full operation recording & traceability** |

---

## 2. Why Is It Needed

Current AI tools have the following structural limitations:

1. **Starting from scratch every time** — Entering the same background information into ChatGPT repeatedly
2. **Manual handoffs** — Manually copying AI output and pasting it into the next step
3. **Unknown quality** — Having to verify AI responses yourself
4. **Invisible progress** — Not knowing how far along the task you asked the AI to do yesterday has progressed
5. **Fear of runaway behavior** — Anxiety about the AI accidentally sending wrong emails or deleting important data

ZEO solves these problems **at the architecture level**.

---

## 3. Basic Usage

### Getting Started

```bash
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh   # Automatic dependency installation
./start.sh   # Start backend + frontend
```

Open **http://localhost:5173** in your browser.

### Workflow

```
1. Enter your objective in natural language
   "Create a social media posting calendar for this month"

2. Design Interview (AI digs deeper into requirements)
   "Which social media platforms?" "Posting frequency?" "Target audience?"

3. Spec (what to achieve) is automatically generated

4. Plan (how to achieve it) is automatically generated
   Presents stages, assigned AIs, estimated costs, and required permissions

5. User reviews the plan, makes modifications, and approves

6. Tasks are broken down and executed in parallel
   Progress, artifacts, and failures are visible in real-time

7. Judge Layer performs quality verification
   Rule-based checks + cross-verification by a different model

8. After completion, review and approve artifacts
   An approval dialog appears for dangerous operations like posting or sending
```

### LLM Configuration

| Method | Cost | Configuration |
|--------|------|---------------|
| **Ollama (local)** | Free | `OLLAMA_BASE_URL=http://localhost:11434` |
| **Google Gemini free tier** | Free | `GEMINI_API_KEY=...` |
| **Subscription mode** | Free | `DEFAULT_EXECUTION_MODE=subscription` |
| **OpenRouter** | Pay-per-use | `OPENROUTER_API_KEY=...` |
| **OpenAI / Anthropic** | Pay-per-use | Set each API key |

API keys can be configured in 3 ways:
1. **Settings screen**: Enter via "Settings" -> "LLM API Key Configuration" in the app (recommended)
2. **CLI**: `zero-employee config set GEMINI_API_KEY`
3. **.env file**: Directly edit `apps/api/.env`

---

## 4. 9-Layer Architecture

ZEO is composed of 9 layers. Each layer has independent responsibilities.

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: User Layer                                  │
│   Natural language input → GUI / CLI / TUI / Discord / Slack │
├─────────────────────────────────────────────────────┤
│ Layer 2: Design Interview                            │
│   Requirement deep-dive → Question generation → Answer accumulation → Spec creation │
├─────────────────────────────────────────────────────┤
│ Layer 3: Task Orchestrator                           │
│   Plan generation → DAG creation → Skill assignment → Cost estimation │
│   Self-Healing DAG → Dynamic reconstruction          │
├─────────────────────────────────────────────────────┤
│ Layer 4: Skill Layer                                 │
│   Built-in Skills → Plugin Skills → Gap detection    │
│   Local Context Skill (safe local file reading)      │
├─────────────────────────────────────────────────────┤
│ Layer 5: Judge Layer                                 │
│   Stage 1: Rule-based fast checking                  │
│   Stage 2: Cross-Model Verification (different model verification) │
├─────────────────────────────────────────────────────┤
│ Layer 6: Re-Propose Layer                            │
│   Rejection → Plan Diff → Partial re-execution → Re-proposal │
├─────────────────────────────────────────────────────┤
│ Layer 7: State & Memory                              │
│   State machine → Experience Memory → Failure Taxonomy │
│   Artifact Bridge → Knowledge Refresh               │
├─────────────────────────────────────────────────────┤
│ Layer 8: Provider Interface                          │
│   LiteLLM Gateway → Ollama direct connection → g4f  │
│   Switch between multiple providers via unified API  │
├─────────────────────────────────────────────────────┤
│ Layer 9: Skill Registry                              │
│   Search, install, and verify Skills / Plugins / Extensions │
└─────────────────────────────────────────────────────┘
```

### Layer Descriptions

| Layer | What It Does | Example |
|-------|-------------|---------|
| **User Layer** | Receives user input | "Create a competitive analysis report" |
| **Design Interview** | Clarifies ambiguous instructions | "Which competitors? Time period? Key metrics?" |
| **Task Orchestrator** | Creates an execution plan | Generates a 5-stage DAG, assigns AI to each stage |
| **Skill Layer** | Performs the actual work | Web search, data organization, report generation |
| **Judge Layer** | Verifies quality | Prohibited item checks, cross-verification with different model |
| **Re-Propose Layer** | Retries on failure | Reconstructs DAG with a different approach |
| **State & Memory** | Remembers state and experience | Saves successful patterns, applies them next time |
| **Provider Interface** | Connects to AI models | OpenAI / Anthropic / Gemini / Ollama |
| **Skill Registry** | Manages extensions | Skill search, install, and update |

---

## 5. Technology Stack

### Backend

| Technology | Purpose |
|-----------|---------|
| Python 3.12+ | Backend language |
| FastAPI | REST API framework |
| SQLAlchemy 2.x (async) | ORM (database access) |
| Alembic | DB migration |
| SQLite / PostgreSQL | Database |
| LiteLLM | LLM gateway |
| httpx | Ollama direct HTTP connection |

### Frontend

| Technology | Purpose |
|-----------|---------|
| React 19 | UI framework |
| TypeScript | Type-safe development |
| Vite | Build tool |
| Tailwind CSS | Styling |
| shadcn/ui | UI components |
| Zustand | State management |
| TanStack Query | Server state management |

### Desktop

| Technology | Purpose |
|-----------|---------|
| Tauri v2 (Rust) | Desktop application |

### Edge Deployment

| Technology | Purpose |
|-----------|---------|
| Cloudflare Workers | Edge execution |
| Hono | Web framework for Workers |
| D1 | Edge SQLite |

---

## 6. Implementation Status

### Backend (Implemented — Substantial Code)

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Ollama Provider | `providers/ollama_provider.py` | 656 | Implemented |
| Local RAG | `providers/local_rag.py` | 572 | Implemented |
| Ollama Integration | `providers/ollama_integration.py` | 511 | Implemented |
| LLM Gateway | `providers/gateway.py` | 488 | Implemented |
| g4f Provider | `providers/g4f_provider.py` | 322 | Implemented |
| Judge Layer | `orchestration/judge.py` | 250 | Implemented |
| State Machine | `orchestration/state_machine.py` | 239 | Implemented |
| Experience Memory | `orchestration/experience_memory.py` | 182 | Implemented |
| Knowledge Refresh | `orchestration/knowledge_refresh.py` | 169 | Implemented |
| Failure Taxonomy | `orchestration/failure_taxonomy.py` | 152 | Implemented |
| Cost Guard | `orchestration/cost_guard.py` | 149 | Implemented |
| DAG | `orchestration/dag.py` | 147 | Implemented |
| Artifact Bridge | `orchestration/artifact_bridge.py` | 137 | Implemented |
| Audit Logger | `audit/logger.py` | 137 | Implemented |
| Secret Manager | `security/secret_manager.py` | 133 | Implemented |
| Re-Propose | `orchestration/repropose.py` | 120 | Implemented |
| Quality SLA | `orchestration/quality_sla.py` | 116 | Implemented |
| Autonomy Boundary | `policies/autonomy_boundary.py` | 113 | Implemented |
| Design Interview | `orchestration/interview.py` | 112 | Implemented |
| Approval Gate | `policies/approval_gate.py` | 109 | Implemented |
| Sanitizer | `security/sanitizer.py` | 83 | Implemented |

### API Endpoints (Implemented — 24 Route Modules)

| Endpoint Group | Key Features |
|---------------|-------------|
| `/auth` | Login, registration, anonymous session, OAuth |
| `/companies` | Company CRUD, dashboard |
| `/tickets` | Ticket creation, listing, details, state transitions, file attachment |
| `/specs_plans` | Spec / Plan creation and approval |
| `/tasks` | Task creation, execution, completion |
| `/agents` | Agent management, role-based addition, pause, resume |
| `/approvals` | Approval listing, approve, reject |
| `/artifacts` | Artifact management |
| `/audit` | Audit log listing and filtering |
| `/budgets` | Budget policy and cost management |
| `/heartbeats` | Periodic execution policies and run history |
| `/registry` | Skill / Plugin / Extension search, CRUD, natural language generation |
| `/ollama` | Local LLM direct operations, RAG |
| `/settings` | Application settings, tool connections |
| `/config` | Runtime configuration management |
| `/models` | Model catalog, health check, deprecation management |
| `/observability` | Inference traces, communication logs, execution monitoring |
| `/self-improvement` | AI self-improvement (Skill analysis, improvement, Judge tuning, A/B testing) |
| `/multi-model` | Multi-model comparison, brainstorming, conversation memory, per-role settings |
| `/secretary` | Secretary AI (brain dump, daily summary) |
| `/knowledge` | Knowledge store, change detection |
| `/platform` | MCP, Sentry, IAM, hypothesis verification, sessions, investigation |
| `/projects` | Project and goal management |
| WebSocket `/ws/events` | Real-time event delivery |

### Frontend (23 Screens)

| Screen | Status | Notes |
|--------|--------|-------|
| LoginPage | Implemented | Login, registration, Google OAuth |
| SetupPage | Implemented | 6-step wizard |
| DashboardPage | Implemented | Statistics, natural language input, recommended actions |
| InterviewPage | Implemented | 7-question Design Interview |
| SettingsPage | Implemented | LLM API key configuration, execution mode, Ollama, provider connections |
| ReleasesPage | Implemented | Version management and downloads |
| DownloadPage | Implemented | OS-specific installer distribution |
| TicketListPage | UI exists | Data connection is partial |
| TicketDetailPage | UI exists | Section structure only |
| SpecPlanPage | UI exists | DAG visualization placeholder |
| OrgChartPage | UI exists | Organization structure skeleton |
| ApprovalsPage | UI exists | Filter and table structure |
| AuditPage | UI exists | Filter and table structure |
| HeartbeatsPage | UI exists | Policy and run history structure |
| CostsPage | UI exists | Budget and expenditure structure |
| ArtifactsPage | UI exists | Artifact listing structure |
| SkillsPage | UI exists | Search and status badges |
| SkillCreatePage | UI exists | Creation form |
| PluginsPage | UI exists | Browser and installer |
| PermissionsPage | UI exists | Permissions management dashboard |
| AgentMonitorPage | UI exists | Agent monitoring dashboard |
| SecretaryPage | Implemented | Brain dump, daily summary, priority suggestions |
| BrainstormPage | Implemented | Brainstorming, multi-model comparison, per-role settings, AI org management |

### ORM Models (29 Tables)

Company, CompanyMember, User, Department, Team, Agent, Project, Goal, Ticket, TicketThread, Spec, Plan, Task, TaskRun, Artifact, Review, ApprovalRequest, HeartbeatPolicy, HeartbeatRun, BudgetPolicy, CostLedger, Skill, Plugin, Extension, ToolConnection, ToolCallTrace, PolicyPack, SecretRef, AuditLog

### Tests

| Test | Target |
|------|--------|
| `test_auth.py` | Authentication |
| `test_companies.py` | Company management |
| `test_tickets.py` | Tickets |
| `test_health.py` | Health check |
| `test_state_machine.py` | State transitions |
| `test_cost_guard.py` | Cost management |
| `test_failure_taxonomy.py` | Failure classification |
| `test_audit_logger.py` | Audit logs |
| `test_registry.py` | Registry |
| `test_ollama_provider.py` | Ollama |
| `test_chaos_dag.py` | Chaos testing (Self-Healing DAG) |
| `test_ollama_integration.py` | Ollama integration |
| `zeo_bench.py` | ZEO-Bench (Judge Layer 200-question benchmark) |

---

## 7. Offline Operation

ZEO can operate without cloud APIs.

### Fully Offline Configuration

```
Ollama (local LLM) + SQLite (local DB) + Local RAG
```

#### Setup

```bash
# 1. Install Ollama
# Download from https://ollama.com/

# 2. Download models
ollama pull qwen3:8b        # General purpose (recommended)
ollama pull qwen3-coder:30b # Coding specialized

# 3. Configure .env
echo "OLLAMA_BASE_URL=http://localhost:11434" >> apps/api/.env
echo "DEFAULT_EXECUTION_MODE=free" >> apps/api/.env
```

#### CLI Mode

```bash
zero-employee local                      # Chat with default model
zero-employee local --model qwen3:8b     # Specify model
zero-employee local --lang ja            # Japanese mode
zero-employee models                     # List installed models
zero-employee pull qwen3:8b              # Download model
```

#### Features Available Offline

| Feature | Available | Notes |
|---------|-----------|-------|
| Design Interview | Yes | Inference with Ollama model |
| Spec / Plan generation | Yes | Inference with Ollama model |
| Task execution (local Skills) | Yes | File operations, analysis, etc. |
| Judge Layer (rule-based) | Yes | Stage 1 only |
| Judge Layer (Cross-Model) | Conditional | Requires multiple Ollama models |
| Approval flow | Yes | Completed within local UI |
| Audit logs | Yes | Recorded in SQLite |
| Local RAG search | Yes | TF-IDF based |
| Experience Memory | Yes | Recorded in SQLite |
| External API integration | No | Requires internet |

### Supported Local Models

| Model | Purpose |
|-------|---------|
| `qwen3:8b` / `qwen3:32b` | High-quality general-purpose inference |
| `qwen3-coder:30b` | Coding specialized |
| `llama3.2` | Meta general-purpose model |
| `mistral` | Mistral general-purpose model |
| `phi3` | Microsoft lightweight model |
| `deepseek-coder-v2` | Coding specialized |
| `codellama` | Meta code specialized |
| `gemma2` | Google lightweight model |

Models installed in Ollama are automatically detected.

---

## 8. Boundary Between Core and Extension Features

ZEO adopts a **"don't bundle everything from the start"** design philosophy.

### Core (Essential to the Platform)

Authentication, permissions, audit, state management, execution control, DAG, Judge, approval flow, Experience Memory

-> Without these, "AI business orchestration" cannot function

### Skill (Minimum Capability Unit)

File organization, translation, script generation, competitive analysis, etc.

-> 6 built-in Skills are included in `skills/builtin/`

### Plugin (Business Function Package)

AI Avatar, AI Secretary, Discord Bot, Slack Bot, LINE Bot, YouTube operations, Research, Back Office, etc.

-> Manifests defined in `plugins/` (9 Plugins). Business-specific logic is not placed in the core

### Extension (System Infrastructure Extension)

OAuth authentication, MCP connection, notifications, Obsidian integration, etc.

-> Manifests defined in `extensions/`. Adding connection targets is not placed in the core

**Decision Criteria**: "Would approval, audit, and execution control break without it?"

- Yes -> Core
- No -> Skill / Plugin / Extension

For details, see [docs/dev/FEATURE_BOUNDARY.md](../dev/FEATURE_BOUNDARY.md).

---

## 9. External Tool Integration

### Currently Defined Integrations

| Integration | Type | Status | Description |
|------------|------|--------|-------------|
| **AI Avatar** | Plugin | Manifest exists | Learns user's decision criteria and writing style, acts as a proxy |
| **AI Secretary** | Plugin | Manifest exists | Briefing, priority suggestions, bridge between user and AI organization |
| **Discord** | Plugin | Manifest exists (v0.2.0) | Ticket creation, approval, dialogue, briefing via Bot |
| **Slack** | Plugin | Manifest exists (v0.2.0) | Ticket creation, approval, dialogue, briefing via Slash Command |
| **LINE** | Plugin | Manifest exists | Ticket creation, approval, notifications via LINE Bot |
| **Obsidian** | Extension | Manifest exists | Bidirectional integration with Vault as Knowledge Source |
| **MCP** | Extension | Manifest exists | Model Context Protocol compatible tool connection |
| **Google OAuth** | Extension | Manifest exists | Google account authentication |
| **Notifications** | Extension | Manifest exists | Slack / Discord / LINE / Email notifications |

### AI Avatar / AI Secretary

**AI Avatar (AI Avatar Plugin)** learns the user's decision criteria and writing style, and acts as the user's "avatar." It can also reflect the user's values in Judge Layer decision criteria.

**AI Secretary (AI Secretary Plugin)** functions as a "hub" connecting the user with the AI organization, generating morning briefings, next action suggestions, and progress summaries. It can deliver briefings via Discord / Slack / LINE in collaboration with chat tool Plugins.

### Multi-Agent Operations from Discord / Slack / LINE

By installing Discord / Slack / LINE Bot Plugins, you can send instructions directly to ZEO's multi-agent system from chat applications.

```
Discord/Slack/LINE → Bot receives message
  → Ticket creation request to ZEO API
    → Design Interview → Plan → Tasks execution
      → Results replied to chat channel
```

For operations requiring approval, an approval dialog is displayed within the chat tool as well.

**Command Examples:**
```
/zeo ticket Create a competitive analysis report
/zeo status
/zeo briefing
/zeo ask What are the risks of this initiative?
```

### Obsidian Integration

By installing the Obsidian Extension, you can use Markdown files in your Vault as a Knowledge Source.

- **Import**: Ingest notes from Vault into RAG
- **Export**: Output Spec / Plan / Tasks / artifacts as Markdown to Vault
- **Link Utilization**: Reference Obsidian's `[[internal links]]` structure as a knowledge graph
- **Fully Offline**: Obsidian Sync is not required; just set the local Vault path

---

## 10. Design Considerations and Future Direction (v0.1)

### Principles to Avoid Over-Engineering

ZEO's design documents cover an extremely wide scope, but implementation follows these principles:

1. **MVP First** — Getting the end-to-end flow working is the top priority
2. **Add features via Plugins** — Don't bloat the core
3. **The 9 layers are a responsibility separation guide** — Not all layers need to be fully implemented
4. **Screens are enriched gradually** — The UI skeleton is in place; data connections are being added
5. **Community extensions** — Users share and publish Plugins to expand external service integrations

### v0.1 Feature Bloat Review

The following features are included in the v0.1 codebase but are **positioned as extension features**, not core features.
They are planned to be separated into independent Extension / Skill / Plugin packages in future versions.

| Feature | Migration Target | Reason |
|---------|-----------------|--------|
| Sentry integration | Extension | Error monitoring is not required for core approval, audit, and execution control |
| AI investigation tool | Skill | DB/log investigation is a single-purpose task |
| Hypothesis verification engine | Plugin | Multi-agent hypothesis verification is an advanced feature |
| MCP server | Extension | A connection target extension, not core-essential |
| External skill import | Extension | A Registry extension feature |

For details, see [docs/dev/FEATURE_BOUNDARY.md](../dev/FEATURE_BOUNDARY.md).

### Current Issues

| Issue | Details |
|-------|---------|
| Frontend data connection | 12 screens are UI skeletons only (backend APIs exist) |
| features/ modules | 11 modules contain only `.gitkeep` (logic is written directly in pages) |
| packages/ shared libraries | 5 packages contain only `.gitkeep` |
| Worker core logic | Runner/executor structure exists but logic is thin |
| E2E tests | Not implemented |

### Future Priorities

1. **Complete frontend <-> backend connection**
   - Data binding for ticket list/detail
   - Real-time updates for approval screen
   - Filter functionality for audit log screen

2. **E2E flow from Design Interview -> Spec -> Plan -> Task execution**
   - End-to-end from natural language input to artifact generation

3. **Plugin / Extension installation mechanism**
   - Manifest-based loading and execution

4. **Full-scale Worker operation**
   - Background task execution
   - Heartbeat scheduler

---

## 11. Document Index

> For detailed descriptions of all documents (purpose, target audience, main content), see **[`docs/MD_FILES_INDEX.md`](../MD_FILES_INDEX.md)**.

**For Users (`docs/`):**

| File | Content | Target Audience |
|------|---------|----------------|
| `README.md` | Quick start, technology stack | Everyone |
| `docs/ABOUT.md` | Why ZEO is needed, comparison with conventional tools | Non-engineers, executives |
| `docs/USER_GUIDE.md` | From setup to operation guide | End users |
| **`docs/OVERVIEW.md` (this document)** | **Comprehensive explanation of philosophy, features, and structure** | **First-time visitors** |
| `docs/FEATURES.md` | Complete list of implemented features (34 sections) | Feature verification, evaluators |
| `docs/SECURITY.md` | Security policy, pre-deployment checklist | Operators |
| `docs/CHANGELOG.md` | Change history | Everyone |
| `docs/ja-JP/Zero-Employee Orchestrator.md` | Top-level reference document (philosophy, requirements) | Designers |
| `docs/MD_FILES_INDEX.md` | Index of all `.md` files | Everyone |

**For Developers (`docs/dev/`):**

| File | Content | Target Audience |
|------|---------|----------------|
| `docs/dev/DESIGN.md` | Implementation design document (DB, API, state transitions) | Implementers |
| `docs/dev/MASTER_GUIDE.md` | Implementation and operations guide | AI agents, implementers |
| `docs/ja-JP/BUILD_GUIDE.md` | Step-by-step build instructions (Japanese, phase-by-phase) | Source build users |
| `docs/dev/FEATURE_BOUNDARY.md` | Core vs. extension feature boundary definitions | Developers |
| `docs/dev/PROPOSAL.md` | Project proposal document | Grant reviewers, sponsors |
| `CLAUDE.md` | Development guide for Claude Code | AI agents |

**Other:**

| File | Content | Target Audience |
|------|---------|----------------|
| `apps/edge/README.md` | Cloudflare Workers deployment method comparison | Infrastructure team |
| `apps/edge/full/README.md` | Full Workers (Method B) setup | Infrastructure team |
| `apps/edge/proxy/README.md` | Proxy (Method A) setup | Infrastructure team |

---

## Directory Structure

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── core/           # Configuration, DB, security, i18n
│   │   │   ├── api/routes/     # REST API (24 routes)
│   │   │   ├── api/ws/         # WebSocket
│   │   │   ├── models/         # ORM models (29 tables / 18 files)
│   │   │   ├── schemas/        # Pydantic DTO
│   │   │   ├── services/       # Business logic
│   │   │   ├── repositories/   # DB I/O abstraction
│   │   │   ├── orchestration/  # DAG, Judge, state machine, Memory (18 modules)
│   │   │   ├── heartbeat/      # Periodic execution scheduler
│   │   │   ├── providers/      # LLM Gateway, Ollama, g4f, RAG
│   │   │   ├── tools/          # External tool connections (MCP/Webhook/API/CLI)
│   │   │   ├── policies/       # Approval gate, autonomy boundary
│   │   │   ├── security/       # Secret Manager, Sanitizer, IAM
│   │   │   ├── integrations/   # Sentry, MCP Server, external skills (*extensions)
│   │   │   ├── audit/          # Audit logs
│   │   │   └── tests/          # Tests
│   │   └── alembic/            # DB migration
│   ├── desktop/                # Tauri desktop app
│   │   └── ui/src/             # React frontend (23 screens)
│   ├── edge/                   # Cloudflare Workers
│   │   ├── proxy/              # Method A: Reverse proxy
│   │   └── full/               # Method B: Hono + D1 full migration
│   └── worker/                 # Background worker
├── skills/
│   ├── builtin/                # Built-in Skills (6)
│   └── templates/              # Skill templates
├── plugins/                    # Plugin manifests
│   ├── ai-avatar/              # AI Avatar
│   ├── ai-secretary/           # AI Secretary
│   ├── discord-bot/            # Discord Bot
│   ├── slack-bot/              # Slack Bot
│   ├── line-bot/               # LINE Bot
│   ├── youtube/                # YouTube operations
│   ├── research/               # Research
│   └── backoffice/             # Back Office
├── extensions/                 # Extension manifests
│   ├── oauth/                  # OAuth authentication
│   ├── mcp/                    # MCP connection
│   ├── notifications/          # Notifications
│   └── obsidian/               # Obsidian integration
├── packages/                   # Shared packages
│   ├── config/                 # Configuration
│   ├── sdk/                    # SDK
│   ├── skill-manifest/         # Skill manifest
│   ├── types/                  # Shared type definitions
│   └── ui/                     # Shared UI
├── docs/                       # User documentation
│   └── dev/                    # Developer documentation
├── scripts/                    # Development and deployment scripts
│   ├── dev/                    # Development
│   ├── lint/                   # Linting
│   ├── release/                # Release
│   └── seed/                   # Seed data
├── examples/                   # Samples and examples
├── docker/                     # Docker configuration
├── assets/                     # Logo and images
├── Dockerfile                  # Rootless container
├── docker-compose.yml          # All-in-one service startup
├── setup.sh                    # Setup script
└── start.sh                    # Startup script
```

---

*Zero-Employee Orchestrator — AI, working as an organization.*
