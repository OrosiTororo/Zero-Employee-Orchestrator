# Changelog

> [日本語](../CHANGELOG.md) | English | [中文](../zh/CHANGELOG.md)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-03-12 — Platform v0.1 (Consolidated Release)

### Security

- **bcrypt promoted to required dependency** — Removed SHA-256 fallback, enforcing bcrypt for password hashing
- **Rate limiting added** (`slowapi`) — Implemented rate limits on authentication endpoints (registration: 5/min, login: 10/min)
- **RAG file permissions fixed** — Restricted `index.json` / `idf.json` to `0o600` (owner only)
- **RAG input validation** — Added content size limit (10 MB) and metadata key count restriction
- **Authentication endpoint protection** — Added authentication to approval / config / registry APIs
- **CORS restriction hardening** — Changed wildcard to explicit method and header lists
- **UUID input validation** — Fixed to return 400 for invalid UUIDs

### Added

- **File Attachment-based Plan Creation** — Attach files to Design Interview and integrate into spec generation context
  - `POST /api/v1/tickets/{ticket_id}/interview/attach` — File upload
  - `GET /api/v1/tickets/{ticket_id}/interview/attachments` — List attachments
  - Supports text, code, images, and PDF (auto text extraction + multi-encoding support)
  - Extracted text automatically integrated into the "Reference Materials" section of Specs
- **Local Context Skill Image Support** — Image file reading (Base64 encoding + PNG/JPEG size detection)
  - Supports `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.svg`
  - SVG also parsed as text
  - 10 MB size limit
- **Extended File Type Support** — Significantly expanded supported formats for Local Context Skill
  - Code: `.tsx`, `.jsx`, `.java`, `.go`, `.rs`, `.c`, `.cpp`, `.h`, `.html`, `.xml`, `.css`, `.sql`, `.sh`
  - Multi-encoding auto-detection (UTF-8, Shift_JIS, EUC-JP, CP932)

- **Brainstorming (Sparring Partner) Feature** (`services/multi_model_service.py`, `api/routes/multi_model.py`, `pages/BrainstormPage.tsx`)
  - Brainstorm session management with AI advisors (create, message, search, archive)
  - Multi-model brainstorming support (use GPT / Gemini / Claude simultaneously)
  - Session types: brainstorm / debate / review / ideation / strategy
- **Multi-Model Comparison** (`services/multi_model_service.py`)
  - Send same input to multiple models and compare responses side-by-side
  - Per-model character count, token count, and latency measurement
  - Persistent storage and listing of comparison results
- **Conversation Memory** (`services/multi_model_service.py`)
  - Permanently store all conversations between users and AI organization
  - Keyword search across past conversations (supports user queries about past discussions)
  - Conversation statistics (total messages, characters, by role, by type)
- **Accurate Character Counting (TextAnalyzer)** (`services/multi_model_service.py`)
  - Unicode-aware character counting using Python's len()
  - Breakdown by hiragana, katakana, kanji, ASCII, digits
  - Character count validation (min/max length checks)
  - Text Analysis API: POST /text/analyze
- **Per-Role Model Settings** (`services/multi_model_service.py`)
  - Users can assign AI models to each agent role freely
  - Agent-specific settings with global fallback
  - Configurable fallback model, max_tokens, temperature, system prompt
- **Dynamic Agent Organization Management** (`services/agent_org_service.py`)
  - Add agents by preset roles (Secretary, Advisor, PM, Researcher, Engineer, etc.)
  - Create, list, and delete custom roles
  - Update agent roles (name, description, model, autonomy level, system prompt)
  - Remove agents (transition to decommissioned status)
- **Secretary & Advisor Role Definitions** (`services/agent_org_service.py`)
  - Secretary: Bridge between AI organization and user, knowledge repository, information management
  - Advisor: Sparring partner for brainstorming, multi-perspective advice, bridge between secretary and user
  - Each role has predefined system prompts
- **Natural Language Organization Management** (`services/agent_org_service.py`)
  - Submit requests to AI organization in natural language (e.g., "Add an advisor agent")
  - Keyword-based action and role auto-detection
  - Auto-execute mode (executes automatically when confidence is high)
  - Persistent storage and listing of feature requests
- **Frontend BrainstormPage** (`pages/BrainstormPage.tsx`)
  - Brainstorm session management UI (create, send/receive messages, search)
  - Multi-model comparison UI (model selection, input, side-by-side result display)
  - Per-role model settings UI (list configs, available roles)
  - AI organization management UI (natural language requests, role list, agent addition)
  - Real-time character count display
