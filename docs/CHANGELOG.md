# Changelog

## [v0.1.7-polish] (2026-04-20)

### Completeness — every EVALUATION_v0.1.7 deferred item landed

The v0.1.7 evaluation carried four "deferred" gaps. All of them close in
this release, at the quality level the evaluation asked for:

- **VS Code extension** (`extensions/vscode/`) — four commands (Open Chat,
  Create Ticket from Selection, Show Active Tickets, Engage Kill Switch),
  status-bar entry, strict-mode TypeScript, three configurable settings
  (`zeo.endpoint`, `zeo.autonomyLevel`, `zeo.showApprovalInStatusBar`).
  Does not bundle the daemon; expects `zero-employee serve` to be running
  and respects the operator's approval gate + audit trail unchanged.
- **Hyperagent + Comet agent bridges** — two new `AgentFrameworkAdapter`
  subclasses. Hyperagent routes via HTTP to a user-configured endpoint;
  Comet supports both API mode and browser-relay mode (queues the job so
  the user's own Comet extension approves and executes — ZEO never drives
  a remote browser it does not own).
- **AI CEO 5-skill YAML manifests** (`plugins/ai-ceo/skills/*.yaml`) plus
  a matching `plugin_skill_loader` service that reads each plugin's
  `skills/*.yaml`, validates required fields + security block, and
  reports `manifest.json` ↔ YAML drift so `/lint` surfaces dead slugs.
- **Dynamic Alembic head discovery** — `version_migration._discover_alembic_head()`
  walks `alembic/versions/*.py` and picks the revision that is no one
  else's `down_revision`. Falls back to a pinned constant when the
  directory is unreachable (pip-installed wheels without source). The
  stamp step registered in PR #333 now auto-tracks new revisions.

### Architecture — self_improvement 6-module split

`self_improvement_service.py` collapses from 1,332 → 55 lines. The six
skills (analyzer, improver, judge-tuner, failure-to-skill, A/B test,
auto-test-generator) plus the batch runner each get their own module under
`app.services.self_improvement/`. The original file remains as a
re-export facade so every `from app.services.self_improvement_service
import ...` still resolves — the package `__init__` is the preferred path
for new code.

### UI / UX — Claude-design-style polish

- New CSS tokens: spacing (`--space-1..8`), typography (`--text-xs..2xl`),
  motion (`--motion-fast/med/slow`, `--motion-ease`). Every new UI change
  is expected to draw from this palette rather than raw px values.
- `EmptyState` + `Skeleton` shared primitives. EmptyState always nudges
  the user toward a concrete next action; Skeleton fills the same box as
  the real component so dashboards don't reflow when data arrives.
- WCAG 2.2-compliant focus ring (2px accent, 2px offset) and `prefers-
  reduced-motion` override that collapses transitions + animations to
  near-zero.
- Keyboard-reachable skip-link at the top of `<Layout>`, translated across
  all six locales (`a11y.skip_to_main`).

### Tests

+46 new tests (AI CEO skill loader, Hyperagent / Comet adapters, dynamic
Alembic head, EmptyState, Skeleton, self-improvement package import
identity). Suite: 778 (merged) → 916 passing locally.

## [v0.1.7-final] (2026-04-17)

### Feature — Competitor-Parity Primitives (revision-3)

Five backends that close the feature gap with CrewAI / Dify / LangGraph / n8n /
Microsoft 365 tooling, all reachable from the desktop UI in one click and
wrapped in the existing approval gate + audit trail:

- **Workflow templates** (Dify-style) — `POST /workflow-templates/{slug}/instantiate`
  turns a preset DAG into a ticket with variable substitution; ships with five
  built-in templates (`research-brief`, `social-post`, etc.).
- **Crews** (CrewAI-style) — `POST /crews` spawns a multi-role agent team from
  a preset in one call; `POST /crews/{id}/dispatch` fans instruction out across
  members with per-role model tiering.
- **DAG node-result cache** (LangGraph-style) — `ZEO_DAG_CACHE=1` enables
  deterministic reuse of identical node outputs across runs;
  `GET /orchestration/cache/stats` exposes hit/miss/eviction counters.
- **Generic HTTP connector** (n8n-style) — `_sync_http_step` brings any REST
  API into the approval-gated connector layer without a new plugin. SSRF guard
  blocks RFC1918 / link-local / cloud-metadata targets.
- **Microsoft Graph adapter** — M365 mail / calendar / files / Teams under one
  Bearer token; tokens masked before any log call.

### Desktop UI

- **Templates page** (`/templates`) — preset gallery, variable-form
  instantiation modal, DAG preview, result card with ticket link.
