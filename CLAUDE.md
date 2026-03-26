# Zero-Employee Orchestrator -- Claude Code Development Guide

> An AI orchestration platform that defines business workflows in natural language,
> delegates tasks across multiple AI agents with role-based assignment, and executes
> with human approval gates and full auditability.

## Before Starting Work

Run the following at the start of each session to check the latest state:

```bash
git log --oneline -10
ls apps/api/app/
ls apps/api/app/tests/
```

Reference documents:
- `README.md` -- **Always check first. Contains feature list, configuration, and security settings**
- `docs/Zero-Employee Orchestrator.md` -- Top-level requirements document
- `docs/dev/DESIGN.md` -- Implementation design document
- `docs/dev/MASTER_GUIDE.md` -- Implementation operations guide
- `docs/dev/BUILD_GUIDE.md` -- Build-from-scratch guide (by phase)
- `docs/dev/FEATURE_BOUNDARY.md` -- Core vs Skill/Plugin/Extension boundary definition
- `ROADMAP.md` -- Roadmap (remaining tasks from v0.2 onward)
- `docs/dev/DEVELOPER_SETUP.md` -- Developer setup guide (Sentry, red-team testing, etc.)
- `USER_SETUP.md` -- User setup guide (API keys, security, DB, deployment, etc.)

**IMPORTANT: If this file contains outdated information, read the actual code and README.md and update it. Always check the repository structure and all md files. When reviewing the repository, check all files. Record updates in md files.**

## Architecture (9 Layers)

1. User Layer -- GUI / CLI / TUI
2. Design Interview -- Brainstorming and requirements exploration
3. Task Orchestrator -- DAG decomposition, cost estimation, progress management
4. Skill Layer -- Specialized Skills + Local Context
5. Judge Layer -- Two-stage Detection + Cross-Model Verification
6. Re-Propose -- Rejection and dynamic DAG reconstruction
7. State & Memory -- Experience Memory, Failure Taxonomy
8. Provider Interface -- LLM Gateway (LiteLLM)
9. Skill Registry -- Skill/Plugin/Extension publishing, search, and import

## Directory Structure

```
apps/
├── api/              # FastAPI backend (Python 3.12+)
│   ├── app/
│   │   ├── core/           # Config, DB, rate limiting, i18n
│   │   ├── api/routes/     # REST API endpoints (40 route modules, 350+ endpoints)
│   │   ├── api/ws/         # WebSocket (events, browser_assist_ws)
│   │   ├── api/deps/       # Dependency injection
│   │   ├── models/         # SQLAlchemy ORM
│   │   ├── schemas/        # Pydantic DTO
│   │   ├── services/       # Business logic (25 services)
│   │   ├── repositories/   # DB I/O abstraction
│   │   ├── orchestration/  # DAG, Judge, state machine, Knowledge, Memory, MetaSkill, A2A, Transparency (22 modules)
│   │   ├── heartbeat/      # Heartbeat scheduler
│   │   ├── providers/      # LLM gateway, Ollama, g4f, RAG, ModelRegistry, WebSession
│   │   ├── tools/          # External tool connectors (MCP/Webhook/API/CLI/GraphQL/Browser/BrowserAdapter/LSP)
│   │   ├── policies/       # Approval gates, autonomy boundaries
│   │   ├── security/       # IAM, secrets, sanitize, prompt defense, PII, sandbox, data protection, red-team
│   │   ├── integrations/   # Sentry, MCP, external skills, browser assist, AI research, media generation, AI tools, iPaaS, export, repurpose, RSS/ToS, Obsidian, cloud, smart devices, app connector hub
│   │   ├── audit/          # Audit logging
│   │   └── tests/          # Tests
│   ├── alembic/            # DB migrations
│   └── model_catalog.json  # LLM model catalog (family-based, auto version resolution)
├── desktop/          # Tauri v2 + React UI
├── edge/             # Cloudflare Workers (proxy / full)
└── worker/           # Background workers
skills/builtin/       # Built-in Skills (8: 7 Python modules + browser-assist manifest)
plugins/              # Plugin manifests (10 Plugins)
extensions/           # Extension manifests (10 Extensions + Chrome extension)
```

## Commands

```bash
# Start server
zero-employee serve --reload        # Hot reload (port 18234)

# Chat mode (all providers, natural language for all operations)
zero-employee chat                  # Default settings
zero-employee chat --mode free      # Ollama / g4f mode
zero-employee chat --lang en        # English mode

# Tests
pytest apps/api/app/tests/          # All tests
pytest apps/api/app/tests/test_cost_guard.py -v  # Individual test

# Lint and format
ruff check apps/api/app/
ruff format apps/api/app/

# DB migration
zero-employee db upgrade

# Update
zero-employee update                # Update to latest
zero-employee update --check        # Check only

# Other
zero-employee health
zero-employee models
zero-employee config list
```

## pyproject.toml Management (Important)

**IMPORTANT: Two `pyproject.toml` files exist. Always use the `bump-version` script when updating versions.**