- **ZEO-Bench — Judge Layer Quantitative Evaluation Benchmark** (`tests/zeo_bench.py`)
  - 200-question test set for quantitative evaluation of Cross-Model Verification accuracy
  - 4 categories: Factual Accuracy (50), Contradiction Detection (70), False Positive (40), Correction Quality (40)
  - Numerical comparison of detection rate improvement vs single-model self-evaluation
  - `BenchmarkReport` with per-category breakdowns and summary
- **Cross-Model Verification Improvements** (`orchestration/judge.py`)
  - Semantic similarity checking (token-level Jaccard similarity)
  - Numeric tolerance comparison (within 5% considered matching)
  - Contradiction detection engine: negation patterns, numeric discrepancies, conclusion conflicts, temporal inconsistencies
  - Confidence-weighted scoring (weighted by number of agreeing models)
  - Detailed contradiction reporting (contradiction_details)
- **Generalized Domain Skill Templates** (`skills/builtin/domain_skills.py`)
  - ContentCreatorSkill — Content generation for any platform (blog, social media, email, video scripts, presentations)
  - CompetitorAnalysisSkill — Competitor analysis for any domain (market analysis, SWOT, pricing, feature comparison)
  - TrendAnalysisSkill — Trend analysis for any domain (market, technology, social media, industry trends)
  - PerformanceAnalysisSkill — Performance analysis for any business (KPI, ROI, conversion, engagement)
  - StrategyAdvisorSkill — Cross-domain strategic advisor (next actions, resource allocation, risk assessment)
  - All Skills support i18n (ja/en/zh) and Artifact Bridge compatibility
- **Enhanced Artifact Bridge** (`orchestration/artifact_bridge.py`)
  - auto_link_outputs_to_inputs: Automatic artifact linking within DAGs
  - Cross-domain transformation: e.g., trend_report → market_context automatic type conversion
  - Compatibility matrix: Auto-conversion rules between artifact types
  - find_compatible_artifacts: Search for compatible artifacts
  - build_artifact_pipeline: Design artifact flow through Skill chains
- **Self-Healing DAG Chaos Tests** (`tests/test_chaos_dag.py`)
  - 20+ fault injection test cases
  - Single node failures, cascade failures, parallel branch failures, full branch failures
  - Recovery success rate and recovery time benchmarks
  - Strategy effectiveness comparison (retry / skip / replan)
  - DAG integrity validation (orphan nodes, dependency resolution, completed node preservation)

### Fixed (post-release)

- CI workflow `claude-code-review.yml`: Fixed review skip handling for bot PRs (Dependabot, etc.)
- CI workflow `create-release.yml`: Fixed CHANGELOG path to `docs/CHANGELOG.md`
- Release workflow `release.yml`: Updated Tauri v2 build action and asset table to latest
- Frontend `ReleasesPage.tsx`: Added fallback display when GitHub Releases are not yet published
- Documentation reorganization: Restructured md files into `docs/` (user-facing) and `docs/dev/` (developer-facing)
- Security: Added Dependabot configuration, security check script, and pre-publish checklist

### Added

- **Runtime Configuration Management — API Key Setup Without .env** (`core/config_manager.py`, `api/routes/config.py`)
  - CLI commands `zero-employee config set/get/list/delete/keys` to configure API keys and execution modes
  - Web API `GET/PUT /api/v1/config` for in-app configuration changes
  - Added LLM API key input UI to the Settings page (SettingsPage)
  - Settings saved to `~/.zero-employee/config.json` (protected with file permission 600)
  - Priority order: Environment variables > config.json > .env > Default values
  - Sensitive value masking, provider connection status API
- **Knowledge Store — Persistent Memory for User Settings and File Permissions** (`orchestration/knowledge_store.py`)
  - File/folder operation permission memory (no need to re-ask during planning)
  - Business document folder location memory
  - User settings and preferences persistence
  - Change detection (diff detection and notification against previous information)
  - Knowledge API (`/knowledge/*`) — Store, search, and check for changes
- **Login-Free Anonymous Sessions**
  - Instantly start using the app with `POST /auth/anonymous-session`
  - Link account later (`POST /auth/link-account`)
  - Login enables state sharing across multiple devices
  - Frontend: Added "Start without logging in" button
- **Web Dashboard — Agent Monitoring** (`pages/AgentMonitorPage.tsx`)
  - Monitor agent status in real-time from the browser
  - 4 tabs: Running tasks, Sessions, Hypothesis verification, Error monitoring
  - 5-second auto-refresh
  - Sentry-integrated error statistics display
