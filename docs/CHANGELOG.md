# Changelog

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