- **Crews page** (`/crews`) — preset gallery (4 cards), spawn + dispatch
  modals, active-crew list with per-member status.
- **Sidebar** — "Templates" and "Crews" added under the Manage group.
- **Command Palette** — 5 new commands (navigate Templates / Crews,
  Instantiate Template, Spawn Crew, Browse Presets).
- **What's New** banner — v0.1.7 revision-3 bullets surfaced on first launch.
- **i18n** — keys added for all six locales (en, ja, zh-CN, ko, pt-BR, tr);
  all modals are `role="dialog"` with focus trap and Esc handler.

### Security

- Rate limits (`30/minute`) on template save/delete and crew spawn/dispatch.
- Templates and crews now scoped per `user_id`; cross-tenant read/delete
  eliminated.
- Prompt-injection scan on crew dispatch instructions.
- PII masking on user-supplied template name/description and crew name/
  instruction via `detect_and_mask_pii`.
- AuditLog rows written for `template.saved`, `template.deleted`,
  `crew.spawned`, `crew.dispatched`, `crew.disbanded`.

### Developer Experience

- **`ZEO_MOCK_LLM=1`** echo-provider — lets the golden path
  (template instantiate, crew dispatch, `/template`, `/crew`) run without
  Ollama or any external API key. Intended for demos + tests only; bypasses
  the LLM gateway's usual sanitize/observe pipeline.
- **CLI slash commands** — `/template <slug>` and `/crew <preset>` mirror the
  HTTP endpoints; `/help` documents them.
- **Actionable error messages** — 404/409 from templates and crews now point
  users at the relevant list endpoint.

---

## [v0.1.7] (2026-04-16)

### Feature — Karpathy-style Knowledge Wiki + arscontexta Context Engine

ZEO now ships a vendor-neutral, file-based knowledge layer that works fully
offline — no vector DB, no paid RAG service, no vendor lock-in.

- **`/ingest <source>`** — compiles a raw Markdown/text source into atomic
  wiki pages with `[[wikilinks]]`, updates the vault index, and rebuilds
  backlink maps (`services/wiki_knowledge_service.py`).
- **`/query <question> [--save]`** — keyword search over the vault, returns
  citations; `--save` persists the Q&A as a new concept page and triggers
  approval gate (`wiki_query_save` permission).
- **`/lint [--fix]`** — broken-link / empty-page / missing-backlink health
  check; `--fix` deletes empty pages and is gated on `wiki_lint_fix`.
- **`/ralph`** — arscontexta-inspired Record→Reduce→Reflect→Retrieve→Verify→
  Resync pipeline: sweeps `Inbox/` into atomic pages, rebuilds cross-links,
  writes a session report, archives processed notes to `ops/queue/`
  (`services/context_engine_service.py`).
- **`/plan <goal>`** — spec-then-execute plan mode; proposes a plan without
  running it (existing `spec` skill, wired from CLI).
- **HTTP endpoints** — `POST /wiki/ingest`, `POST /wiki/query`,
  `GET /wiki/lint`, `POST /wiki/context/setup`, `POST /wiki/context/ralph`;
  all go through sandbox path-boundary checks, `wrap_external_data()`, and
  PII masking (`api/routes/wiki.py`).
- **knowledge-wiki plugin** — bundles all five skills into a single
  installable plugin (`plugins/knowledge-wiki/manifest.json`).
- **Obsidian-compatible layout** — vault written as Self/Knowledge/Ops;
  any AI (Claude, Gemini, local Qwen) can read it; cross-AI portable.

### Feature — AI CEO Organizational Pattern

- **ai-ceo plugin** (`plugins/ai-ceo/manifest.json`) — maps the
  Owner→CEO→CMO/CTO/COO delegation pattern onto ZEO subagents, with
  per-role model tiering (Opus for strategic planning, Sonnet for
  execution, Haiku for batch/reporting). All sub-CEO actions pass through
  the approval gate and audit log.

### Feature — Cross-Version Upgrade Ladder

- **`zero-employee upgrade`** CLI subcommand — walks a hand-written
  migration ladder (`core/version_migration.py`) so users on any pre-v0.1.3
  install can jump straight to the current schema. Additive-only (no data
  loss), fully idempotent, uses semver-max bookmarking to survive fast
  hardware where timestamps collide.
- Four ladder steps: `0.0.0→0.1.3` (knowledge store, approvals, audit),
  `0.1.3→0.1.5` (widen operator profile columns), `0.1.5→0.1.6` (MCP
  tool-registration table), `0.1.6→0.1.7` (wiki/context-engine scaffolding).