- **Permissions Management Dashboard** (`pages/PermissionsPage.tsx`)
  - File/folder permissions configuration UI
  - Business folder location registration UI
  - Change detection review UI
- **Sandbox Environment** (`worker/app/sandbox/cloud_sandbox.py`)
  - Multi-mode support: Local execution, Docker execution, Cloudflare Workers execution
  - Direct editing of local code (with permission checks)
  - JavaScript/TypeScript execution on Workers
  - One-click deploy to Cloudflare Workers
- **Rootless Container Support** (`Dockerfile`, `docker-compose.yml`)
  - Runs in containers without root privileges
  - Executes as non-root user (UID 1000)
  - All services launched together with Docker Compose
- **External Skill Import** (`integrations/external_skills.py`)
  - Search and import from GitHub Agent Skills repositories
  - Search and import from the skills.sh platform
  - Skill conversion from OpenClaw / Claude Code formats
  - Manifest retrieval from arbitrary Git repositories
  - `POST /skills/external/search` / `POST /skills/external/import`
- **MCP Server** (`integrations/mcp_server.py`)
  - Model Context Protocol compliant server implementation
  - 8 built-in tools (Tickets, Tasks, Skills, Knowledge, Audit, Monitoring, Hypothesis verification)
  - 4 resources (Dashboard, Agents, Skills, Knowledge)
  - 2 prompt templates
  - MCP API (`/mcp/*`)
- **Cloudflare Deployment Support**
  - Existing `apps/edge/full/` Workers app
  - One-click deploy with `deploy_to_workers()` method
  - Automatic wrangler.toml generation
- **AI Investigation Tool** (`integrations/ai_investigator.py`)
  - AI completes investigations by referencing logs and DB
  - Safe SELECT-only DB read queries
  - Audit log search, error pattern analysis, task execution history
  - System metrics retrieval
  - SQL injection prevention (prohibited keywords, SELECT statements only)
  - Investigation API (`/investigate/*`)
- **Sentry Integration** (`integrations/sentry_integration.py`)
  - Integration with Sentry SDK (built-in event store when SDK is unavailable)
  - Exception capture, message capture, performance transactions
  - Error statistics and event listing
  - Alert callback functionality
  - Sentry API (`/sentry/*`)
- **Human/AI Account Separation (IAM)** (`security/iam.py`)
  - Dedicated service accounts for AI agents
  - Separate permission scopes for human and AI accounts
  - Automatic exclusion of permissions prohibited for AI (secret reading, admin, approval)
  - Credential file protection (owner read-only permissions)
  - IAM API (`/iam/*`)
- **Parallel Hypothesis Verification Engine** (`orchestration/hypothesis_engine.py`)
  - Multi-agent hypothesis verification and review loop
  - Evidence support/refutation score calculation
  - Cross-review consensus determination
  - Hypothesis state management (Proposed -> Investigating -> Evidence -> Review -> Confirmed/Refuted)
  - Hypothesis API (`/hypotheses/*`)
- **Agent Session Management** (`orchestration/agent_session.py`)
  - Multi-round interactions with context preservation
  - Idle state waiting (with context retention) and resumption
  - Working memory (temporary in-session memory)
  - Hybrid DB persistence and in-memory storage
  - Session API (`/sessions/*`)

### Changed

- `core/config.py`: Added SENTRY_DSN, SANDBOX_MODE, CLOUDFLARE_ACCOUNT_ID, CREDENTIAL_DIR settings
- `main.py`: Added imports for new models (knowledge_store, agent_session, iam), added Sentry/MCP initialization
- `api/routes/__init__.py`: Added knowledge, platform routers
- `api/routes/auth.py`: Added anonymous session, account linking, optional authentication
- `shared/hooks/use-auth.ts`: Added isAnonymous state, startAnonymous/linkAccount methods
- `app/router.tsx`: Added PermissionsPage, AgentMonitorPage routes
- `shared/ui/Layout.tsx`: Added Agent Monitoring and Permissions Management navigation to sidebar
- `pages/LoginPage.tsx`: Added "Start without logging in" button

- **External Tool Integration Enhancements** (`tools/connector.py`)
  - Added CLI tool connection type (supports gws / gh / aws / gcloud / az and other CLI tools)
  - Added gRPC and GraphQL connection types
  - Added service account authentication type
