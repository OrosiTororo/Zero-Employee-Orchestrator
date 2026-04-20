# Roadmap

> Last updated: 2026-04-20
> Current version: v0.1.7 (polish)

---

## Current State (v0.1)

v0.1 includes all features originally planned for v0.2 through v1.0, implemented ahead of schedule.

### Implemented in v0.1

**Foundation:**
- Full 9-layer architecture (24 orchestration modules, 27 services)
- ZEO-Bench, Self-Healing DAG, Experience Memory, AI Self-Improvement
- 51 API route modules, 428 endpoints
- 14 security defense layers

**Connectivity:**
- Tool Connector (REST/MCP/GraphQL/CLI/Webhook), iPaaS (n8n/Zapier/Make)
- Artifact Export, User Input Requests, Resource Import, File Upload API
- E2E Test Framework, LLM Response Mocking

**AI Organization:**
- Meta-Skills (Feeling/Seeing/Dreaming/Making/Learning)
- AI Repurpose Engine, RSS/ToS Monitor, A2A Communication, Avatar Co-evolution
- Secretary AI, Browser Assist, Media Generation (5 types)
- 45+ AI tool integrations across 19 categories

**Ecosystem:**
- Skill/Plugin/Extension Registry with marketplace service
- Natural language skill generation (16 safety checks)
- Browser Automation (Playwright + plugin adapters)
- 34+ app integrations via App Connector Hub

**Desktop UI (Tauri v2 + React):**
- Cowork-style task-first layout with nav sidebar + progressive disclosure
- Autonomy Dial (Observe/Assist/Semi-Auto/Autonomous)
- Dispatch background task feed in status bar
- Operator Profile (about-me + global instructions)
- 3 themes (Dark/Light/High Contrast)
- Command Palette (Ctrl/Cmd+K)
- Marketplace page (Skills/Plugins/Extensions unified view)
- Agent behavior settings (autonomy, browser, workspace access)
- 6 built-in languages (ja/en/zh/ko/pt/tr), extension language packs
- All pages use i18n and CSS variables for full theme/language support

**Production Quality:**
- Governance & Compliance (GDPR/HIPAA/SOC2/ISO27001/CCPA/APPI)
- 24/365 Scheduler, Cloud Native Integration (AWS/GCP/Azure/Cloudflare)
- Workspace Isolation (default-deny, gradual access permission)

---

## v0.1.x — In Progress (Developer Team)

Items that can be implemented by the development team without large-scale community or funding.

