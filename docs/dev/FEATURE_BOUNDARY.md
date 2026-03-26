# Feature Boundary Definition — Core Features vs Skill / Plugin / Extension

> Created: 2026-03-09 / Updated: 2026-03-10 (v0.1 — Feature boundary revision)
> Purpose: To explicitly define the boundary between features that should be included in the core from the start and features that should be added later as Skills / Plugins / Extensions.

---

## Principles

1. **Core**: Authentication, authorization, auditing, state management, execution control, observability — stability is the top priority
2. **Skill**: Execution capability for a single task — business-specific logic
3. **Plugin**: A bundle of multiple Skills plus supporting features — a business function package
4. **Extension**: Expansion of connection targets, UI, and runtime environments — system infrastructure extensions

**Decision criteria**: "Would approval, auditing, or execution control break without it?" — If Yes, it's core. If No, it's an extension.

---

## Core Features (Required in the main system)

### Authentication & Security
- Local authentication (user registration, login, session management)
- Role-based access control (Owner / Admin / User / Auditor / Developer)
- Secret Manager (encrypted API key storage)
- Sanitizer (masking of sensitive information)

### 9-Layer Architecture Foundation
- **Design Interview** — Question generation for requirement deep-dives, answer accumulation, context integration via file attachments
- **Task Orchestrator** — DAG generation, Skill assignment, cost estimation, Self-Healing
- **Skill Execution Framework** — Framework for loading, executing, and retrieving results from Skills
- **Judge Layer** — Rule-based primary evaluation + Cross-Model Verification
- **Re-Propose Layer** — Rejection, re-proposal, Plan Diff
- **State Machine** — State transitions for Ticket / Task / Approval / Agent
- **Experience Memory** — Persistent memory of success patterns and improvement knowledge
- **Failure Taxonomy** — Failure classification and recurrence prevention
- **Provider Interface** — LLM Gateway (LiteLLM / direct Ollama connection)

### Approval & Auditing
- Approval workflow (mandatory blocking of dangerous operations)
- Approval gate (detection of 12 categories of dangerous operations)
- Autonomous execution boundary management
- Audit log (recording of all significant operations, non-deletable)

### Data Management
- Data persistence via SQLite / PostgreSQL
- Structured storage of Spec / Plan / Tasks
- Artifact management
- Cost measurement and budget management

### UI Foundation
- Dashboard
- Ticket management screen
- Approval management screen
- Audit log screen
- Settings screen

### Offline Operation
- Ollama Provider (direct local LLM connection)
- Local RAG (file-based vector DB)
- Fully local DB via SQLite
- g4f Provider (subscription mode)

---

## Built-in Skills (Bundled with the main system)

| Skill | Purpose | Reason |
|-------|---------|--------|
| `local_context` | Safe reading of local files | Essential for the core Local Context feature |
| `spec_writer` | Automatic Spec document generation | Required element of the Design Interview flow |
| `plan_writer` | Automatic Plan document generation | Required element of the Task Orchestrator |
| `task_breakdown` | Task decomposition | Required element of DAG generation |
| `review_assistant` | Review support | Assists the Judge Layer |
| `artifact_summarizer` | Artifact summarization | Assists the Artifact Bridge |

---

## Features Added via Plugins (Not included in the core)

### Business-Specific Plugins

| Plugin | Purpose | Status |
|--------|---------|--------|
| `youtube` | YouTube channel management | manifest available |
| `research` | Competitive analysis and market research | manifest available |
| `backoffice` | Accounting, administration, and document organization | manifest available |
| `discord-bot` | Multi-agent operation, interaction, and approval via Discord | manifest available (v0.2.0) |
| `slack-bot` | Multi-agent operation, interaction, and approval via Slack | manifest available (v0.2.0) |

### AI Agent Extension Plugins