### Tests

- **8 new tests** — `test_wiki_knowledge_service.py` (5 tests: ingest,
  query/save, lint/fix, ralph pipeline, setup idempotency) and
  `test_version_migration.py` (3 tests: fresh-DB recording, idempotency,
  table-name stability).

---

## [v0.1.6] (2026-04-10)

### Feature — Full Model Context Protocol (MCP) server

Zero-Employee Orchestrator now ships a spec-compliant MCP server so
Claude Desktop, Cursor, Continue and any other MCP-aware client can
drive ZEO natively — no custom glue code.

- **JSON-RPC 2.0 transport** — new endpoint `POST /api/v1/mcp/rpc`
  implementing `initialize`, `ping`, `tools/list`, `tools/call`,
  `resources/list`, `resources/read`, `prompts/list`, `prompts/get`,
  `logging/setLevel`, notifications, and JSON-RPC batch requests
  (`integrations/mcp_server.py`, `api/routes/platform.py`).
- **Streaming transport** — new endpoint `GET /api/v1/mcp/sse` emits
  Server-Sent Events for push notifications and heartbeat.
- **stdio transport** — new `zero-employee mcp serve` subcommand runs
  the MCP server over stdin/stdout using newline-delimited JSON-RPC so
  Claude Desktop, Cursor and Continue can be pointed at ZEO with a
  `{"command": "zero-employee", "args": ["mcp", "serve"]}` config block
  instead of an HTTP proxy.
- **MCP protocol 2025-11-25** — `initialize` advertises the latest
  spec revision and negotiates down to `2024-11-05` if a client asks
  for the older version. Tools expose the new `annotations` object
  (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `title`) so
  hosts can render safety affordances before invoking destructive
  actions (`create_ticket`, `execute_skill`, `propose_hypothesis`).
- **`logging/setLevel` method** — clients can adjust the server-side
  logging level at runtime; unknown levels return a clean error
  payload instead of raising.
- **14 built-in MCP tools** — tickets, tasks, skills, knowledge,
  audit, agent status, kill-switch status, autonomy level,
  Cost Guard budget, approval queue, hypothesis proposal, and
  `get_server_info` (up from 8 in v0.1.5). All 14 now carry
  annotation metadata.
- **6 built-in resources** (dashboard, agents, skills, knowledge,
  kill-switch, autonomy) and **3 built-in prompts** (task planning,
  code review, security audit).
- **Dynamic server version** — `MCPServer.get_server_version()` reads
  the version from `importlib.metadata` or `pyproject.toml` instead
  of a hard-coded string, so the MCP `initialize` handshake always
  matches the running build.
- **CLI integration** — new `zero-employee mcp` subcommand with
  `info`, `tools`, `call`, and `serve` actions. All three read
  subcommands honor `--json` for clean scripting output, and
  `mcp tools` prints the annotation hints inline. `mcp serve`
  suppresses the banner so stdout stays a clean JSON-RPC channel.
- **25 MCP tests** — `apps/api/app/tests/test_mcp_server.py` covers
  every JSON-RPC method (including `logging/setLevel`), tool
  annotations, protocol-version negotiation, prompt rendering with
  missing arguments, invalid top-level payloads, and a full stdio
  transport round-trip with an in-memory reader/writer. Total test
  count: **631 passing, 0 failing** (up from 467 in v0.1.5 final2,
  +164).
- **Response-model fix** — `MCPCapabilitiesResponse` now declares
  `tools: list[str]` instead of `list[dict]`, unblocking the previously
  broken `GET /api/v1/mcp/capabilities` endpoint.

### Feature — AI Team Role Definitions

`skills-engineer.md` and `construction-engineer.md` at the repo root
have been rewritten from standalone Japanese blog posts into
ZEO-specific English role definitions:

- **Skills Engineer** — owns persona contracts in `SKILL.md`; ships a
  canonical 6-section template (Persona, Inputs, Outputs, Tone & Style
  Rules, Forbidden Actions, Escalation Policy) and a pre-merge
  checklist.
- **Construction Engineer** — owns DAG topology, judge pairs, approval
  placement, cost envelopes, kill-switch predicates, and chaos tests;
  ships a "ZEO Construction Architect" prompt template for any
  MCP-aware planning client.

The two roles are explicit counterparts: personas vs. topology, with
neither editing the other's files. Both documents are now the source
of truth for how human engineers (and the ZEO self-improvement loop)
extend the platform.

### Fix — Documentation drift since v0.1.5

- `CLAUDE.md` — endpoint count corrected from 402 to **408** and the
  MCP integration line now reflects 14 tools + JSON-RPC 2.0 + stdio.
