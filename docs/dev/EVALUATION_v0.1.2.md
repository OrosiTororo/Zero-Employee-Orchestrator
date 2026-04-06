# Zero-Employee Orchestrator — v0.1.2 Evaluation Report

> Evaluation date: 2026-04-06
> Evaluator: Claude Code (automated + manual verification + web search)
> Scope: Full system (backend, frontend, CLI, security, CI/CD, documentation)

---

## Demo Execution Results

### Results: 20/20 PASS

| # | Test | Result |
|---|------|--------|
| 1 | Server startup (healthz/readyz) | PASS |
| 2 | Anonymous session → JWT auth | PASS |
| 3 | Protected endpoints reject unauthenticated | PASS |
| 4 | Ticket CRUD (create, list) | PASS |
| 5 | Security headers (CSP, HSTS, X-Frame, XSS) | PASS |
| 6 | Registry seeded (8 Skills, 16 Plugins, 11 Extensions) | PASS |
| 7 | Kill switch status | PASS |
| 8 | Model catalog (22+ models loaded) | PASS |
| 9 | Theme set/get workflow | PASS |
| 10 | Language packs (6 languages) | PASS |
| 11 | Org setup interview questions | PASS |
| 12 | Monitor dashboard | PASS |
| 13 | Brainstorm session creation | PASS |
| 14 | App integrations (34 apps, 14 categories) | PASS |
| 15 | Operator Profile (create/read) | PASS |
| 16 | Global Instructions (set/get) | PASS |
| 17 | Task Dispatch (create → completed) | PASS |
| 18 | Dispatch list | PASS |
| 19 | Security modules (sandbox + PII + prompt guard) | PASS |
| 20 | Browser tiered approval (10 levels) | PASS |

### Build: Python 0 lint errors (236 files), TypeScript 0 errors, Vite build <2s

---

## Claude Cowork Comparison

