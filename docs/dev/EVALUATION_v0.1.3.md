# Zero-Employee Orchestrator — v0.1.3 Evaluation Report

> Evaluation date: 2026-04-07
> Evaluator: Claude Code (automated verification + web search for competitor data)
> Scope: Full system (backend, frontend, CLI, security, documentation, i18n)
> Previous: v0.1.2 — 8.3/10 (2026-04-06)

---

## Demo Execution Results

### Results: 20/20 PASS (code-level verification)

| # | Test | Result |
|---|------|--------|
| 1 | Server startup (healthz/readyz) | PASS |
| 2 | Anonymous session → JWT auth | PASS |
| 3 | Protected endpoints reject unauthenticated | PASS |
| 4 | Ticket CRUD (create, list) | PASS |
| 5 | Security headers (CSP, HSTS, X-Frame, XSS) | PASS |
| 6 | Registry seeded (8 Skills, 16 Plugins, 11 Extensions) | PASS |
| 7 | Kill switch status | PASS |
| 8 | Model catalog (24 families loaded) | PASS |
| 9 | Theme set/get workflow | PASS |
| 10 | Language packs (6 languages) | PASS |
| 11 | Org setup interview questions | PASS |
| 12 | Monitor dashboard | PASS |
| 13 | Brainstorm session creation | PASS |
| 14 | App integrations (34 apps, 14 categories) | PASS |
| 15 | Operator Profile (create/read) | PASS |
| 16 | Global Instructions (set/get) | PASS |
| 17 | Task Dispatch (create → completed) | PASS |
| 18 | Dispatch list + UI page | PASS |
| 19 | Security modules (sandbox + PII + prompt guard) | PASS |
| 20 | Browser tiered approval (10 levels) | PASS |

### Build: ruff 0 errors (236 files), TypeScript 0 errors

---

## Competitor Landscape (April 2026 — Web Search Verified)

| Platform | Stars | Key 2026 Updates | Pricing |
|----------|-------|-------------------|---------|
| **Claude Cowork** | N/A (closed) | Recurring scheduled tasks, Computer Use, MS365 integration, Windows launch, 11 open-source plugins, Dispatch, Sonnet 4.6 default | $20-100+/mo |
| **Dify** | 134k+ | v1.9.0: Knowledge Pipeline, Queue-based Graph Engine, MCP support | Open-source + Cloud |
| **CrewAI** | 30k+ | v1.13.0: Enterprise RBAC, SSO, NVIDIA NemoClaw, GPT-5 compat | Free + Enterprise |
| **LangGraph** | Part of LangChain | v1.0.10 GA, graph-based orchestration, multi-agent hierarchies, OpenTelemetry | Open-source |
| **n8n** | 70k+ | v2.0: Native LangChain, 70+ AI nodes, HITL tool approval, MCP Client, Guardrails node | Open-source + Cloud |
| **AutoGen** | 40k+ | v0.4: Actor model, OpenTelemetry, cross-language (.NET/Python), AutoGen Studio rebuild | Open-source |

---

## 1. Relative Evaluation (vs Competitors)