- **Plugin GitHub Import Feature** (`integrations/external_skills.py`)
  - Direct search and import of plugins from GitHub repositories (`topic:zeo-plugin`)
  - Search and import from community plugin registry
  - `POST /api/v1/registry/plugins/search-external` — External plugin search
  - `POST /api/v1/registry/plugins/import` — Import plugins from GitHub
  - Users can share and publish plugins, enabling external service integration without additional developer work
- **Document Multilingualization** (USER_GUIDE.md, README.md)
  - USER_GUIDE.md: Support for 3 languages (Japanese, English, Chinese)
  - README.md: Releases section explained in 3 languages for non-engineers
  - Added download file selection guide
- **Legacy File Migration**
  - Integrated useful ideas from `ZPCOS_FEATURES_AND_IMPROVEMENTS.md` into existing documentation
  - Reflected meta-skill concepts, security self-testing, iPaaS integration ideas into DESIGN.md / FEATURES.md
  - Deleted legacy files

- Unified version notation to v0.1 across all documentation
- `CHANGELOG.md`: Consolidated all releases as v0.1
- `docs/FEATURES.md`: Added external tool integration and community plugin sections, added feature bloat review results
- `docs/FEATURE_BOUNDARY.md`: Added community plugin sharing policy, added v0.1 feature boundary review
- `ABOUT.md`: Unified to v0.1 notation, changed comparison targets to AI agents
- `docs/OVERVIEW.md`: Unified to v0.1 notation, updated screen count to 21, added feature bloat review
- `USER_GUIDE.md`: Corrected provider information for Method C (subscription mode), changed comparison targets to AI agents
- `README.md`: Added directory structure in three languages (Japanese, English, Chinese) to each section, updated to latest structure
- `DESIGN.md`: Updated screen count to 21, added integrations/ and security/IAM to directory structure
- `CLAUDE.md`: Added extension feature classification notes for integrations/ modules

### Changed — v0.1 Feature Boundary Review

The following features were reclassified from core features to extension features (bundled in the codebase, planned for future separation):
- `integrations/sentry_integration.py` -> Extension
- `integrations/ai_investigator.py` -> Skill
- `orchestration/hypothesis_engine.py` -> Plugin
- `integrations/mcp_server.py` -> Extension
- `integrations/external_skills.py` -> Extension

### Initial Implementation (Pre-release — 2026-03-09)

- Initial implementation of the 9-layer architecture
  - User Layer / Design Interview / Task Orchestrator / Skill Layer / Judge Layer / Re-Propose Layer / State & Memory / Provider Interface / Skill Registry
- FastAPI backend (`apps/api`)
  - REST APIs for authentication (OAuth PKCE), companies, agents, tickets, tasks, approvals, Heartbeat, and budget management
  - SQLAlchemy 2.x (async) + Alembic migrations
  - Multi-LLM gateway via LiteLLM Router
- React 19 + TypeScript frontend (`apps/desktop/ui`)
  - Dashboard, tickets, agents, and settings screens
  - Design system with shadcn/ui + Tailwind CSS
  - State management with TanStack Query + Zustand
- Tauri v2 desktop app (`apps/desktop`)
  - Windows (.msi / .exe), macOS (.dmg), Linux (.AppImage / .deb) support
- Orchestration engine
  - Dynamic task reconstruction via Self-Healing DAG
  - Two-stage Detection + Cross-Model Verification (Judge Layer)
  - Experience Memory + Failure Taxonomy
  - State machine-based execution management
- CI/CD pipeline
  - Automated linting, testing, and building via GitHub Actions
  - Multi-platform Tauri build & release
  - Cloudflare Workers deployment
- Documentation
  - README, DESIGN.md, MASTER_GUIDE.md
  - Implementation guides for each section (instructions_section2-7)

## Development History (Pre-release milestones, consolidated into v0.1.0)

## [0.5.0] - 2026-03-10 — Skills Management

### Added

- **Natural Language Skill Generation Engine** (`services/skill_service.py`)
  - Auto-generates manifest (skill.json) and execution code (executor.py) simply by describing skill functionality in natural language
  - LLM-based generation + template-based fallback (guaranteed operation even when LLM is unavailable)
  - Automatic safety check of generated code (16 types of dangerous pattern detection)
  - Safety report generation (risk_level: low/medium/high, permission requirements, external connection detection)
  - `POST /api/v1/registry/skills/generate` endpoint
