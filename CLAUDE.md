# Zero-Employee Orchestrator — Claude Code Guide

> **The AI Meta-Orchestrator**: orchestrate orchestrators, unify every AI framework and tool
> under human approval, audit trail, and security.
> 9-layer architecture. Python 3.12+ / FastAPI / Tauri v2 + React / Cloudflare Workers.

## Session Start

```bash
git log --oneline -10
ls apps/api/app/
```

**Key docs**: `README.md` (features, config), `docs/dev/DESIGN.md` (architecture), `docs/dev/REVIEW.md` (security audit), `USER_SETUP.md` (deployment), `ROADMAP.md`

**IMPORTANT: If this file is outdated, read the actual code and README.md and update it.**

## Architecture

9 layers: User → Design Interview → Task Orchestrator (DAG) → Skills → Judge (cross-model) → Re-Propose → State & Memory → Provider (LiteLLM) → Skill Registry

## Directory Map

```
apps/api/app/         # FastAPI backend
  core/               # Config, DB, rate limiting, i18n
  api/routes/         # 47 route modules, 433 endpoints
  services/           # 25 services (business logic)
  orchestration/      # DAG, Judge, transparency, CostGuard (22 modules)
  providers/          # LLM gateway, Ollama, g4f, ModelRegistry
  security/           # sandbox, pii_guard, prompt_guard, iam, workspace_isolation
  policies/           # approval_gate, autonomy_boundary
  integrations/       # app_connector (34 apps), media, MCP, browser-assist
  tools/              # MCP, browser_adapter, agent_adapter
  tests/              # pytest + pytest-asyncio
apps/desktop/         # Tauri v2 + React (Cowork-style layout)
apps/edge/            # Cloudflare Workers
skills/builtin/       # 11 Skills (6 system + 5 domain)
plugins/              # 16 Plugins (10 general + 6 role-based packs)
extensions/           # 11 Extensions
```

## Commands

```bash
zero-employee serve --reload        # Dev server (port 18234)
zero-employee chat                  # Interactive CLI (NL + slash commands)
pytest apps/api/app/tests/          # Tests
ruff check apps/api/app/ && ruff format apps/api/app/  # Lint
./scripts/bump-version.sh X.Y.Z    # Update ALL 8 version files
```

## MUST-FOLLOW Rules

### Security (non-negotiable)
1. External data → LLM: **always** `wrap_external_data()` (`security/prompt_guard.py`)
2. User input → AI: **always** PII check via `pii_guard.py`
3. File access: **always** through `sandbox.py` (whitelist + path boundary `+ "/"`)
4. Dangerous ops: register in `approval_gate.py` + `autonomy_boundary.py`
5. New endpoints: verify security headers applied
6. Secrets: sanitize via `sanitizer.py` before logging
7. Registry imports: `analyze_code_safety()` on manifest; block HIGH risk without `?force=true`

### Version Management
**IMPORTANT: 8 version files. Always use `./scripts/bump-version.sh`.**
Files: root `pyproject.toml`, `apps/api/pyproject.toml`, `apps/desktop/package.json`, `apps/desktop/ui/package.json`, `apps/edge/proxy/package.json`, `apps/edge/full/package.json`, `apps/desktop/src-tauri/tauri.conf.json`, `apps/desktop/src-tauri/Cargo.toml`

### Coding Style
- Python: ruff (line-length=100), type hints, `async def` for all endpoints
- TypeScript: strict mode, functional components, Tailwind CSS
- Model catalog: family IDs only (`anthropic/claude-opus`), never version IDs directly

## Design Principles

