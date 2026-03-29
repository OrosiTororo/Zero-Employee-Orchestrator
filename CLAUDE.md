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
- `docs/ja-JP/Zero-Employee Orchestrator.md` -- Top-level requirements document (Japanese)
- `docs/dev/DESIGN.md` -- Implementation design document
- `docs/dev/MASTER_GUIDE.md` -- Implementation operations guide
- `docs/ja-JP/BUILD_GUIDE.md` -- Build-from-scratch guide (by phase, Japanese)
- `docs/dev/FEATURE_BOUNDARY.md` -- Core vs Skill/Plugin/Extension boundary definition
- `ROADMAP.md` -- Roadmap (remaining tasks from v0.2 onward)
- `docs/dev/DEVELOPER_SETUP.md` -- Developer setup guide (Sentry, red-team testing, etc.)
- `docs/dev/REVIEW.md` -- **Comprehensive code review (2026-03-27) with security findings, architecture analysis, and industry best practice comparison**
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
│   │   ├── api/routes/     # REST API endpoints (41 route modules, 350+ endpoints)
│   │   ├── api/ws/         # WebSocket (events, browser_assist_ws)
│   │   ├── api/deps/       # Dependency injection
│   │   ├── models/         # SQLAlchemy ORM
│   │   ├── schemas/        # Pydantic DTO
│   │   ├── services/       # Business logic (25 services)
│   │   ├── repositories/   # DB I/O abstraction
│   │   ├── orchestration/  # DAG, Judge, state machine, Knowledge, Memory, MetaSkill, A2A, Transparency (23 modules)
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
extensions/           # Extension manifests (11 Extensions + Chrome extension)
```

## Commands

```bash
# Start server
zero-employee serve --reload        # Hot reload (port 18234)

# Chat mode (all providers, natural language for all operations)
zero-employee chat                  # Default settings
zero-employee chat --mode free      # Ollama / g4f mode
zero-employee chat --lang en        # English mode

# Chat mode slash commands (file ops & shell — Claude Code-like)
# /read <path>     Read a file (sandbox-checked)
# /write <path>    Write content to a file
# /edit <path>     View a file for editing
# /run <command>   Execute a shell command (30s timeout)
# /ls [path]       List directory contents
# /cd <path>       Change working directory
# /pwd             Show current directory
# /find <pattern>  Find files by glob pattern
# /grep <pat> [p]  Search file contents

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

## Version Management (Important)

**IMPORTANT: 8 version-bearing files exist. Always use the `bump-version` script when updating versions.**

| File | Format |
|------|--------|
| `pyproject.toml` (root) | `version = "X.Y.Z"` |
| `apps/api/pyproject.toml` | `version = "X.Y.Z"` |
| `apps/desktop/package.json` | `"version": "X.Y.Z"` |
| `apps/desktop/ui/package.json` | `"version": "X.Y.Z"` |
| `apps/edge/proxy/package.json` | `"version": "X.Y.Z"` |
| `apps/edge/full/package.json` | `"version": "X.Y.Z"` |
| `apps/desktop/src-tauri/tauri.conf.json` | `"version": "X.Y.Z"` |
| `apps/desktop/src-tauri/Cargo.toml` | `version = "X.Y.Z"` |

- Version update: `./scripts/bump-version.sh 0.2.0`
- The script updates all 8 files and verifies consistency
- CI (`check-metadata-sync` job) will fail if pyproject.toml files are out of sync
- When changing metadata, always update both pyproject.toml files simultaneously

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

### Language Extension Design

- The NSIS installer offers 6 language choices (en, ja, zh, ko, pt, tr)
- Only the installer-selected language is active by default
- Other languages (including remaining built-in 5 and new languages) are enabled via the language-pack extension system
- Language changes affect both UI display and AI agent output
- Some features require app restart after language change
- Additional languages beyond the built-in 6 can be loaded dynamically via API (`loadLanguagePack()`)
- Language pack API: `GET /api/v1/language-packs`, `POST /api/v1/language-packs/set`
- Extension manifest: `extensions/language-pack/manifest.json`

### CLI Design (Claude Code-like)

- `zero-employee chat` provides an interactive agent with file/shell operations
- Slash commands: `/read`, `/write`, `/edit`, `/run`, `/ls`, `/cd`, `/pwd`, `/find`, `/grep`
- File operations are sandbox-checked via `sandbox.py`
- Shell commands have a 30-second timeout and block dangerous patterns
- Natural language commands process file operations (FILE category in NL command service)
- Both CLI and Desktop/Web provide equivalent operational capabilities

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
13. **Registry safety**: All skill/plugin/extension create/install/import endpoints run `analyze_code_safety()` on manifest code. HIGH risk items are blocked unless `?force=true` is explicitly passed