- `CLAUDE.md` — skill count drift corrected from the stale
  "11 Skills (6 system + 5 domain)" claim back to the runtime-verified
  **8 built-in skills (all system-protected)**. README's directory
  map received the same fix.
- `CLAUDE.md` — latest-evaluation pointer updated to
  `docs/dev/EVALUATION_v0.1.6_mcp.md`.
- `/.well-known/agent.json` — A2A agent card version bumped
  0.1.5 → 0.1.6 so agent discovery reports the real build.
- `README.md` — MCP row in the feature table rewritten to mention the
  new JSON-RPC endpoint and compatible clients.

### Release notes — see `docs/releases/v0.1.6.md`

## [v0.1.5] (2026-04-09)

### Fix — Operator Profile broken in Docker / root-user deployments

The sandbox's default denied list (`/root`, `/etc/*`, etc.) took precedence
over explicitly-whitelisted sub-directories. Because the Operator Profile
module stores data under `~/.zero-employee/`, any deployment running as root
(the Docker image default) returned **403 Forbidden** on every
`GET/PUT /operator-profile/profile` and `/operator-profile/instructions`
call, silently breaking the "About Me + Global Instructions" feature.

- `security/sandbox.py` — `check_access()` now evaluates the explicit
  whitelist first. Directory-level denies (`/root`, `/etc/shadow`, ...) are
  bypassed when the target is inside an `add_allowed_path()` directory.
  Filename-pattern denies (`.env`, `.key`, `id_rsa`, `credentials.json`, ...)
  continue to apply inside whitelisted directories, so secrets cannot be
  smuggled in by opt-in whitelisting.
- `security/sandbox.py` — Default denied entries for home dotfiles corrected
  from the literal `/.ssh`, `/.gnupg`, `/.aws`, `/.config/gcloud`, `/.azure`
  (which only matched the non-existent filesystem-root variants) to `~/.ssh`,
  `~/.gnupg`, `~/.aws`, `~/.config/gcloud`, `~/.azure` — these are now
  expanded through `Path.expanduser()` so the effective service user's home
  secrets are actually protected (previously relied on the filename patterns
  `id_rsa`, `credentials.json`, etc. for partial coverage only).
- `tests/test_security.py` — New regression test
  `test_explicit_whitelist_overrides_directory_deny` covering:
  whitelisted sub-dir under `/root` allowed; non-whitelisted siblings denied;
  filename-pattern denies (`.env`, `id_rsa`) still applied inside whitelist.

### Doc sync — Endpoint count corrected to 402

Authoritative count from the live `/api/v1/openapi.json` output is 402 (398
from `@router` decorators across 46 route modules + 4 from `main.py`:
`/healthz`, `/readyz`, `/.well-known/agent.json`, `/`). Previous docs
undercounted.

- CLAUDE.md: `398 endpoints` → `402 endpoints`
- ROADMAP.md: `397 endpoints, 23 orchestration modules` → `402 endpoints, 24 orchestration modules`
- docs/guides/architecture-guide.md: `397 endpoints` → `402 endpoints`
- docs/dev/POSITIONING.md: `397 endpoints` → `402 endpoints`

### New — Copilot Cowork-Inspired Task Management

Dispatch system enhanced with features inspired by Microsoft Copilot Cowork and Claude Cowork:

- **Plan Preview**: `preview_only=true` generates execution plan without running; user reviews steps then approves via `POST /dispatch/{id}/start`
- **Needs Input Checkpoint**: Tasks auto-detect when LLM needs human input, pause with `needs_input` status and a reason message; resume via `POST /dispatch/{id}/resume`
- **Mid-Execution Steering**: `POST /dispatch/{id}/steer` adds instructions to redirect a running task without cancelling
- **Rich Approval Preview**: Approval responses now include `preview` field (human-readable impact description) and risk-level color badges
- **CLI Task Management**: New slash commands in chat mode: `/dispatch`, `/tasks`, `/status`, `/approve`, `/reject`, `/cancel`
- **DispatchPage Redesign**: Expandable task cards, Active/Done/All tabs, plan step display, steering input, resume input, status badges

### New — ZEO Positioning Document

- `docs/dev/POSITIONING.md` — Defines ZEO's identity as meta-orchestrator vs desktop agents (Claude Cowork) and enterprise graph agents (Copilot Cowork)
- Adopted features (採長補短) matrix with rationale
- Browser Assist roadmap (4 phases)
- GUI/CLI/Web integration strategy

### Endpoint Count Update