- **Skill / Plugin / Extension Full CRUD API**
  - GET (list/individual) / POST (create) / PATCH (update) / DELETE (delete) support for all entities
  - Slug-based duplicate checking
  - Enable/disable toggle (`enabled` flag)
  - Filtering: status, skill_type, include_disabled
- **System Protected Skills Feature** (`is_system_protected`)
  - Protects 6 built-in skills essential for system operation
    - spec-writer, plan-writer, task-breakdown, review-assistant, artifact-summarizer, local-context
  - API-level rejection of protected skill deletion (HTTP 403)
  - API-level rejection of protected skill disabling (HTTP 403)
  - Automatic registration and protection flag setting of system skills at application startup
- **Plugin / Extension Management Service** (`services/registry_service.py`)
  - Plugin: Full CRUD + system protection + enable/disable toggle
  - Extension: Full CRUD + system protection + enable/disable toggle
  - Rejection of protected Plugin/Extension deletion and disabling
- **Frontend Skill Management UI** (`SkillsPage.tsx`)
  - Skill list display via API integration (real-time retrieval)
  - Skill enable/disable toggle
  - Skill deletion (system-protected skills shown as locked in UI)
  - System protection badge display
  - Search filter (name, description, slug)
- **Frontend Skill Generation UI** (`SkillCreatePage.tsx`)
  - Natural language input area (10-5000 characters, character counter)
  - Visual display of safety check results (pass/fail, risk level display)
  - Preview of generated manifest (JSON) and code (Python)
  - "Register Skill" button available after passing safety check
  - Detailed safety report display
- **Frontend Plugin Management UI** (`PluginsPage.tsx`)
  - List display via API integration
  - New plugin addition form
  - Enable/disable toggle and deletion (protected plugins shown as locked)
  - Search filter

### Changed

- **Skill / Plugin / Extension Models** (`models/skill.py`)
  - Added `is_system_protected` column (Boolean, default=False)
  - Added `enabled` column (Boolean, default=True)
  - Added `generated_code` column (Skill only, Text)
  - Added `unique=True` constraint on slug
- **Registry API** (`api/routes/registry.py`)
  - Complete rewrite from basic list/install to full CRUD + natural language generation
  - Changed to service layer routing (direct SQLAlchemy -> services.skill_service / registry_service)
  - Proper HTTP status codes (201 Created, 403 Forbidden, 404 Not Found, 409 Conflict)
- **Registry Schemas** (`schemas/registry.py`)
  - Added `SkillUpdate`, `PluginUpdate`, `ExtensionUpdate`
  - Added `SkillGenerateRequest`, `SkillGenerateResponse`
  - Added `RegistryDeleteResponse`
  - Added `is_system_protected`, `enabled` fields to all Read schemas
- **Application Startup** (`main.py`)
  - Added automatic registration of system-required skills at startup

## [0.4.0] - 2026-03-09

### Added

