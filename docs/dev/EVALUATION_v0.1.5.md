# Zero-Employee Orchestrator — v0.1.5 Evaluation Report

> Evaluation date: 2026-04-07
> Evaluator: Claude Code (Opus 4.6, automated verification + web search + code audit)
> Scope: Full system (backend, frontend, CLI, security, documentation, i18n, competitive landscape)
> Previous: v0.1.3 — 7.7/10 (2026-04-07)

---

## 1. Relative Evaluation (vs Competitors)

### 1.1 Claude Cowork (Anthropic) — Primary Comparison Target

ZEO explicitly positions itself as a "free, Cowork-like" alternative (docs/ja-JP/Zero-Employee Orchestrator.md line 1983). Cowork launched January 2026 as a desktop agent for knowledge work.

| Dimension | Claude Cowork | ZEO v0.1.5 | Winner |
|-----------|--------------|-------------|--------|
| **UX polish** | Consumer-grade, desktop-native | Functional prototype | Cowork |
| **Setup friction** | Download → sign in → work | Install Python → venv → config → run | Cowork |
| **Task execution** | Real (Computer Use, Deep Connectors) | Stub (state transitions only, no actual execution) | Cowork |
| **Model support** | Claude only | 22 families (Anthropic, OpenAI, Gemini, Ollama, g4f) | ZEO |
| **Self-hosting** | Impossible | Full self-hosting | ZEO |
| **Cost** | $20-200/mo per user | Free (users pay LLM providers) | ZEO |
| **Meta-orchestration** | Own plugins/sub-agents only | CrewAI, AutoGen, LangChain, Dify, n8n, Zapier as sub-workers | ZEO |
| **Security depth** | Enterprise controls, telemetry | 14-layer defense (sandbox, PII, prompt guard, approval gate, IAM) | ZEO |
| **Offline** | No | Yes (Ollama) | ZEO |
| **Enterprise** | SSO, admin, plugin marketplace | Auth, audit, but no SSO/SAML | Cowork |
| **Mobile Dispatch** | Phone-to-desktop via QR | Web/desktop only | Cowork |
| **Connectors** | Google Workspace, DocuSign, FactSet, etc. (deep, native) | 34 app connectors (shallow, config-level) | Cowork |

**Verdict**: Cowork wins on polish and actual execution capability. ZEO wins on openness, cost, and architectural ambition. **ZEO cannot compete with Cowork on execution quality today** — its core task execution is unimplemented.

### 1.2 Developer Frameworks

| Framework | Maturity | vs ZEO |
|-----------|----------|--------|
| **LangGraph** | Production-ready, graph-based, checkpointing | ZEO's DAG is 173 lines; LangGraph is far more capable |
| **CrewAI** | Good for prototyping, role-based teams | ZEO claims to orchestrate CrewAI but integration is config-level |
| **AutoGen** | Maintenance mode (Microsoft Agent Framework) | Less relevant comparison |
| **Dify** | $30M funding, 1.4M+ machines, visual builder | ZEO has broader vision but Dify has execution + community |

### 1.3 No-Code Automation

| Platform | vs ZEO |
|----------|--------|
| **n8n** | n8n 2.0 with AI Agent node, LangChain integration — more mature for automation |
| **Zapier** | Massive ecosystem, consumer-friendly — ZEO cannot match connector count |
| **Make** | Visual workflow builder — ZEO's NL approach is different but unproven |

**Relative Score: 5.5/10**
- Vision is compelling (meta-orchestrator + free + open)
- But execution gap vs competitors is severe
- Cowork already has what ZEO promises to build

---

## 2. Objective Evaluation (First-Time User Perspective)

### 2.1 README & First Impressions: 7/10
- README is comprehensive and well-organized
- Feature list is impressive but **overpromises** — many listed features are stubs
- Marketing language ("command every AI framework") implies working orchestration
- Good: No-API-key-required options documented clearly

### 2.2 Install Experience: 4/10
- Requires Python 3.12+, uv/pip, virtual environment setup
- No `pip install zero-employee-orchestrator` on PyPI
- Desktop app requires Rust toolchain + pnpm for development
- Tauri binary releases would help but auto-update was broken until v0.1.5

### 2.3 Time to First Value: 3/10
- Server starts and health check passes
- Can create tickets and brainstorm sessions
- **But**: Cannot actually execute a task end-to-end
- `start_task()` transitions state but doesn't execute anything
- User hits a wall after basic CRUD operations

### 2.4 Error Handling: 6/10
- Graceful degradation for optional services (Sentry, Ollama)
- Security middleware catches invalid inputs
- But many code paths return `None` or `pass`
- Frontend silently fails with `.catch(() => [])`