- 3 new dispatch endpoints: `/dispatch/{id}/steer`, `/dispatch/{id}/resume`, `/dispatch/{id}/start`
- Total: 46 route modules, **397 endpoints** (394 routes + 3 main.py)

---

## [v0.1.5-pre] (2026-04-07)

### New — End-to-End Task Execution Engine

The core task execution engine is now implemented. Tasks can be planned and executed end-to-end:

- **`POST /tickets/{id}/execute`** — Generate plan, execute all steps via LLM, verify with Judge, return results
- **`POST /tickets/{id}/generate-plan`** — Generate execution plan (DAG) from ticket spec
- **`executor.py`** — Central orchestration engine connecting all 9 layers:
  Interview → DAG plan generation → LLM execution → Judge verification → Reproposal on failure
- **Dispatch now executes** — Background tasks route through the execution engine (not just ticket creation)
- **Repropose layer** — Real failure classification with plan diffs and confidence scoring
- **Autonomy boundary** — `execute` added to autonomous operations set

### Security & Stability

- Thread safety: Added `threading.Lock()` to in-memory stores (`_dispatch_tasks`, `_file_store`)
- Fixed PII detection API usage in dispatch (`has_pii` not `detected`)

### Fix — Desktop Auto-Update System

The desktop auto-update was completely non-functional for users who installed v0.1.2–v0.1.4. Three root causes identified and fixed:

- **[CRITICAL] Release workflow jq bug** — `latest.json` platforms object was always empty due to operator precedence error in the `merge-updater-json` job. No platform entries → updater found nothing → silent failure.
- **[CRITICAL] CSP blocking updater** — `connect-src` only allowed `api.github.com` but the updater endpoint is on `github.com`. Added `github.com` and `objects.githubusercontent.com`.
- **Auto-download & install** — Previously required manual click on "Download & Restart" banner. Now automatically downloads and installs updates by default (user-configurable toggle in Settings).

### Desktop Updater Improvements

- Initial update check reduced from 30s → 5s
- Periodic recheck interval reduced from 4h → 1h
- Added window-focus recheck (minimum 5 min interval)
- Update banner now shows download/install progress with i18n (6 languages)
- Dismiss no longer permanently hides the update
- New auto-update ON/OFF toggle in Settings page

### Release Workflow Hardening

- Platform validation changed from `::warning` to `exit 1` (broken `latest.json` no longer uploads)
- Added macOS to platform validation (was only checking Linux + Windows)
- Updater fragment upload changed from `if-no-files-found: ignore` to `error`
- Added empty platforms check before per-platform validation

### Documentation Sync

- Fixed route count: 46 → 47 across README, CLAUDE.md, 6 translated READMEs, FEATURES.md, OVERVIEW.md, architecture guide
- Fixed endpoint count: 387 → 396 (verified by counting @router decorators + main.py endpoints)
- Fixed skill count: 8 → 11 → 8 (6 system + 2 domain; domain-skills and browser-assist are the 2 domain skills)
- Fixed `common.version` stuck at v0.1.2 in all 6 i18n locale files
- Updated `bump-version.sh` to also update locale files and WhatsNew.tsx (prevents version drift)

### Audit & Corrections (v0.1.5 continued)

- **Endpoint count corrected**: 433 → 394 across CLAUDE.md, FEATURES.md, architecture-guide.md, REVIEW.md
- **CRITICAL FIX: Judge severity bug** — LLM gateway errors (e.g. missing API key) returned `CompletionResponse(content="Error: ...")` which passed Judge quality check with `severity="warning"` (score 0.95 > threshold 0.6). Changed `no_error_response` rule severity to `"error"` and added `JudgeVerdict.FAIL` check to executor. Tasks now correctly fail when LLM call fails.
- **Frontend /approvals path mismatch** — DashboardPage and AgentMonitorPage called non-existent `/approvals?status=requested` instead of `/companies/{cid}/approvals`. Fixed to use correct company-scoped path.
- **TicketDetailPage error display** — Error messages in execution output (starting with "Error:") now render in red text instead of default color
- **Orchestration module count corrected**: 22 → 23
- **Model family count corrected**: 26 → 24 in README.md (verified from model_catalog.json)
- **ROADMAP version corrected**: v0.1.4 → v0.1.5
- **DAG parallel execution**: Independent nodes now execute concurrently via `asyncio.gather`
- **Frontend error handling**: Replaced 16 silent `.catch(() => [])` with `console.warn` logging
- **Python 3.11+ support**: Lowered minimum requirement from 3.12 to 3.11, added CI matrix testing
- **CI matrix testing**: Added Python 3.11 to lint-and-test matrix
- **E2E test added**: `test_e2e_ticket_execution.py` — full ticket create → execute → verify flow
- **Evaluation corrected**: v0.1.5 evaluation contained false claims about stub implementations; corrected in `EVALUATION_v0.1.5_corrected.md` (5.8 → 6.3)