| File | Purpose | Package Path |
|------|---------|-------------|
| `pyproject.toml` (root) | PyPI publishing and build | `packages = ["apps/api/app"]` |
| `apps/api/pyproject.toml` | Development (`working-directory: apps/api`) | `packages = ["app"]` |

- Version update: `./scripts/bump-version.sh 0.2.0`
- `name`, `version`, `description`, `requires-python`, `license`, `dependencies`, `dev dependencies` must match in both files
- CI (`check-metadata-sync` job) will fail if they are out of sync
- When changing metadata, always update both files simultaneously

## Coding Conventions

- **Python**: ruff (line-length=100), type hints required, all FastAPI endpoints use `async def`
- **TypeScript**: strict mode, functional components only, Tailwind CSS
- Tests use pytest + pytest-asyncio
- Defer code style details to ruff. Fix any linter errors

## Design Principles

### Skill / Plugin / Extension Enabled States

- **Built-in system protection skills** -> Always enabled, cannot be deleted or disabled
- **User-added Skill / Plugin / Extension / Heartbeat** -> Enabled by default (users can manually disable)
- "Minimal initial state" means "nothing unnecessary is included" -- features that users explicitly add should be enabled by default

### LLM Usage Design Principles

- API key input is not required. Multiple key-free options are provided:
  - g4f (subscription mode): No key needed
  - Ollama: Fully offline with local models
  - Multi-LLM platforms (OpenRouter, etc.): One account for multiple LLMs
- ZEO does not charge usage fees. LLM API costs are paid directly by users to each provider
- No specific provider is promoted as "recommended". Docs and UI present options equally
- Maintain extensibility for new multi-LLM platforms or key-free services

## Model Catalog (`apps/api/model_catalog.json`)

**IMPORTANT: Model IDs are managed by family name (do not include version numbers).**

```
Family ID:         "anthropic/claude-opus"
latest_model_id:   "claude-opus-4-6"  <- Used for actual API calls
```

- When updating models, only change `latest_model_id` (no code changes needed)
- `ModelRegistry.resolve_api_id()` auto-resolves family -> latest version
- Execution modes: quality / speed / cost / free / subscription
- RSS/ToS auto-update pipeline implemented (`integrations/rss_tos_monitor.py`)

## Security (Critical)

**IMPORTANT: The following rules must always be followed.**

1. **When passing external data to LLMs**: Always wrap with `wrap_external_data()` boundary markers
2. **Prompt injection checks**: Inspect user input before passing to LLMs
3. **When adding dangerous operations**: Register in `approval_gate.py` and `autonomy_boundary.py`
4. **Secrets**: Sanitize via `sanitizer.py` before logging
5. **New API endpoints**: Verify that security headers are applied
6. **PII protection**: Detect and mask via `pii_guard.py` before passing user input to AI
7. **File access**: Check access through the `sandbox.py` sandbox
8. **Data transfer**: Check upload/download permissions via `data_protection.py`
9. **AI must never access unauthorized folders or files**
10. **Password uploads are always blocked**
11. **Workspace isolation**: Check isolation via `workspace_isolation.py`. AI can only access internal storage (default)
12. **Per-task environment overrides**: If chat instructions differ from system settings, use `should_request_approval()` to ask the user for permission

Defense layers:
- Workspace isolation (`security/workspace_isolation.py`) -- No local/cloud connections by default
- Prompt injection defense (`security/prompt_guard.py`) -- 5 categories, 40+ patterns
- Approval gates (`policies/approval_gate.py`) -- 12 categories of dangerous operations
- Autonomy boundaries (`policies/autonomy_boundary.py`)
- IAM (`security/iam.py`) -- AI denied secret and admin access
- PII guard (`security/pii_guard.py`) -- 13 categories of personal info detection and masking
- File sandbox (`security/sandbox.py`) -- Whitelist-based folder access control
- Data protection (`security/data_protection.py`) -- Upload/download policy control
- Security headers and request validation (`security/security_headers.py`)
- Secret management (`security/secret_manager.py`) -- Fernet encryption
- Sanitization (`security/sanitizer.py`)
- Rate limiting (`core/rate_limit.py`)

## Browser Assist

Two usage modes:
1. **Chrome Extension**: Overlay chat + real-time screen sharing (`extensions/browser-assist/chrome-extension/`)
2. **REST API**: Analysis via screenshot submission (`apps/api/app/api/routes/browser_assist.py`)

WebSocket endpoint: `ws://localhost:18234/ws/browser-assist`

Supports file and image attachments (both Chrome extension and REST API).

## Plugin-based Browser Automation (Browser Adapter)

Like VS Code extensions, browser automation tools can be added/switched as plugins.
By default, only a minimal Playwright adapter is included. browser-use etc. are installed via Plugin.

- Adapter registry: `apps/api/app/tools/browser_adapter.py`
- browser-use Plugin: `plugins/browser-use/manifest.json`
- API: `/api/v1/browser-automation/adapters`, `/api/v1/browser-automation/tasks`

## Plugin Loader

VS Code-style dynamic plugin management. Install by saying "add browser-use" or "add image generation tool" in natural language.