| Status | Feature | Description |
|:------:|---------|-------------|
| Done | **UI i18n completion** | All pages use i18n keys, no hardcoded strings |
| Done | **Theme system** | Dark/Light/High Contrast via CSS variables |
| Done | **Command Palette** | Ctrl/Cmd+K quick navigation |
| Done | **Marketplace UI** | Unified Skills/Plugins/Extensions view |
| Done | **Agent behavior settings** | Autonomy level, browser automation, workspace access |
| Done | **Provider expansion** | 11 LLM providers, 12 service connections with categories |
| Done | **Template Gallery** | 5 quick-start business templates (Content Ops, Sales Research, FAQ/KB, Meeting→Tasks, Pre-publish Review) |
| Done | **Execution Logs view** | Reasoning Traces tab + Approvals queue in Agent Monitor (real-time) |
| Done | **UI redesign** | Cowork-style layout, MIT-licensed colors, code split (48% reduction), theme extension API |
| Done | **CLI Neovim-style modes** | NORMAL/INSERT/COMMAND mode switching, lualine-inspired status line |
| Done | **Token auto-refresh** | 401 interceptor, periodic refresh, prevents auto-logout |
| Done | **Plugin/Extension seeding** | 18 built-in plugins (12 general + 6 role-based packs) + 11 extensions seeded on startup |
| Done | **API client migration** | All pages use centralized api client (auth + Tauri URL) |
| Done | **Frontend data connection** | TicketList, Approvals, Heartbeats, Costs, Audit connected to real API |
| Done | **features/ module separation** | features/company/ with shared useCompanyId hook |
| Done | **Cowork Dispatch** | Fire-and-forget background tasks, status bar feed, /dispatch endpoint |
| Done | **Operator Profile** | Cowork-style about-me + global instructions (/operator-profile) |
| Done | **Tiered browser approval** | 10-level approval hierarchy (navigate < click < type < submit < login < payment) |
| Done | **Role-based plugin packs** | 6 packs (Sales, Finance, HR, Legal, Marketing, Support) |
| Done | **SSO / SAML** | Enterprise single sign-on support |
| Done | **Compliance framework** | GDPR/HIPAA/SOC2/ISO27001 governance endpoints |
| Done | **Plugin Loader UI** | PluginsPage CRUD + install form, API-connected |
| Done | **E2E flow integration** | Dashboard → Interview → SpecPlan → Execution (all API-connected) |
| Done | **Worker core logic** | TaskRunner (5 types, retry, judge) + HeartbeatRunner (cron, checks) |
| Done | **Tool Connector UI** | SettingsPage Provider Connections (12+ services, category filter) |
| Done | **Knowledge Feed UI** | SecretaryPage brain-dumps + knowledge store + PermissionsPage |
| Done | **Contributor Guide** | CONTRIBUTING.md with dev setup, CI checks, design guidelines |
| Done | **VS Code IDE extension** | `extensions/vscode/` — chat, ticket-from-selection, kill-switch, status bar |
| Done | **Hyperagent + Comet bridges** | Two new AgentFrameworkAdapter subclasses under approval gate |
| Done | **AI CEO skill YAMLs** | 5-skill manifest set + plugin-skill-loader with drift report |
| Done | **self_improvement split** | 6 skill modules + facade; main file 1,332 → 55 lines |
| Done | **Dynamic Alembic head** | `version_migration` walks `alembic/versions/` to pick the tip |
| Done | **WCAG 2.2 a11y pass** | 2px focus ring, prefers-reduced-motion, skip-link in 6 locales |
| Done | **Design tokens** | Spacing / typography / motion scales, Skeleton + EmptyState primitives |

---

## v0.2 — Community & Ecosystem (Requires Community)

These features require a user base and community participation.

| Priority | Feature | Description |
|:--------:|---------|-------------|
| **High** | **Discord community server** | Official Discord for user support, feature requests, and plugin sharing |
| **High** | **Community Skill Ecosystem** | Large-scale Skill/Plugin sharing, reviews, ratings |
| **High** | **Marketplace production operation** | User-submitted content, moderation, install counts |
| **High** | **Native mobile app** | React Native / Flutter client with Dispatch integration (phone → desktop) |
| High | **Anonymous Feedback Aggregation** | Privacy-preserving Experience Memory sharing |
| Medium | **Cross-Model Large-scale Verification** | Community-contributed verification datasets |
| Medium | **Multilingual Experience Memory** | Shared knowledge across language boundaries |
| Medium | **Vector DB production integration** | Pinecone/Qdrant/ChromaDB for embedding-based RAG at scale |

## v0.3 — Enterprise & Scale (Requires Funding/Infrastructure)

| Priority | Feature | Description |
|:--------:|---------|-------------|
| High | **Self-Improvement Loop** | Auto-cycle: propose → test → verify → apply |
| High | **Cross-Orchestrator Learning** | Knowledge sharing between ZEO instances |
| Medium | **Fine-tuning Infrastructure** | Auto-create specialized domain models |
| Medium | **Enterprise governance certification** | HIPAA/SOC2 actual certification (legal costs) |
| Medium | **Large-scale multi-tenant operation** | Infrastructure scaling, operations team |

## v1.0 — AI Singularity Platform

| Priority | Feature | Description |
|:--------:|---------|-------------|
| High | **AI Architecture Self-Improvement** | AI proposes system-design-level improvements |
| High | **Meta-Learning** | Learning "how to improve efficiently" itself |
| Medium | **VR/AR & IoT production** | Hardware integration at scale |
| Medium | **Cross-platform agent federation** | Interop with CrewAI, AutoGen, LangChain, etc. |