### v0.1.5 Final Audit & Release

- **Model family count corrected**: 24 → 22 in README.md (verified: 22 active + 4 deprecated = 26 total entries in model_catalog.json)
- **Route module count corrected**: 47 → 46 across README, CLAUDE.md, 6 translated READMEs, FEATURES.md, OVERVIEW.md, ROADMAP.md, architecture guide (47 was counting `__init__.py`)
- **eslint peer dependency conflict fixed**: Downgraded eslint 10.x → 9.x and eslint-plugin-react-hooks 7.x → 5.x to resolve `npm install` failure without `--legacy-peer-deps`
- **12 eslint errors resolved**: Removed unused catch variables in SecretaryPage, OrgChartPage, InterviewPage; fixed unused `_configLoading` and empty catch block in SettingsPage
- **Hono version aligned**: edge/full ^4.12.10 → ^4.12.11 (matching edge/proxy)
- **Full verification**: 497 tests pass (26 files), ruff lint clean, tsc clean, vite build clean, eslint 0 errors, server starts successfully

## [v0.1.4] (2026-04-07)

### Cowork-Style Transition (Complete)

- **All VSCode/VS Code references removed** from codebase (code, docs, CSS, comments)
- CSS variable `--bg-activity-bar` renamed to `--bg-nav-bar`; `ActivityBarDivider` → `NavBarDivider`
- Theme names changed: "Dark (VSCode Default)" → "Dark Default"
- Plugin/extension docstrings updated to Cowork terminology

### New — Operator Profile Page

- **OperatorProfilePage** — dedicated UI for About Me + Global Instructions
- Two-tab layout: profile fields (role, team, responsibilities, priorities, work style) and instruction editor
- Connected to existing `/operator-profile/` API endpoints
- Added to nav bar as bottom item with UserCircle icon

### New — Welcome Tour

- **WelcomeTour** — 3-step overlay for first-time users
- Step-by-step introduction: Dashboard → Monitor → Autonomy Dial
- Shows once per user (localStorage), dismissible, inspired by Claude Code quickstart

### New — "What's New" Banner

- **WhatsNew** — version-aware banner on Dashboard
- Shows key highlights per version, dismissible, inspired by Claude Code release notes

### Documentation

- All 6 translated READMEs synced (added Claude Cowork, Operator Profile, Task Dispatch)
- Fixed count discrepancies: zh-TW tools 19→21, pt-BR routes 41→46
- New evaluation: `EVALUATION_v0.1.3.md` — 7.7/10 with concrete fix proposals
- ROADMAP updated to v0.1.4

## [v0.1.3] (2026-04-07)

### Meta-Orchestrator Identity

ZEO is now positioned as **the AI meta-orchestrator** — orchestrate orchestrators, unify every AI framework and tool under human approval, audit trail, and security. Connect CrewAI, AutoGen, LangChain, Dify, n8n, Zapier, and 34+ business apps under one platform.

### Task Dispatch (Background Execution)

- **POST /dispatch** — Fire-and-forget background tasks with automatic ticket creation
- **GET /dispatch/{id}** — Poll task status (queued → running → completed)
- **DispatchPage** — Full UI with task input, status list, cancel, 10s auto-refresh
- Activity bar and status bar show live dispatch count

### Operator Profile & Global Instructions

- **PUT/GET /operator-profile/profile** — Persistent user context (role, team, priorities, work style) for AI personalization across sessions
- **PUT/GET /operator-profile/instructions** — Global instructions injected into every AI conversation
- Stored in ~/.zero-employee/ with 0o600 permissions

### Role-Based Plugin Packs (6 new)

Pre-configured plugin bundles per business role, each with manifest + runtime handler:

- **Sales Pack** — Lead scoring, competitive analysis, CRM sync, pipeline reports, outreach drafting
- **Finance Pack** — Expense analysis, budget tracking, invoice processing, financial reporting
- **HR Pack** — Job description drafting, resume screening, onboarding checklists, survey analysis
- **Legal Pack** — Contract review, clause extraction, compliance checking, NDA drafting
- **Marketing Pack** — Content calendar, SEO analysis, social scheduling, campaign tracking
- **Customer Support Pack** — Ticket triage, FAQ auto-response, escalation routing, sentiment analysis

