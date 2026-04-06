# Changelog

## v0.1.2 (2026-04-06)

### Changed — UI Redesign (VSCode/Zed/Neovim)

- **VSCode Dark Default colors** — All GUI colors replaced with exact VSCode MIT-licensed values. Custom gradients, shadows, and glow effects removed entirely.
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

- **Built-in seeding** — 10 plugins and 11 extensions seeded on server startup.
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