- **Meta-Orchestrator**: ZEO integrates other AI frameworks (CrewAI, AutoGen, LangChain, Dify) and automation platforms (n8n, Zapier, Make) as sub-workers under its approval/audit layer. Tool-of-tools: connect to tools that connect to other tools.
- **No API key required**: g4f (subscription), Ollama (local), OpenRouter (one key)
- **ZEO is free**: Users pay LLM providers directly; no provider is "recommended"
- **Skill/Plugin/Extension**: Skill = single task; Plugin = skill bundle (includes role-based packs); Extension = system integration
- **System skills**: Always enabled, cannot be disabled (6 system); 5 domain skills can be toggled
- **UI**: Task-first layout — Cowork-style nav sidebar with progressive disclosure, Autonomy Dial in status bar, Command Palette (Ctrl+K), Dispatch background tasks
- **CLI**: Claude Code-like slash commands (`/read`, `/write`, `/edit`, `/run`, `/ls`, `/cd`, `/pwd`, `/find`, `/grep`)
- **Operator Profile**: Cowork-style about-me + global instructions (`/operator-profile/profile`, `/operator-profile/instructions`)
- **Dispatch**: Background task execution, Cowork Dispatch pattern (`/dispatch`)
- **Browser permissions**: Tiered approval (10 levels: navigate < click < type < submit < login < payment)

## Prohibited

- Blurring Skill/Plugin/Extension boundaries
- Silent execution of approval-required operations
- External transmission without audit logging
- LLM calls without `wrap_external_data()` on external input
- Direct model version IDs in catalog (use `latest_model_id`)
- AI access to unauthorized folders/files
- Password/credential uploads
- User input to AI without PII detection

## Ports

FastAPI: 18234 | Vite dev: 5173

## Post-Change Documentation Sync (MANDATORY)

After any code change (new routes, features, counts), you MUST:
1. **Check ALL md files** for claims that need updating (route count, plugin count, endpoint count, feature lists)
2. **Check ALL translated READMEs** (docs/ja-JP/, docs/zh-CN/, docs/zh-TW/, docs/ko-KR/, docs/pt-BR/, docs/tr/) match the English README
3. **Bidirectional check**: md → code (does every claim match?) AND code → md (is every new feature documented?)
4. **Key files to check**: CLAUDE.md, README.md, ROADMAP.md, SECURITY.md, docs/CHANGELOG.md, docs/guides/architecture-guide.md, docs/dev/EVALUATION_v0.1.2.md

## Release Notes

Write about system behavior changes for end users. Do NOT write about docs/CI/config changes.

## Demo Execution & Evaluation

### Demo Checklist (user scenario testing)

```bash
# Server: cd apps/api && PYTHONPATH=. SECRET_KEY=demo-key DATABASE_URL=sqlite+aiosqlite:///./demo.db python -m uvicorn app.main:app --port 18234
# Auth: curl -s -X POST localhost:18234/api/v1/auth/anonymous-session
# CRUD: POST /companies/$CID/tickets, GET /registry/skills, GET /kill-switch/status
# Security: GET /themes without token → 401, check security headers
# Frontend: cd apps/desktop/ui && npx tsc --noEmit && npx vite build
# Security modules: sandbox boundary, PII guard, prompt guard
```

14 items: server startup, auth flow, protected endpoints, ticket CRUD, security headers, registry (8/10/11), kill switch, models (22+), themes, languages (6), org setup, monitor, brainstorm, app integrations (34 apps)

### Evaluation Criteria

**IMPORTANT: Web search is MANDATORY for all competitive comparisons and market data. Do not rely on training data alone.**

**Required perspectives (minimum):**

1. **Relative evaluation** — Compare vs competitors (CrewAI, Dify, LangGraph, AutoGen, n8n, Claude Cowork) using verified market data from web search. Dimensions: usability, learning curve, onboarding time, security posture, multi-model support, enterprise readiness, ecosystem, community.

2. **Objective evaluation** — First-time user perspective. Dimensions: README clarity, install experience, time to first value, error handling (actionable messages), documentation, UI intuitiveness (progressive disclosure), feature discoverability, trust & transparency.

3. **Additional perspectives** — Architecture quality, deployment readiness, i18n/accessibility, cost to operate, plus any other relevant dimensions.

**Scoring**: 0-10 scale. Overall = (Relative × 0.35) + (Objective × 0.35) + (Additional × 0.30)

**Latest evaluation**: `docs/dev/EVALUATION_v0.1.5.md` — 5.8/10 (2026-04-07, recalibrated with honest implementation audit)