Plugins: 10 → 16. Plugin development guide added (docs/dev/PLUGIN_GUIDE.md).

### Enterprise SSO & Compliance

- **SSO/SAML** — GET /sso/providers (Google OAuth, SAML 2.0, Okta, Azure AD), SAML metadata/ACS endpoints
- **Compliance API** — GET /compliance/frameworks (GDPR, HIPAA, SOC 2, CCPA, ISO 27001, FedRAMP), data retention policies, audit export (JSON/CSV)

### Browser Automation — Tiered Approval Model

10-level operation classification following Claude Cowork's tool hierarchy:

| Level | Operations | Risk |
|-------|-----------|------|
| LOW | navigate, screenshot | Safe — autonomous OK |
| MEDIUM | extract_data, click | Approval required |
| HIGH | type, fill_form, submit, download | Approval required |
| CRITICAL | login, payment | Always requires approval |

- Natural language instruction classifier with negation handling ("don't click" → navigate)
- Web AI sessions now require approval (was bypassed)
- Browser consent persisted to disk (survives restart)

### Desktop Auto-Update Fix

- **release.yml**: releaseDraft false (was true, making updates invisible)
- **use-updater.ts**: 4-hour periodic re-check (was one-time at startup)
- **latest.json merge job**: Prevents macOS entries from being lost in matrix build race conditions

### UI Improvements

- **Progressive disclosure sidebar** — 6 core items always visible, Manage (6 items) and Extend (4 items) collapsed by default with auto-expand
- **Autonomy Dial** — Status bar control cycling Observe/Assist/Semi-Auto/Autonomous, connected to backend config API
- **Interactive welcome tour** — 4-step onboarding (Describe task → Meet Secretary → Review & approve → Customize)
- **Actionable error messages** — All catch blocks across 5 pages replaced with toast notifications guiding users to resolution

### Security Hardening

- **Sandbox path boundary** — startswith() checks now include "/" separator, preventing /data/work-archive bypassing /data/work
- **PII Guard SSN** — Keyword context required (SSN, social security, 社会保障番号), bare numbers no longer false-positive
- **Prompt Guard** — System override and role hijacking correctly blocked
- **Auth enforcement** — themes, app-integrations endpoints now require authentication
- **Approval categories** — 12 → 14 (added BROWSER_AUTOMATION, WEB_AI_SESSION)

### Infrastructure & CI

- ci.yml: $GITHUB_WORKSPACE instead of hardcoded runner path
- deploy-api.yml: flyctl-actions pinned to v2 (was @master)
- deploy-workers.yml: Node.js 20 → 22
- release.yml: artifact actions v7/v8, latest.json merge job
- Docker: pnpm 9 → 10
- .env.example: 7 missing config variables added

### Documentation

- **CLAUDE.md rewritten** — 553 → 142 lines, mandatory post-change md sync rule
- **All 6 translated READMEs synced** (ja/zh-CN/zh-TW/ko/pt-BR/tr)
- **Evaluation report** — 8.3/10 with search-verified competitive analysis and Claude Cowork comparison

## v0.1.2 (2026-04-06)

### Changed — UI Redesign (Cowork-style + MIT palette)

- **MIT-licensed dark palette colors** — All GUI colors replaced with MIT-licensed values. Custom gradients, shadows, and glow effects removed entirely.
- **Code splitting** — Lazy-loaded 20 page routes into 42 separate chunks. Main bundle reduced from 749KB to 388KB (48% reduction).
- **Login page simplified** — Removed custom left-panel branding. Form-only centered layout.
- **Empty state improvements** — Pages with no data now show icons and navigation links to the Dashboard.
- **Welcome guide** — First-launch banner on Dashboard with quick-start actions (6 languages).

### Added — Theme Extension API

- `POST /api/v1/themes/register` — Extensions can register custom themes with CSS variable overrides.
- `GET /api/v1/themes` — List all available themes (built-in + extension-provided).
- `POST /api/v1/themes/set` — Switch active theme by slug.

### Added — CLI Neovim-Inspired Modes

- **NORMAL mode** — Standard input with slash commands. Green prompt.
- **INSERT mode** — Multi-line input via `"""`. Blue prompt.
- **COMMAND mode** — During slash command execution. Yellow prompt.
- **Status line** — Neovim lualine-style: `NORMAL │ provider │ ctx:%    lang │ mode │ ●`

### Fixed — Authentication

- **Token auto-refresh** — 401 interceptor retries with refreshed token. Periodic refresh every 4 hours. Anonymous sessions no longer expire unexpectedly.

### Fixed — Plugin/Extension Registry