- Plugin Loader: `apps/api/app/services/plugin_loader.py`
- Generic Tool Registry: ToolRegistry (AI agents dynamically select optimal tools per task)
- Supported categories: browser-automation, image-generation, music-generation, audio-generation, video-generation, search, data-analysis, three-d, communication, code-generation, custom
- Auto environment checks: pip packages, API keys, browser, LLM providers
- API: `/api/v1/browser-automation/plugins/*`, `/api/v1/browser-automation/tools/*`

## Transparency / Fact-checking (Transparency Layer)

Transparency layer to prevent AI from being a black box.

- Transparency report: `apps/api/app/orchestration/transparency.py`
- Disclose sources/information referenced by AI to users
- Present information needed for approval decisions (cost, risk, permissions, data flow, reversibility)
- Fact-check item user confirmation flow
- Display AI reasoning summary, uncertainties, and questions

## Web AI Sessions (Use AI without API fees)

Method to use GPT, Gemini, Claude, etc. without API fees.

- Web Session Provider: `apps/api/app/providers/web_session_provider.py`
- Methods: g4f (recommended), Ollama (local), browser session
- API: `/api/v1/browser-automation/web-ai/*`

## App Connector Hub

Hub for managing integrations with external applications in a unified way.
Operates only within the scope permitted by the user.

- Connector hub: `apps/api/app/integrations/app_connector.py`
- Supported categories (16): knowledge_base, note_taking, document, productivity, project_management, communication, crm, calendar, email, cloud_storage, design, code_hosting, database, analytics, automation, custom
- Supported apps (35+): Obsidian, Notion, Logseq, Joplin, Anytype, Roam Research, Google Docs/Sheets/Drive/Calendar/Gmail, Microsoft 365/Teams/OneDrive/Outlook, Confluence, Jira, Linear, Asana, Trello, ClickUp, Slack, Discord, HubSpot, Salesforce, Figma, Canva, Airtable, Dropbox, GitHub, GitLab, n8n, Zapier, Make
- Custom app registration supported (users can add arbitrary apps)
- API: `/api/v1/app-integrations/*`

Security:
- Connections are not established until explicitly permitted by the user
- Permission control (read/write/delete/sync/export + path restrictions)
- Workspace isolation, approval gates, PII guard, and audit logging applied

## Media Generation / AI Tool Integration

- Media generation: `apps/api/app/integrations/media_generation.py` (image, video, audio, music, 3D; dynamic provider registration)
- AI tool registry: `apps/api/app/integrations/ai_tools.py` (45+ external tools, 19 categories)
- **Tools are not fixed; users freely choose and switch** -- managed by Plugin Loader's ToolRegistry
- API: `/api/v1/media/*`, `/api/v1/ai-tools/*`

## API Endpoints

Prefix: `/api/v1`

For the latest endpoint list, check `apps/api/app/api/routes/__init__.py`.

Major groups: auth, companies, agents, tickets, specs-plans, tasks, approvals,
budgets, audit, registry, models, observability (traces/communications/monitor),
ollama, knowledge, config, self-improvement, browser-assist, **browser-automation**,
secretary, brainstorm, conversation-memory, hypotheses, sessions, org-setup,
platform, security, media, ai-tools, **app-integrations**, **files, user-input,
resources, ipaas, export, marketplace, teams, governance, quality-insights**
(prerequisite-monitor, spec-contradiction, task-replay, judgment-review, plan-quality)

## Skill / Plugin / Extension

| Type | Role | Examples |
|------|------|---------|
| Skill | Single-purpose specialized processing | spec-writer, review-assistant, browser-assist |
| Plugin | Bundles multiple Skills | ai-secretary, ai-avatar, research |
| Extension | System integration and infrastructure | mcp, oauth, notifications, obsidian, notion, logseq, joplin, google-workspace, microsoft-365, browser-assist (Chrome extension) |

- Built-in Skills (8): spec-writer, plan-writer, task-breakdown, review-assistant, artifact-summarizer, local-context, domain-skills, browser-assist
- System protection Skills cannot be deleted or disabled
- Natural language skill generation: `POST /api/v1/registry/skills/generate` (16 dangerous pattern detections)

## Ports

- FastAPI: 18234
- Vite dev server: 5173

## Prohibited

- Blurring Skill / Plugin / Extension boundaries
- Silently executing approval-required operations
- External transmissions or permission changes without audit logging
- Passing external data to LLMs without `wrap_external_data()`
- Disabling security headers
- Using version-numbered IDs directly in model catalog (use `latest_model_id`)
- **AI accessing unauthorized folders or files**
- **Uploading data containing passwords or credentials**
- **Passing user input to AI without PII detection**

## Roadmap

All formerly planned v0.2-v1.0 features are implemented in v0.1. Remaining tasks:

- **v0.2**: Complete frontend data connections, features/ separation, Plugin Loader implementation
- **v0.3**: Community Skill ecosystem, anonymous feedback aggregation
- **v1.0**: Self-Improvement Loop automation, Cross-Orchestrator Learning

See `ROADMAP.md` for details.