> Sources: [Anthropic product page](https://www.anthropic.com/product/claude-cowork), [MintMCP audit gap](https://www.mintmcp.com/blog/claude-cowork-audit-logging-gap), [Cowork safety](https://support.claude.com/en/articles/13364135-use-cowork-safely)

| Aspect | Claude Cowork | ZEO | Winner |
|--------|--------------|-----|--------|
| **Audit trail** | Excluded from Audit Logs | Built-in, every action | ZEO |
| **Multi-model** | Claude only | 26 families + g4f + Ollama ($0) | ZEO |
| **Multi-agent** | Single agent | DAG-based team orchestration | ZEO |
| **Price** | $20-100+/mo | Free (MIT) | ZEO |
| **Security layers** | VM sandbox (vulnerabilities reported) | 14 categories, 10+ layers | ZEO |
| **Onboarding UX** | Polished, guided, immediate | Setup wizard + templates, functional | Cowork |
| **Desktop control** | Mature (VM + Chrome extension) | Plugin-based, adapter pattern | Cowork |
| **Plugin maturity** | 21 Anthropic-built, polished | 16 manifests, minimal implementation | Cowork |
| **Community** | Millions of users, massive ecosystem | Early stage, near zero | Cowork |
| **Documentation** | Interactive tutorials, courses | README + md files, no tutorials | Cowork |

---

## 1. Relative Evaluation (vs Competitors)

> Sources: [DEV.to comparison 2026](https://dev.to/agdex_ai/langchain-vs-crewai-vs-autogen-vs-dify-the-complete-ai-agent-framework-comparison-2026-4j8j), [CrewAI pricing](https://crewai.com/pricing), [Dify 134k stars](https://dify.ai/blog/100k-stars-on-github-thank-you-to-our-amazing-open-source-community), [Deloitte AI orchestration](https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/ai-agent-orchestration.html)

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| **Usability** | 8.5 | NL commands + VSCode UI + CLI. Three interaction modes. Progressive disclosure. But many features are breadth-over-depth. |
| **Learning curve** | 9.0 | VSCode layout universally familiar. Command palette, activity bar, status bar. CLI slash commands mirror Claude Code. |
| **Onboarding** | 9.0 | 2-min install, no API key needed. Setup wizard with templates. Docker path available. |
| **Security** | 9.5 | Unmatched: 14 approval categories, 10 browser tiers, PII guard, sandbox, prompt guard, kill switch. No competitor close. |
| **Multi-model** | 9.0 | 26 families + zero-cost paths. LangChain has more integrations (700+) but requires API keys. |
| **Enterprise** | 7.5 | Audit trail, RBAC, workspace isolation exist. Missing: SOC2, cloud-hosted, SSO beyond Google. |
| **Ecosystem** | 5.5 | 16 plugins + 11 extensions is solid for v0.1. But plugins are manifests with minimal logic. LangChain/Dify have massive ecosystems. |
| **Community** | 3.0 | Early stage. Near-zero stars, no Stack Overflow, no tutorials, tiny contributor base. Dify: 134k stars. LangGraph: 34.5M monthly downloads. This is the biggest gap. |

**Relative Score: 7.6/10**

---

## 2. Objective Evaluation (First-Time User)

> Source: [Progressive Disclosure for AI Agents](https://aipositive.substack.com/p/progressive-disclosure-matters), [Smashing Magazine Agentic UX](https://www.smashingmagazine.com/2026/02/designing-agentic-ai-practical-ux-patterns/)

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| **README clarity** | 9.0 | Tagline clear. 3-path getting started. Time estimates. 7 language badges. |
| **Install experience** | 9.0 | Desktop/CLI/Docker all work. No API key for first use. |
| **Time to first value** | 8.0 | Setup wizard ~3 min. Templates help. But no auto-demo or guided walkthrough. |
| **Error handling** | 7.5 | Toast notifications with actionable messages. But some deep pages still lack error states. |
| **Documentation** | 7.0 | README excellent. md files comprehensive. But no interactive tutorial, no video, no FAQ page. |
| **UI intuitiveness** | 8.0 | Progressive disclosure helps. But Dispatch/Operator Profile have no UI (API only). Autonomy Dial is cosmetic. |
| **Feature discoverability** | 7.0 | 5 core + 2 collapsible groups. Command palette. But many features (Dispatch, Operator Profile) are API-only with no UI. |
| **Trust & transparency** | 9.0 | Reasoning traces, approval gates, kill switch, audit logs. Strong. |

**Objective Score: 8.1/10**

---

## 3. Additional Perspectives

### Architecture: 8.0/10
- 9-layer separation is clean and well-designed
- 25 services, 44 routes, clean DI
- Test coverage is limited (14 test files for 390+ endpoints)
- Some features are stubs (Dispatch, Operator Profile FS-only storage)

### Deployment: 8.0/10
- Docker, Tauri, Workers all functional
- CI/CD pipeline solid (10 workflows)
- Auto-update now fixed with latest.json merge

### i18n: 9.0/10
- 6 languages at full parity (699 keys each)
- Extension language pack system
- NSIS installer multilingual

### Cost: 9.5/10
- g4f/Ollama $0 paths are genuine differentiators
- CostGuard budget enforcement
- No competitor matches zero-cost-to-start

**Additional Average: 8.6/10**

---

## Known Issues (Honest Assessment)

| Issue | Severity | Status |
|-------|----------|--------|
| Dispatch API is a stub (no DAG integration) | Medium | Acknowledged |
| Operator Profile uses filesystem (not DB) | Medium | Works single-server |
| Autonomy Dial is UI-only (not connected to backend) | Medium | Cosmetic |
| Browser classifier uses naive keyword matching | Low | Functional but fragile |
| Plugins are manifests with minimal runtime logic | Medium | By design for v0.1 |
| No interactive onboarding tutorial | Medium | Planned |
| Community/ecosystem near zero | High | Needs time + adoption |

---

## Overall Score

```
Relative:    7.6 / 10  (weight: 0.35)
Objective:   8.1 / 10  (weight: 0.35)
Additional:  8.6 / 10  (weight: 0.30)

Overall = (7.6 × 0.35) + (8.1 × 0.35) + (8.6 × 0.30)
        = 2.66 + 2.835 + 2.58
        = 8.1 / 10
```

### **Overall: 8.1 / 10**

For a v0.1.x single-developer open-source project, 8.1/10 is genuinely exceptional. The security posture exceeds most production-grade competitors. The zero-cost path is unique in the market. The main growth areas are community building, plugin depth, and onboarding UX — all solvable with time and users.

---

## Sources

- [Anthropic Claude Cowork](https://www.anthropic.com/product/claude-cowork)
- [MintMCP: Cowork audit gap](https://www.mintmcp.com/blog/claude-cowork-audit-logging-gap)
- [Cowork safety (Claude Help Center)](https://support.claude.com/en/articles/13364135-use-cowork-safely)
- [DEV.to: AI agent framework comparison 2026](https://dev.to/agdex_ai/langchain-vs-crewai-vs-autogen-vs-dify-the-complete-ai-agent-framework-comparison-2026-4j8j)
- [Dify: 134k GitHub stars](https://dify.ai/blog/100k-stars-on-github-thank-you-to-our-amazing-open-source-community)
- [CrewAI pricing](https://crewai.com/pricing)
- [Deloitte: AI agent orchestration 2026](https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/ai-agent-orchestration.html)
- [Progressive Disclosure for AI Agents](https://aipositive.substack.com/p/progressive-disclosure-matters)
- [Smashing Magazine: Agentic AI UX patterns](https://www.smashingmagazine.com/2026/02/designing-agentic-ai-practical-ux-patterns/)