- **Built-in seeding** — 16 plugins and 11 extensions seeded on server startup.
- **API client migration** — All registry pages use centralized API client with auth headers and correct Tauri URLs.

---

## v0.1.1 (2026-03-29)

### Added — Desktop UI Overhaul

- **Theme system** — 3 built-in themes: Dark (default), Light, and High Contrast. All UI colors use CSS variables, enabling full theme switching from Settings without restart.
- **Command Palette (Ctrl/Cmd+K)** — Instant search across all pages and actions. Keyboard-navigable with arrow keys, Enter to execute, ESC to close.
- **Marketplace page** — Unified view for browsing and installing community-created Skills, Plugins, and Extensions. Tab filtering by type, search bar, and install buttons.
- **Extensions page** — Dedicated page for managing extensions (language packs, themes, tool integrations) with Installed and Marketplace tabs.
- **Dashboard quick actions** — One-click action cards for common workflows: Research, Report, Automate, Analyze. Each populates the input field with an example prompt.

### Added — AI Agent Capabilities

- **External agent framework integration** — ZEO can now delegate tasks to external AI agent frameworks installed as plugins: CrewAI, AutoGen (Microsoft), LangChain, OpenClaw, and Dify. Install via natural language ("Add CrewAI") or the Plugin system.
- **Agent behavior settings** — New Settings section for controlling AI agent autonomy:
  - **Autonomy level**: Observe (read-only) / Assist (suggestions) / Semi-Auto (execute after approval) / Autonomous (auto-execute within safe boundaries)
  - **Browser automation**: AI can control Chrome to use web-based GPT/Gemini/Claude without API keys, fill forms, and interact with sites (dangerous operations require approval)
  - **Workspace access**: Local file access and cloud storage connections (both opt-in, off by default)
- **Social media auto-posting** — AI agents can create and publish content to 6 platforms: Twitter/X, Instagram, TikTok, YouTube, LinkedIn, and Threads. All posting requires human approval.
- **Video editing tools** — Added Runway ML, Pika, CapCut, and Descript integrations for AI-powered video generation and editing.

### Added — Platform Features

- **11 LLM providers** — Expanded from 4 to 11 pre-configured providers: OpenRouter, OpenAI, Anthropic, Google Gemini, DeepSeek, Mistral, Cohere, Groq, Together AI, Perplexity, xAI (Grok). Users select which to show via a dropdown picker and can still add custom providers.
- **12 service connections with category filter** — Expanded from 4 to 12: OpenRouter, Google Workspace, GitHub, GitLab, Slack, Discord, Notion, Obsidian, Jira, Linear, n8n, Zapier. Filterable by category (AI, Productivity, Development, Communication, Automation).
- **Marketplace publish flow** — Users can now publish their created Skills, Plugins, and Extensions to the marketplace. Full flow: Create → Publish → Review → Approve → Install by others → Rate and review.
- **Natural language SNS commands** — The NL command processor now recognizes social media posting intents in both Japanese and English (e.g., "Twitterに投稿して", "Post to Instagram").
- **55+ tool integrations across 21 categories** — Including new Social Media (6 tools) and Video Editing (4 tools) categories.

### Changed — UI Consistency & Accessibility

- **All pages use i18n** — Every page now uses translation keys instead of hardcoded strings. Approvals, Audit Log, Cost Management, and Health Monitor pages have been fully converted.
- **All pages use CSS variables** — Hardcoded color values replaced across all pages, enabling theme switching to work globally.
- **Semantic HTML** — Layout uses `<header>`, `<nav>`, `<main>`, `<footer>` instead of generic `<div>`. Added `aria-label`, `aria-current`, `aria-pressed`, `role="tooltip"`, `role="tablist"` throughout.
- **Health Monitor** — Renamed from "Heartbeats" with added description explaining its purpose (periodic system health checks with auto-notification on anomalies).
- **Skills/Plugins pages** — Removed version badges (v0.1), added My Skills/Marketplace tabs to separate user-created from community items.
- **Brainstorm page** — Complete rewrite with dark theme, dropdown model selector replacing checkboxes, custom model ID input, removed English subtitle duplication.

### Security

- **Red-team self-testing strengthened (8 categories, 22 tests)** — All test handlers now execute real adversarial payloads against actual security modules. Covers prompt injection, data leakage, privilege escalation, PII exposure, unauthorized access, sandbox escape, rate limit bypass, and auth bypass.
- **Sandbox symlink attack hardening** — Detects and blocks access when resolved paths point outside whitelisted directories.
- **Data Protection password matching fix** — Case-insensitive matching for PASSWORD/Password/password variants.