| Plugin | Purpose | Status |
|--------|---------|--------|
| `ai-avatar` | Avatar AI (learns the user's judgment criteria and writing style to act on their behalf) | **Newly added** |
| `ai-secretary` | Secretary AI (schedule management, briefings, bridging between the AI organization and the user) | **Newly added** |

#### Avatar AI (ai-avatar) Role

An AI agent that acts as the user's "avatar." It learns the user's values, judgment criteria, and writing style to:

- **Integration with Judge Layer**: Provides the user's judgment patterns as custom rules for the Judge Layer, reflecting them in quality evaluation criteria
- **Proxy review**: Reviews tasks and makes priority judgments when the user is absent (final approval authority always remains with the user)
- **Writing style reproduction**: Creates drafts in the user's writing style and tone
- **Approval pattern learning**: Proposes autonomous execution boundaries based on past approval/rejection patterns

#### Secretary AI (ai-secretary) Role

An AI agent that functions as a "hub" connecting the user and the AI organization:

- **Morning briefing**: Summarizes pending approvals, in-progress tasks, and today's schedule
- **Next action suggestions**: Presents what should be done next based on priority
- **Progress summary**: Reports AI organization activity status in a user-friendly manner
- **Delegation routing**: Routes user instructions to the appropriate agents
- **Chat integration**: Delivers briefings to external chat apps by integrating with Discord/Slack/LINE Bot Plugins

### Chat Tool Integration Plugins

| Plugin | Purpose | Status |
|--------|---------|--------|
| `line-bot` | Multi-agent operation from LINE | **Newly added** |

### AI Self-Improvement Plugin

| Plugin | Purpose | Status |
|--------|---------|--------|
| `ai-self-improvement` | A self-improvement plugin where AI analyzes, improves, and generates AI | **Newly added** |

#### AI Self-Improvement (ai-self-improvement) Role

A plugin that realizes Phase 1 (individual development scope) of AI Self-Improvement:

- **Skill Analyzer**: AI evaluates code quality, performance, and error handling of existing Skills and generates improvement proposals
- **Experience-Driven Judge Tuning**: Automatically proposes custom rules for the Judge Layer based on approval/rejection patterns from Experience Memory
- **Failure-to-Skill**: Automatically generates failure-prevention Skills from accumulated Failure Taxonomy data
- **Skill A/B Testing**: Runs the same task with multiple Skills and quantitatively compares quality, speed, and cost
- **Auto Test Generator**: Automatically generates, executes, and reports test code for Skills

See [docs/AI_SELF_IMPROVEMENT_ROADMAP.md](../AI_SELF_IMPROVEMENT_ROADMAP.md) for details.

### Future Plugin Candidates

| Plugin | Purpose |
|--------|---------|
| `blog-manager` | Blog article planning, drafting, and publication management |
| `sns-scheduler` | Automatic creation of SNS posting calendars |
| `code-review` | Code review and test automation |

---

## Features Added via Extensions (Not included in the core)

### Connection & Authentication

| Extension | Purpose | Status |
|-----------|---------|--------|
| `oauth` | OAuth authentication for Google / GitHub, etc. | manifest available |
| `mcp` | Tool connection via Model Context Protocol | manifest available |
| `notifications` | Notifications via Slack / Discord / LINE / email | manifest available |
| `obsidian` | Bidirectional integration with Obsidian Vault | manifest available |
| `notion` | Notion page and database integration | manifest available |
| `logseq` | Logseq graph integration | manifest available |
| `joplin` | Joplin note integration (REST API) | manifest available |
| `google-workspace` | Google Docs / Sheets / Drive / Calendar / Gmail | manifest available |
| `microsoft-365` | Word / Excel / OneDrive / Outlook / Teams | manifest available |

### General-Purpose App Connector Hub

A general-purpose application connector hub is implemented in `integrations/app_connector.py`.
It provides unified management of connections to 35+ external applications.
It operates only within the scope explicitly authorized by the user and supports custom app registration.

### Reorganization Based on v0.1 Feature Bloat Review

The following features exist in the codebase but are **positioned as extensions rather than core features**.
They are bundled in v0.1 but are planned for future separation as Extensions / Skills / Plugins.

| Feature | Current Location | Migration Target | Reason |
|---------|-----------------|-----------------|--------|
| **Sentry integration** | `integrations/sentry_integration.py` | Extension | Error monitoring is useful but not required for core approval, auditing, or execution control |
| **AI investigation tool** | `integrations/ai_investigator.py` | Skill | DB/log investigation is a single-purpose task and should be provided as a Skill |
| **Hypothesis verification engine** | `orchestration/hypothesis_engine.py` | Plugin | Multi-agent hypothesis verification is an advanced feature not required for basic orchestration |
| **MCP server** | `integrations/mcp_server.py` | Extension | MCP support is a connection target extension and not essential to the core |
| **External skill import** | `integrations/external_skills.py` | Extension | Skill search and import from GitHub is an extension of the Registry |

> **Note**: The features listed above are bundled in the codebase in v0.1, but according to the core feature
> decision criteria — "Would approval, auditing, or execution control break without it?" — they are classified
> as extensions. They will be separated into independent Extension / Skill / Plugin packages in future versions.

### Future Extension Candidates

| Extension | Purpose |
|-----------|---------|
| `sentry` | Sentry-compatible error and performance monitoring |
| `proxy-network` | Corporate proxy and VPN support |
| `google-drive` | Google Drive integration |
| `github-integration` | GitHub Issues / PR integration |
| `gws-integration` | Google Workspace CLI (gws) integration |
| `vscode-ui` | VS Code-style UI theme |
| `generative-ui` | Dynamic responses with forms, tables, and charts |
| `auto-update` | Automatic update mechanism |
| `ipaas-bridge` | Make / Zapier / n8n integration bridge |
| `security-audit` | Security self-testing (white-hat team) |

### Future Skill Candidates

| Skill | Purpose |
|-------|---------|
| `ai-investigator` | AI-powered DB/log investigation |
| `hypothesis-tester` | Parallel hypothesis verification |

---

## Community Plugin Sharing Policy (v0.1)

By providing a mechanism for users to share and publish Plugins, external service integrations can expand without additional work from the developers.

### Sharing Mechanism

1. A user develops a plugin and publishes it to a GitHub repository with a `plugin.json` manifest
2. The repository is tagged with the `zeo-plugin` topic
3. Other users search via `POST /registry/plugins/search-external`
4. One-click installation via `POST /registry/plugins/import`

### Safety Assurance

- Automatic safety checks at import time (detection of 16 types of dangerous patterns)
- Detection and warning of external communication, credential access, and destructive operations
- Creation, sharing, and publication of offensive or harmful plugins is prohibited
- Risk level is displayed and confirmation is requested from the user before installation

---

## Decision Flowchart

```
New feature request
    │
    ├─ Essential for approval, auditing, or state management? → YES → Core feature
    │
    ├─ Execution capability for a single task? → YES → Skill
    │
    ├─ A function package for a specific business domain? → YES → Plugin
    │
    └─ Extension of connection targets, UI, or environment? → YES → Extension
```

## Offline Operation Guarantee

Core features can operate fully offline with the **Ollama + SQLite** combination.

| Feature | Offline | Notes |
|---------|---------|-------|
| Design Interview | Available | Runs on Ollama models |
| Spec / Plan generation | Available | Runs on Ollama models |
| Task execution | Available | Local Skills only |
| Judge Layer | Available | Rule-based evaluation works offline; Cross-Model requires online |
| Approval workflow | Available | Completed within local UI |
| Audit log | Available | Recorded in SQLite |
| Local RAG | Available | File-based TF-IDF |
| External API integration | Unavailable | Requires online |
| Registry search | Unavailable | Already-installed local items are usable |