### 2.5 Documentation: 7/10
- 6 translated READMEs, architecture guide, user guide, security guide
- CLAUDE.md is excellent for AI-assisted development
- But documentation claims features that are stubs

### 2.6 UI Intuitiveness: 7/10
- Cowork-inspired layout works well (task-first, progressive disclosure)
- Autonomy Dial is creative and clear
- 16 of 24+ pages are substantial with real API integration
- Settings page covers 11 LLM providers

### 2.7 Feature Discoverability: 6/10
- Command Palette (Ctrl+K) helps navigation
- Welcome Tour for first-time users
- But hard to discover what actually works vs what's scaffolding

### 2.8 Trust & Transparency: 5/10
- Cowork attribution is transparent and honest
- Security architecture is impressive on paper
- But the gap between documentation claims and implementation reality erodes trust

**Objective Score: 5.6/10**

---

## 3. Additional Perspectives

### 3.1 Architecture Quality: 8/10
- 9-layer design is clean and well-separated
- 47 route modules, 25 services, 22 orchestration modules — impressive scope
- Judge layer (cross-model verification with semantic analysis) is genuinely implemented
- LLM Gateway with multi-provider routing is functional
- Cost Guard budget enforcement works

### 3.2 Implementation Reality: 3/10

**What Actually Works (end-to-end):**
- API infrastructure (FastAPI, auth, middleware, 433 endpoints)
- LLM Gateway (multi-provider routing, sanitization)
- Judge System (3-tier verification, semantic checking)
- Cost Guard (budget pre-flight checks)
- Audit Logging (event-based trail)
- State Machines (ticket/task/approval validation)
- WebSocket Monitoring (real-time events)
- Desktop UI (16+ functional pages)

**What Doesn't Work:**
- **Task execution** — `start_task()` only changes state, no actual execution
- **DAG scheduling** — 173 lines, minimal logic, no real scheduling
- **Multi-agent orchestration** — stubs/message envelopes only
- **Meta-Skills** — 5 types defined, mostly `pass` statements
- **Experience Memory** — schemas only, no retrieval logic
- **Knowledge Store** — DB models only
- **Hypothesis Engine** — empty evaluate methods
- **Avatar Co-evolution** — 582 lines, all methods are `pass`
- **A2A Communication** — protocol defined, routing is stub

**Estimated implementation completion: ~30%**

### 3.3 Deployment Readiness: 5/10
- Docker/docker-compose defined
- Cloudflare Workers deployment option
- Tauri desktop app builds (auto-update now fixed in v0.1.5)
- But no PyPI package, no one-click deploy

### 3.4 i18n / Accessibility: 7/10
- 6 languages at full parity (EN/JA/ZH/KO/PT/TR)
- Desktop installer with language selection (NSIS)
- Extensive translation coverage

### 3.5 Cost to Operate: 9/10
- Zero infrastructure cost possible (g4f + Ollama)
- No subscription fees
- Users control their own LLM spending

### 3.6 Security Posture: 7/10
- 14-layer defense architecture
- Prompt injection defense (28 patterns)
- PII detection (13 categories)
- File sandbox with path boundary checks
- Approval gate with 14 categories
- v0.1.5 fixed: PII detection in dispatch, sandbox in operator_profile, approval gates in delete/publish
- But: security is tested at unit level, not integration/penetration tested

### 3.7 Cowork Design Dependency: Concern

ZEO derives ~35% of its design from Cowork:
- Operator Profile, Dispatch, Approval Gates, Autonomy Dial, nav layout
- The Japanese design doc explicitly says: "Aiming to be a free Cowork-like AI agent platform"
- Risk: If Cowork releases a free tier or open-sources components, ZEO's value proposition weakens
- Mitigation: ZEO's meta-orchestration (orchestrate other frameworks) is genuinely differentiated

---

## 4. Scoring

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| **Relative (vs competitors)** | 5.5 | 0.35 | 1.93 |
| **Objective (first-time user)** | 5.6 | 0.35 | 1.96 |
| **Architecture quality** | 8.0 | 0.08 | 0.64 |
| **Implementation reality** | 3.0 | 0.07 | 0.21 |
| **Security posture** | 7.0 | 0.05 | 0.35 |
| **i18n / Accessibility** | 7.0 | 0.03 | 0.21 |
| **Cost to operate** | 9.0 | 0.04 | 0.36 |
| **Deployment readiness** | 5.0 | 0.03 | 0.15 |

**Overall: 5.8/10** (down from 7.7 in v0.1.3 — recalibrated with honest implementation assessment)

---

## 5. The Core Problem

**ZEO is a beautifully designed car that doesn't drive.**

The architecture is genuinely impressive. The security layers are real. The UI is polished. The documentation is comprehensive. But the **core value proposition — autonomous task execution via multi-agent orchestration — is unimplemented.**