Defense layers:
- Workspace isolation (`security/workspace_isolation.py`) -- No local/cloud connections by default
- Prompt injection defense (`security/prompt_guard.py`) -- 5 categories, 28+ patterns
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

## External Agent Framework Integration (Agent Adapter)

Like the browser adapter, external AI agent frameworks can be added/switched as plugins.
ZEO's AI organization can delegate sub-tasks to external frameworks while maintaining
approval gates, audit logging, and transparency.

- Agent adapter registry: `apps/api/app/tools/agent_adapter.py`
- Supported frameworks: CrewAI, AutoGen (Microsoft), LangChain, OpenClaw, Dify
- Plugin templates: `crewai-orchestrator`, `autogen-orchestrator`, `langchain-agent`, `openclaw-agent`, `dify-workflow`
- Installation: Natural language ("add CrewAI") or `POST /api/v1/browser-automation/plugins`
- Integration: External agents register with A2A communication hub
- Safety: All delegated tasks go through approval gates and audit logging

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
- Supported apps (34+): Obsidian, Notion, Logseq, Joplin, Anytype, Roam Research, Google Docs/Sheets/Drive/Calendar/Gmail, Microsoft 365/Teams/OneDrive/Outlook, Confluence, Jira, Linear, Asana, Trello, ClickUp, Slack, Discord, HubSpot, Salesforce, Figma, Canva, Airtable, Dropbox, GitHub, GitLab, n8n, Zapier, Make
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
(prerequisite-monitor, spec-contradiction, task-replay, judgment-review, plan-quality),
**language-packs** (list, current, set)

## Skill / Plugin / Extension

| Type | Role | Examples |
|------|------|---------|
| Skill | Single-purpose specialized processing | spec-writer, review-assistant, browser-assist |
| Plugin | Bundles multiple Skills | ai-secretary, ai-avatar, research |
| Extension | System integration and infrastructure | mcp, oauth, notifications, language-pack, obsidian, notion, logseq, joplin, google-workspace, microsoft-365, browser-assist (Chrome extension) |

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

## Desktop UI (Tauri v2 + React)

The desktop app follows a VSCode/Cursor-inspired IDE layout for AI orchestration.

### Layout Structure
- **Title Bar** -- App name, current page, version
- **Activity Bar** (left sidebar) -- Icon navigation with tooltips
- **Tab Bar** -- Current page tab
- **Main Content** -- Page content
- **Status Bar** -- App info
- **Command Palette** (`Ctrl/Cmd+K`) -- Quick search across all pages and actions

### Navigation (Activity Bar)
Dashboard, Org Chart, Secretary, Tickets, Approvals, Artifacts,
Health Monitor, Costs, Audit, Skills, Plugins, Extensions,
Marketplace, Brainstorm, Agent Monitor, Permissions, Settings

### Theme System
- 3 built-in themes: Dark (default), Light, High Contrast
- Theme selector in Settings
- All colors via CSS variables (`--bg-base`, `--accent`, etc.)
- Custom themes can be added via extensions

### Key Pages
- **Dashboard**: Command center with natural language input, quick actions, status grid
- **Settings**: Theme, Language, LLM API Keys (11+ providers with dropdown selector),
  Agent Behavior (autonomy level, browser automation, workspace access),
  Execution Mode, Company, Provider Connections (12+ with category filter), Policies
- **Skills/Plugins/Extensions**: Installed + Marketplace tabs, search, CRUD
- **Marketplace**: Unified view for community-created skills/plugins/extensions
- **Brainstorm**: Multi-model comparison with dropdown model selector + custom model input

### Agent Behavior (Settings)
- **Autonomy levels**: Observe / Assist / Semi-Auto / Autonomous
- **Browser automation**: Chrome control, Web AI sessions (API-free GPT/Gemini/Claude), site interaction (approval-gated)
- **Workspace access**: Local file access (opt-in), Cloud storage connections (opt-in)
- Default: Semi-Auto autonomy, internal storage only, all dangerous ops require approval

### i18n
- 6 built-in languages: ja, en, zh, ko, pt, tr
- Additional languages via extension language packs
- All UI strings use i18n keys (no hardcoded strings)

## Release Notes Guidelines

**GitHub Releases text must focus on system changes only.**

Write about:
- Security improvements (new defenses, hardened modules, vulnerability fixes)
- Deployment changes (Docker, infrastructure, production configuration)
- AI model catalog updates (new models, version changes, pricing)
- Internationalization (new languages, translation coverage)
- Platform features (new capabilities, API additions, orchestration improvements)

Do NOT write about:
- Documentation changes (typo fixes, wording improvements, accuracy corrections)
- CI/CD pipeline changes (GitHub Actions, workflow modifications)
- Repository configuration (Dependabot, linter settings, gitignore)
- Internal refactoring that does not change user-facing behavior

The audience is end users, not developers. Describe what changed in the system behavior, not what files were edited.
