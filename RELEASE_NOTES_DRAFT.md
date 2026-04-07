## Security

- **Kill Switch** — Emergency halt mechanism for all active AI executions. Activate via Agent Monitor UI button or `POST /kill-switch/activate` API. Blocks all new executions until explicitly resumed. Designed for immediate response to unexpected agent behavior.
- **Tiered Judge verification** — Judge Layer now operates in three tiers: LIGHTWEIGHT (rule-based checks for read operations), STANDARD (adds policy compliance for writes), HEAVY (adds cross-model verification for send/delete/billing). Automatically selected by operation risk level, reducing API cost by ~70% for routine tasks.
- **Role-based tool permissions** — 5 default agent policies enforce least-privilege access: Secretary (read/write), Researcher (read/execute), Reviewer (read-only), Executor (read/write/execute), Admin (full). AI agents cannot access tools outside their assigned role.
- **Memory trust levels** — Experience Memory entries now carry source type, trust score (0.0–1.0), verification status, and expiry timestamps. Only memories with trust ≥ 0.7 and not expired inform future decisions. Prevents unreliable or outdated information from affecting agent behavior.
- **Red-team self-testing (8 categories, 22 tests)** — Adversarial payloads tested against actual security modules. Covers prompt injection, data leakage, privilege escalation, PII exposure, unauthorized access, sandbox escape, rate limit bypass, and auth bypass.
- **Sandbox symlink hardening** — Detects and blocks resolved paths pointing outside whitelisted directories.

## Platform

- **Google OAuth** — Full OAuth 2.0 flow for desktop and web. Backend handles authorization URL generation, callback with code exchange, user creation/login, and polling-based token delivery for Tauri desktop apps.
- **Organization auto-generation** — `POST /org-setup/generate` creates departments, teams, and agents from business interview answers. Writes directly to database with audit logging.
- **Company update API** — `PATCH /companies/{id}` enables changing organization name, mission, and description after initial setup. Settings page uses this instead of config API.
- **5 business templates** — Ready-to-use workflow templates in Setup wizard and Dashboard: Content Operations, Sales Research, Internal FAQ / Knowledge Base, Meeting-to-Tasks, Pre-publish Review. Each pre-configures business category, pain points, and team size.
- **Orchestration visualization** — Agent Monitor page now includes Reasoning Traces tab (step-by-step AI decision timeline with confidence levels) and Approvals tab (pending approval queue with risk indicators, approve/reject/details buttons, badge count).
- **Settings TOC sidebar** — VSCode-style left sidebar with section navigation and search filtering. Sections scroll into view on click.
- **Integration strategy messaging** — Settings connections section now explains ZEO's role as the judgment, approval, and audit layer, with external tools handling execution.
- **iPaaS workflow registration** — Register n8n, Zapier, and Make webhooks via `POST /ipaas/workflows` with trigger event binding.
- **Custom app registration** — `POST /app-integrations/apps/custom` adds arbitrary external applications to the connector hub.
- **Marketplace publish flow** — Users can publish Skills, Plugins, and Extensions. Items enter pending_review status before becoming discoverable.

## Internationalization

- **6 languages at full parity** — Japanese, English, Chinese, Korean, Portuguese, and Turkish locale files all contain 699 keys with identical section structures.
- **Backend interview i18n** — Organization setup interview questions respond to Accept-Language header. Returns English by default, Japanese when explicitly requested.

## Desktop UI

- **Cowork-style layout** — Nav bar with grouped icons and dividers, centered page title in title bar, status bar with Autonomy Dial and Dispatch feed.
- **Button interactions** — opacity 0.8 on press, 0.4 when disabled, no scale transforms. 120ms transitions.
- **Toast notifications** — Replaced console.error calls with useToastStore across Brainstorm, Skills, Plugins, and Extensions pages.
- **CSS variables** — Hardcoded hex colors replaced throughout all pages. Dark theme uses MIT-licensed palette (#1E1E1E base, #252526 surface, #333333 nav bar, #007ACC accent).
- **Dashboard chat history** — Natural language commands and responses displayed as persistent conversation log.
- **Model selector** — Brainstorm page uses click-to-toggle dropdown instead of checkboxes for model selection.
- **Skill list sections** — System and user skills separated with section headers.

## AI Model Catalog

- **22 models** across 8 providers. Family-based IDs with automatic latest version resolution.
- **5 execution modes** — Quality, Speed, Cost, Free (Ollama), Subscription (g4f). Per-task model override supported via plan_json.

## Deployment

- **Database model import fix** — BrainstormSessionRecord is now imported at startup to ensure table creation. All 33+ tables created correctly on fresh install.