When a user creates a ticket and clicks "execute," the state changes to "in_progress" and... nothing happens. There's no worker, no agent loop, no LLM-driven planning-and-execution cycle. The orchestration layer (DAG, interview, repropose) exists as data structures and method signatures, not as working code.

**This is not a v0.1 product. It's a v0.0.5 architectural prototype with v1.0-level documentation.**

---

## 6. Strategic Pivot Recommendations

### Option A: "Narrow and Deep" — Pick One Flow, Make It Work

**Target**: Get one end-to-end flow working perfectly.

1. User types "Write a competitor analysis for Company X" in Dashboard
2. Interview Layer asks 2-3 clarifying questions
3. DAG creates a 3-step plan: research → analyze → write
4. Each step calls LLM Gateway with proper prompting
5. Judge verifies output quality
6. User approves final result

**Effort**: ~2-4 weeks. Would transform ZEO from demo to usable product.

### Option B: "Meta-Orchestrator Focus" — Double Down on Integration

**Target**: Make the "orchestrate orchestrators" promise real.

1. Actually integrate CrewAI/LangGraph as sub-executors (not just config)
2. Route tasks to the best framework based on task type
3. Provide unified approval/audit layer across all frameworks
4. This is ZEO's unique differentiator vs Cowork

**Effort**: ~4-6 weeks. High differentiation but requires framework expertise.

### Option C: "Cowork Alternative" — Compete Directly on Free + Open

**Target**: Be the best free, self-hosted alternative to Cowork.

1. Implement Computer Use integration (via existing browser-assist)
2. Add real file/folder operations with sandbox
3. Build actual connectors (Google Workspace, Slack, GitHub) beyond config
4. Deliver Dispatch that actually executes (not just state management)

**Effort**: ~6-8 weeks. Directly competes but risks being a perpetual follower.

### Option D: "SDK/Framework" — Pivot from Product to Platform

**Target**: Become the approval/security/audit layer for any AI agent system.

1. Extract the Judge, Approval Gate, Cost Guard, PII Guard as a standalone SDK
2. Offer `pip install zeo-security` that wraps any LangChain/CrewAI/AutoGen agent
3. The unique value is the security + approval + transparency stack, not the orchestration
4. Let others build the execution; ZEO provides the guardrails

**Effort**: ~3-4 weeks. Highest leverage, smallest scope.

### Recommended Path: **A then D**

1. **Immediate** (2 weeks): Make one end-to-end task execution flow work (Option A)
2. **Next** (3 weeks): Extract the security/approval/judge stack as SDK (Option D)
3. **Later**: Decide between B and C based on community response

---

## 7. v0.1.5 Specific Improvements

This release fixed real issues:

| Fix | Impact |
|-----|--------|
| Auto-update jq bug (CRITICAL) | Unblocks all future desktop updates |
| CSP blocking updater | Users can now receive OTA updates |
| Auto-download & install | No manual intervention needed |
| Release workflow hardening | Prevents broken releases |
| PII detection in dispatch | Security rule compliance |
| Sandbox in operator_profile | Security rule compliance |
| Approval gates (5 endpoints) | Security rule compliance |
| Doc count sync (47 routes, 433 endpoints, 11 skills) | Accuracy |
| Model ID compliance (browser_adapter) | Architecture rule compliance |
| bump-version.sh expansion (15 files) | Prevents version drift |

**v0.1.5 is a maintenance/compliance release, not a feature release.**

---

## 8. Key Metrics for Next Evaluation

| Metric | Current | Target for v0.2 |
|--------|---------|------------------|
| End-to-end task execution | Not implemented | 1+ working flow |
| Implementation completion | ~30% | 50%+ |
| Integration test coverage | 0 | 5+ integration tests |
| Stub/pass methods | ~40+ | <10 |
| PyPI installable | No | Yes |
| Time to first value | >30 min | <5 min |

---

## References

- [Claude Cowork — Anthropic](https://www.anthropic.com/product/claude-cowork) (launched Jan 2026)
- [Bloomberg — Anthropic Sees Cowork Agent as Bigger Than Claude Code](https://www.bloomberg.com/news/articles/2026-04-01/) (Apr 2026)
- [Dify $30M Funding — BusinessWire](https://www.businesswire.com/news/home/20260309511426/) (Mar 2026)
- [n8n 2.0 Release](https://n8n.io/) (Dec 2025)
- [ComposioHQ/open-claude-cowork](https://github.com/composiohq/open-claude-cowork) — OSS Cowork alternative
- [CrewAI vs LangGraph vs AutoGen — DataCamp](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen) (2026)
- [Microsoft Copilot Cowork — GeekWire](https://www.geekwire.com/2026/) (Mar 2026)