- **AI Avatar Plugin (Digital Twin AI)** (`plugins/ai-avatar/`)
  - Learns user's decision criteria, writing style, and values to build a profile
  - Integration with Judge Layer (provides user's judgment patterns as custom rules)
  - Proxy review, writing style reproduction, approval pattern learning
  - User profiles encrypted and stored locally
- **AI Secretary Plugin** (`plugins/ai-secretary/`)
  - Morning briefing (pending approvals, in-progress tasks, today's schedule)
  - Next action suggestions (recommended order based on urgency and importance)
  - Progress summaries, reminders, delegation routing
  - Briefing delivery via Discord / Slack / LINE Bot Plugin integration
- **LINE Bot Plugin** (`plugins/line-bot/`)
  - Ticket creation, progress checking, and approval operations via LINE Messaging API
  - Approval dialogs using Flex Messages
  - Quick operations via Rich Menu

### Changed

- **Discord Bot Plugin** updated to v0.2.0
  - Added in-thread conversations, briefing delivery, interactive buttons
  - Added integration with AI Secretary / AI Avatar Plugins
  - Defined `/zeo` slash command system
- **Slack Bot Plugin** updated to v0.2.0
  - Added in-thread conversations, briefing delivery, Block Kit interactions
  - Added integration with AI Secretary / AI Avatar Plugins
  - Defined `/zeo` Slash Command system
- **Full Documentation Update**
  - `USER_GUIDE.md`: Corrected LLM connection method priority recommendations (prioritizing Gemini free API / Ollama), added descriptions for AI Avatar, AI Secretary, and chat integrations, updated FAQ
  - `README.md`: Added new features (AI Avatar, AI Secretary, chat integrations) to Japanese, English, and Chinese sections, updated directory structure
  - `ABOUT.md`: Added AI Avatar, AI Secretary, and chat integration sections, updated LLM recommendations to latest
  - `docs/FEATURES.md`: Updated Plugin / Extension list to detailed tables, added additional features section
  - `docs/OVERVIEW.md`: Updated external tool integration section, added AI Avatar and AI Secretary descriptions
  - `docs/FEATURE_BOUNDARY.md`: Added AI agent extension Plugin and chat tool integration Plugin sections
  - `DESIGN.md`: Added AI Avatar, AI Secretary, and chat Bots to Plugin examples

## [0.3.0] - 2026-03-09

### Added

- **Dynamic Model Registry** (`providers/model_registry.py`)
  - External configuration file management of LLM models via `model_catalog.json`
  - Add, remove, deprecate, and specify successors for models without code changes
  - Automatic fallback for deprecated models (automatic switch to successor model via successor specification)
  - Provider health checks (periodic API availability verification)
  - Dynamic cost information updates
- **Model Registry API** (`/api/v1/models/*`)
  - Model listing, mode-specific catalog, provider health check
  - Model deprecation marking, cost updates, catalog reload
- `model_catalog.json` — Model catalog definition file (all models, modes, quality SLAs)
- **Observability — Reasoning Traces, Communication Logs, Execution Monitoring**
  - `orchestration/reasoning_trace.py` — Step-by-step recording of agent reasoning processes (19 step types, 4 confidence levels)
  - `orchestration/agent_communication.py` — Recording of all inter-agent communications (18 message types, thread management)
  - `orchestration/execution_monitor.py` — Real-time execution monitoring and WebSocket delivery
  - `api/routes/observability.py` — Observability API (reasoning traces, communication logs, monitoring dashboard)
  - Frontend TypeScript type definitions (ReasoningTrace, AgentMessage, ActiveExecution, etc.)

### Changed

- `gateway.py`: Changed from hard-coded model catalog to dynamic loading from ModelRegistry
- `cost_guard.py`: Changed cost table to dynamic generation from ModelRegistry
- `quality_sla.py`: Changed quality mode model lists to dynamic loading from ModelRegistry
- `docs/FEATURES.md`: Corrected old model names, added dynamic management description, added Observability section
- `CLAUDE.md`: Hard-coded model list -> dynamic management, added agent transparency to design principles

## [0.2.0] - 2026-03-09

### Changed

- Updated all old LLM model references to latest versions
  - g4f_provider.py: gpt-4o -> gpt-5.4, gpt-4o-mini -> gpt-5-mini, claude-haiku-4-5 -> claude-haiku-4-5-20251001
  - cost_guard.py: claude-haiku-4-5 -> claude-haiku-4-5-20251001
  - quality_sla.py: claude-haiku-4-5 -> claude-haiku-4-5-20251001
  - docs/BUILD_GUIDE.md: Updated all cost tables and quality mode settings to latest models
- DESIGN.md: Updated state transitions to implemented definitions, synced directory structure with actual codebase

### Added

- Repository layer (`repositories/`)
  - `base.py` — Generic CRUD repository base (BaseRepository)
  - `ticket_repository.py` — Ticket and thread DB operations
  - `audit_repository.py` — Audit log dedicated repository (append-only)
- Heartbeat module (`heartbeat/`)
  - `scheduler.py` — Heartbeat trigger types (9 types), execution management, action recording
- Policy module (`policies/`)
  - `approval_gate.py` — Automatic detection of dangerous operations and approval requests (12 categories)
  - `autonomy_boundary.py` — Boundary determination for autonomous execution vs. approval required
- Security module (`security/`)
  - `secret_manager.py` — Secure storage, masking, and rotation support for credentials
  - `sanitizer.py` — Automatic masking of secret values and personal information during storage/sharing
- Tool connection module (`tools/`)
  - `connector.py` — External tool connection management for MCP/Webhook/REST API, etc.
- Orchestration extensions (`orchestration/`)
  - `knowledge_refresh.py` — Knowledge Pipeline (7 stages), separated knowledge storage (5 types)
  - `artifact_bridge.py` — Cross-stage artifact handoff and version management
- Frontend type definitions (`shared/types/index.ts`)
  - TypeScript types for all entities corresponding to backend schema section 38

[0.1.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.1.0
[0.2.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.2.0
[0.3.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.3.0
[0.4.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.4.0
[0.5.0]: https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases/tag/v0.5.0