> Sources: [DEV.to comparison](https://dev.to/agdex_ai/langchain-vs-crewai-vs-autogen-vs-dify-the-complete-ai-agent-framework-comparison-2026-4j8j), [Turing framework comparison](https://www.turing.com/resources/ai-agent-frameworks), [n8n 8-month review](https://dev.to/nova_gg/n8n-review-2026-i-used-it-for-8-months-to-build-ai-agents-honest-verdict-2aib), [CrewAI v1.13.0](https://aiforautomation.io/news/2026-04-03-crewai-1-13-0-gpt5-enterprise-rbac), [Cowork features](https://claude.com/product/cowork)

| Dimension | Score | Rationale | Key Gap |
|-----------|-------|-----------|---------|
| **Usability** | 7.5 | NL + GUI + CLI is strong, but **many features are breadth-over-depth**. Dispatch has UI; Operator Profile is API-only. Brainstorm/Secretary pages are functional but minimal compared to Cowork's polished flows. | Operator Profile needs UI. Page-level depth is shallow. |
| **Learning curve** | 8.0 | Cowork-style layout is intuitive. Command palette + slash commands lower friction. But no guided walkthrough for first-time users — competitors (Cowork, Dify) offer interactive tutorials. | No onboarding tour. No interactive tutorial. |
| **Onboarding** | 7.5 | 2-min install, no API key. Setup wizard helps. But **no try-before-signup flow**, no video, no sandbox demo. Industry best practice (2026): 40% of top AI tools let users try without account. ZEO requires server startup. | No hosted demo. No video tutorial. |
| **Security** | 9.5 | Still unmatched: 14 approval categories, 10 browser tiers, PII guard (13 patterns), sandbox (371 lines, symlink detection), prompt guard (injection + Base64 recursion), kill switch. n8n added HITL but only at tool level. Cowork's VM sandbox has reported vulnerabilities. | No external penetration test. |
| **Multi-model** | 9.0 | 24 families + zero-cost (g4f/Ollama). Dify supports more providers via plugins. LangChain has 700+ integrations. But ZEO's zero-cost-to-start is unique. | No streaming/real-time model output in UI. |
| **Enterprise** | 7.5 | SSO (Google + SAML), RBAC, audit, compliance API, workspace isolation. But **no actual SOC2/HIPAA certification**. CrewAI v1.13.0 has production RBAC + NVIDIA policy enforcement. No cloud-hosted option. | No hosted/managed offering. No real certifications. |
| **Ecosystem** | 5.5 | 16 plugins, 11 extensions, marketplace flow. But **plugin runtime logic is manifests + thin handlers**. Cowork: 11 polished plugins. Dify: rich plugin marketplace. LangChain: thousands of integrations. Plugin "depth" is the real issue. | Plugins lack real business logic depth. |
| **Community** | 2.0 | Near-zero stars, no Stack Overflow presence, no tutorials by third parties, no Discord/community forum. Dify: 134k stars. n8n: 70k. CrewAI: 30k. **This is the existential gap.** | No community infrastructure at all. |

**Relative Score: 7.1/10** (prev: 8.3 — adjusted for honest competitor parity and community weight)

### Score Change Rationale
- **Usability 8.5→7.5**: Cowork's 2026 updates (Computer Use, recurring tasks, MS365) widened the UX gap. ZEO features are broad but shallow.
- **Onboarding 9.0→7.5**: Industry standard shifted — 2026 best practice demands try-before-signup, video, interactive tours. ZEO has none.
- **Enterprise 8.5→7.5**: CrewAI shipped real RBAC + NVIDIA policy enforcement. ZEO's compliance is API stubs without actual certifications.
- **Ecosystem 7.5→5.5**: Previous score was generous. Plugin manifests ≠ plugin depth. Cowork shipped 11 real plugins.
- **Community 3.0→2.0**: Gap widened as competitors grew. Dify hit 134k stars.

---

## 2. Objective Evaluation (First-Time User)

> Sources: [UserGuiding AI onboarding 2026](https://userguiding.com/blog/how-top-ai-tools-onboard-new-users), [NN/g AI user onboarding](https://www.nngroup.com/articles/new-AI-users-onboarding/), [Smashing Agentic UX](https://www.smashingmagazine.com/2026/02/designing-agentic-ai-practical-ux-patterns/)

| Dimension | Score | Rationale | Fix Proposal |
|-----------|-------|-----------|--------------|
| **README clarity** | 9.0 | Tagline clear. 3-path getting started. 7 language badges. Good. | — |
| **Install experience** | 8.0 | Desktop/CLI/Docker all defined. No API key for first use. But **pip install requires Python 3.12+**, and Docker needs compose knowledge. No one-click cloud deploy. | Add one-click Railway/Render deploy button |
| **Time to first value** | 6.5 | Setup wizard ~3 min. But **no auto-demo, no sample data, no "here's what ZEO can do" moment**. First-time user lands on empty Dashboard with an input box and zero context. NN/g: "New users need to see AI value immediately." | Auto-seed demo ticket + demo dispatch on first login |
| **Error handling** | 7.5 | Toast notifications across pages. But **some errors are silent** (Secretary, Monitor). No global error boundary with retry suggestions. | Add ErrorBoundary with "Report Bug" action |
| **Documentation** | 6.5 | README excellent. CLAUDE.md solid. But **no docs site, no searchable API reference, no FAQ, no video**. 2026 standard: interactive docs (Dify), tutorials (CrewAI), video walkthroughs (n8n). | Create docs site (Docusaurus/Nextra). Add OpenAPI /docs page. |
| **UI intuitiveness** | 7.5 | Progressive disclosure works. Dispatch page is functional. But **Operator Profile has no UI** — a core Cowork feature is API-only. Autonomy Dial cycles levels but doesn't show current effect. Secretary has no empty state guidance. | Add Operator Profile page. Add Autonomy Dial tooltip explaining each level. |
| **Feature discoverability** | 6.5 | Nav sidebar + Command Palette. But **no feature announcements, no "What's New", no tooltips for new features**. 33 pages are a lot — user doesn't know what's important. | Add Welcome Tour (3-5 steps). Add "What's New" banner for new features. |
| **Trust & transparency** | 9.0 | Reasoning traces, approval gates, kill switch, audit logs. Strong and genuine. | — |

**Objective Score: 7.6/10** (prev: 8.1 — adjusted for industry-standard 2026 onboarding expectations)

### Score Change Rationale
- **Time to first value 8.0→6.5**: Empty Dashboard on first launch is a critical UX failure. Competitors pre-populate demos.
- **Documentation 7.0→6.5**: No docs site is below 2026 standard. Dify, CrewAI, n8n all have searchable docs with examples.
- **Feature discoverability 7.0→6.5**: No onboarding tour means most features are invisible to new users.

---

## 3. Additional Perspectives

### Architecture: 8.0/10
- 9-layer separation is clean and well-designed
- 25 services, 47 routes, 22 orchestration modules
- **Test coverage: 27 test files for 433 endpoints** — better than v0.1.2 (14 files) but still low (~6% coverage by file)
- Operator Profile uses filesystem storage (not DB) — fine for v0.1 but not scalable

### Deployment: 7.5/10
- Docker, Tauri, Cloudflare Workers all defined
- CI/CD: 10 workflows, auto-release
- **No cloud-hosted option** — every competitor (Dify Cloud, CrewAI Cloud, n8n Cloud) offers managed hosting
- **No one-click deploy** (Railway, Render, Vercel) — barrier for evaluation

### i18n: 9.0/10
- 6 languages at full parity
- Extension language pack system
- NSIS installer multilingual
- **All translated READMEs now synced** (Cowork, Operator Profile, Dispatch added)

### Cost: 9.5/10
- g4f/Ollama $0 paths are genuine differentiators
- CostGuard budget enforcement
- No competitor matches zero-cost-to-start

**Additional Average: 8.5/10**

---

## Known Issues (Honest Assessment)

| Issue | Severity | Fix Proposal |
|-------|----------|--------------|
| **No Operator Profile UI page** | High | Create `OperatorProfilePage.tsx` with about-me editor + instructions editor |
| **Empty Dashboard on first launch** | High | Auto-seed demo data (1 ticket, 1 dispatch) + Welcome Tour overlay |
| **No docs site** | High | Deploy Docusaurus/Nextra with API reference, guides, FAQ |
| **Plugin depth is shallow** | Medium | Add real business logic to 3 top plugins (browser-use, ai-secretary, research) |
| **No hosted demo / cloud deploy** | Medium | Add Railway/Render one-click deploy; consider hosted demo sandbox |
| **Test coverage ~7%** | Medium | Target 30% coverage for core paths (auth, tickets, dispatch, security) |
| **Community infrastructure missing** | Medium | Create Discord/GitHub Discussions. Write 3 tutorial posts. |
| **No video/interactive tutorial** | Medium | Record 5-min "First 5 Minutes with ZEO" video |
| **Autonomy Dial UX unclear** | Low | Add tooltip explaining each level's concrete effect |
| **Endpoint count was stale (387→433)** | Low | Fixed in v0.1.5 — all docs now show 433 |

---

## Concrete Fix Proposals (Priority Order)

### P0 — First-Time User Experience (Impact: +1.0 to Objective score)

**1. Welcome Tour (3 steps)**
```
Step 1: "This is your Dashboard — describe tasks in natural language"
Step 2: "Monitor your AI agents here" (point to Monitor nav)
Step 3: "Control AI autonomy here" (point to Autonomy Dial)
```
Implementation: React overlay component, ~100 lines, localStorage flag.

**2. Demo Data Seeding on First Launch**
- Create 1 sample ticket ("Design onboarding flow for new product")
- Create 1 sample dispatch task (completed, with result)
- Show in Dashboard as "Example — try editing this"

**3. Operator Profile Page**
- New page at `/operator-profile`
- Two sections: About Me (markdown editor) + Global Instructions (textarea)
- Connected to existing `/api/v1/operator-profile/` endpoints
- Add to nav sidebar under Core items

### P1 — Documentation & Discoverability (Impact: +0.5 to Objective score)

**4. Docs Site**
- Docusaurus with: Getting Started, Architecture, API Reference (from OpenAPI), Plugin Development, Security Model
- Host on GitHub Pages or Cloudflare Pages
- Link from README

**5. OpenAPI /docs Page**
- FastAPI already generates this — ensure it's accessible and complete
- Add descriptions to all 433 endpoints

**6. "What's New" Banner**
- Show once per version update on Dashboard
- 3-5 bullet points of new features
- Dismissible, stored in localStorage

### P2 — Ecosystem & Depth (Impact: +1.0 to Ecosystem score)

**7. Plugin Depth — Pick 3, Go Deep**
- `ai-secretary`: Real AI categorization with LLM calls, not just pattern matching
- `browser-use`: Actual Playwright integration test suite, not just adapter stubs
- `research`: Real web search + summarization pipeline

**8. Community Infrastructure**
- Enable GitHub Discussions
- Create Discord server (or link to existing)
- Write 3 blog posts: "Why ZEO", "Building Your First Plugin", "ZEO vs CrewAI"

### P3 — Deployment & Enterprise (Impact: +0.5 to Additional score)

**9. One-Click Deploy**
- Railway template (railway.json)
- Render blueprint (render.yaml)
- Both with SQLite default, Ollama optional

**10. Test Coverage**
- Target: auth, tickets, dispatch, security, registry routes
- Goal: 30% endpoint coverage (115+ endpoints tested)

---

## Overall Score

```
Relative:    7.1 / 10  (weight: 0.35)
Objective:   7.6 / 10  (weight: 0.35)
Additional:  8.5 / 10  (weight: 0.30)

Overall = (7.1 × 0.35) + (7.6 × 0.35) + (8.5 × 0.30)
        = 2.485 + 2.660 + 2.550
        = 7.7 / 10
```

### **Overall: 7.7 / 10** (prev: 8.3)

### Why the Score Dropped

The previous evaluation (8.3) was measured against a less mature competitive landscape and used generous scoring in Ecosystem (7.5) and Community (3.0). In April 2026:

1. **Cowork shipped major updates**: Computer Use, recurring tasks, MS365 integration, 11 polished plugins, Windows parity. ZEO's Cowork-inspired features are now trailing the source of inspiration.
2. **Industry onboarding standards rose**: Try-before-signup, interactive tutorials, video walkthroughs are now table stakes. ZEO has none.
3. **Community gap widened**: Dify grew to 134k+ stars. n8n at 70k. CrewAI at 30k. ZEO has near-zero.
4. **Plugin depth was overrated**: Manifests + thin handlers ≠ functioning business logic. Ecosystem score was corrected.

### What ZEO Still Does Best

- **Security**: Unmatched in the open-source AI agent space. 14 approval categories, 10 browser tiers, PII/prompt guard, kill switch.
- **Zero-cost path**: g4f + Ollama = genuine $0 to start. No competitor matches this.
- **Architecture**: Clean 9-layer separation. 22 orchestration modules. Meta-orchestrator concept is unique.
- **i18n**: 6 languages at full parity — rare for a v0.1 project.

### Path to 8.5+

If P0 fixes are implemented (Welcome Tour + Demo Data + Operator Profile Page), the Objective score rises to ~8.5. Combined with P1 (Docs Site + What's New), the overall score could reach **8.2-8.5** without any architectural changes.

---

## Sources

- [Claude Cowork product page](https://claude.com/product/cowork)
- [Cowork changelog (CoworkerAI)](https://coworkerai.io/changelog)
- [Cowork Computer Use (Engadget)](https://www.engadget.com/ai/claude-code-and-cowork-can-now-use-your-computer-210000126.html)
- [Cowork plugins updates (eesel AI)](https://www.eesel.ai/blog/claude-cowork-plugins-updates)
- [Anthropic Cowork office worker (CNBC)](https://www.cnbc.com/2026/02/24/anthropic-claude-cowork-office-worker.html)
- [Dify 134k stars](https://dify.ai/blog/100k-stars-on-github-thank-you-to-our-amazing-open-source-community)
- [Dify v1.9.0](https://github.com/langgenius/dify/discussions/26138)
- [CrewAI v1.13.0](https://aiforautomation.io/news/2026-04-03-crewai-1-13-0-gpt5-enterprise-rbac)
- [LangGraph agent orchestration](https://www.langchain.com/langgraph)
- [n8n AI agents review](https://dev.to/nova_gg/n8n-review-2026-i-used-it-for-8-months-to-build-ai-agents-honest-verdict-2aib)
- [AutoGen v0.4](https://www.microsoft.com/en-us/research/blog/autogen-v0-4-reimagining-the-foundation-of-agentic-ai-for-scale-extensibility-and-robustness/)
- [AI agent framework comparison 2026 (Turing)](https://www.turing.com/resources/ai-agent-frameworks)
- [Multi-agent frameworks 2026 (GuruSup)](https://gurusup.com/blog/best-multi-agent-frameworks-2026)
- [AI onboarding best practices 2026 (UserGuiding)](https://userguiding.com/blog/how-top-ai-tools-onboard-new-users)
- [AI user onboarding (NN/g)](https://www.nngroup.com/articles/new-AI-users-onboarding/)
- [Agentic AI UX patterns (Smashing Magazine)](https://www.smashingmagazine.com/2026/02/designing-agentic-ai-practical-ux-patterns/)
- [MintMCP: Cowork audit gap](https://www.mintmcp.com/blog/claude-cowork-audit-logging-gap)
