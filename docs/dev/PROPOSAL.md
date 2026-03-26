# Zero-Employee Orchestrator — Development of a Multi-AI Autonomous Business Execution Platform with Built-in Approval and Audit

<div align="center">

**Define business workflows in natural language and operate multiple AI as an "organization"**
**A safe, transparent AI orchestration platform**

---

*Zero-Employee Orchestrator (ZEO)*
*v0.1 | 2026-03-12*

</div>

---

## 0. Title

### **Development of a Multi-AI Autonomous Business Execution Platform with Built-in Approval and Audit**

An AI orchestration platform that defines business workflows in natural language, delegates planning, execution, verification, and improvement roles across multiple AI agents, and autonomously executes business tasks with human approval and auditability as prerequisites. Through a 9-layer architecture, it consistently handles everything from natural language input through requirements exploration via Design Interview, DAG-based task decomposition and parallel execution, two-stage quality verification via Judge Layer (rule-based checks + cross-model verification), automatic replanning during failures via Self-Healing DAG, to experience learning via Experience Memory. Dangerous operations (posting, sending, deleting, billing, permission changes) are always blocked by approval flows, and all operations are recorded in audit logs, achieving business automation while preventing AI from going rogue. The 3-tier extension system of Skill / Plugin / Extension allows flexible addition of business capabilities, and fully offline, completely free operation is supported via Ollama local models. In v0.1, the 9-layer architecture foundation, 23-screen UI, 40+ API endpoints, AI Self-Improvement Plugin (6 Skills implemented), ZEO-Bench benchmark, chaos tests, and more have been designed and implemented by a single developer.

---

## 1. What We Are Building

### 1.1 Background — Why AI Orchestration Is Needed Now

Between 2025 and 2026, AI agent technology has evolved rapidly. LLMs such as ChatGPT, Claude, and Gemini have moved beyond simple Q&A to executing code generation, document creation, and data analysis at high quality.

However, current AI utilization has **structural limitations**:

```
+----------------------------------------------------------+
|  Current Challenges in AI Utilization                    |
|                                                          |
|  1. Starting from zero every time                        |
|     -> Entering the same background info into ChatGPT    |
|                                                          |
|  2. Manual bridging                                      |
|     -> Manually copying AI output to paste into the      |
|        next step                                         |
|                                                          |
|  3. Unknown quality                                      |
|     -> Having to personally verify whether AI answers    |
|        are correct                                       |
|                                                          |
|  4. Invisible progress                                   |
|     -> Not knowing how far yesterday's AI task           |
|        has progressed                                    |
|                                                          |
|  5. Fear of runaway behavior                             |
|     -> Worried AI might send wrong emails or             |
|        delete important data                             |
|                                                          |
|  6. No experience accumulation                           |
|     -> Repeating the same mistakes for the same          |
|        types of work                                     |
+----------------------------------------------------------+
```

These challenges stem from using AI as a "one-shot tool." This project solves these challenges at the architecture level by building a platform that operates AI as an **"organization."**

### 1.2 Purpose — What We Aim to Achieve

**Zero-Employee Orchestrator (ZEO)** is an AI orchestration platform that achieves the following:

| Feature | Description |
|---------|-------------|
| **Natural Language Input** | Business starts with just "Create a competitive analysis report" |
| **Design Interview** | AI explores requirements and turns vague instructions into concrete specs |
| **Multi-Agent Coordination** | AI team with role-based delegation for planning, execution, verification, and improvement |
| **Quality Verification (Judge Layer)** | AI output is cross-model verified by a separate AI |
| **Approval Flow** | Posting, sending, billing, and deletion always require human approval |
| **Self-Healing DAG** | AI automatically replans and re-executes on failure |
| **Experience Memory** | Accumulates success/failure patterns, improving accuracy with each iteration |
| **Audit Logs** | Full traceability of who did what and why |
| **Extension System** | Add business capabilities via 3-tier Skill / Plugin / Extension |

### 1.3 Goals — How Far We Build

This project sets the following phased goals:

**Phase 1 (v0.2 — 3-month target): Minimum viable product**

- Complete E2E flow from Design Interview -> Spec -> Plan -> Task execution
- Full implementation of Tool Connector (REST API / MCP / CLI tool connections)
- Complete backend connections for all 23 frontend screens
- Implementation of 6 Skills for ai-self-improvement Plugin

**Phase 2 (v0.3 — 6-month target): Advanced AI organization**

- Implementation of meta-skills (ability to learn how to learn)
- A2A (AI-to-AI) bidirectional communication
- Skill marketplace foundation

**Ultimate Goal: AI Self-Improvement**

Safely, transparently, and while preserving human decision-making, achieve the ability for AI to autonomously improve its own Skills, strategies, and quality assessment criteria, and to optimize the improvement process itself.

### 1.4 Architecture — 9-Layer Structure

```
+-------------------------------------------------------------+
| Layer 1: User Layer                                          |
|   Natural language input -> GUI / CLI / TUI / Discord /      |
|   Slack / LINE                                               |
+-------------------------------------------------------------+
| Layer 2: Design Interview                                    |
|   Requirements exploration -> Question generation ->         |
|   Answer accumulation -> Spec creation                       |
+-------------------------------------------------------------+
| Layer 3: Task Orchestrator                                   |
|   Plan generation -> DAG creation -> Skill assignment ->     |
|   Cost estimation                                            |
|   Self-Healing DAG -> Dynamic reconstruction on failure      |
+-------------------------------------------------------------+
| Layer 4: Skill Layer                                         |
|   Built-in Skills -> Plugin Skills -> Gap detection          |
|   Local Context Skill (safe local file reading)              |
+-------------------------------------------------------------+
| Layer 5: Judge Layer                                         |
|   Stage 1: Rule-based fast check (dangerous ops, credential |
|   leaks)                                                     |
|   Stage 2: Cross-Model Verification (verification by        |
|   different model)                                           |
+-------------------------------------------------------------+
| Layer 6: Re-Propose Layer                                    |
|   Rejection -> Plan Diff -> Partial re-execution ->          |
|   Re-proposal                                                |
+-------------------------------------------------------------+
| Layer 7: State & Memory                                      |
|   State machine -> Experience Memory -> Failure Taxonomy     |
|   Artifact Bridge -> Knowledge Refresh                       |
+-------------------------------------------------------------+
| Layer 8: Provider Interface                                  |
|   LiteLLM Gateway -> Ollama direct -> g4f (free)             |
|   Dynamic model catalog -> Deprecated model auto-fallback    |
+-------------------------------------------------------------+
| Layer 9: Skill Registry                                      |
|   Skill / Plugin / Extension publishing, search, install     |
|   Natural language Skill generation -> Safety check ->       |
|   Registration                                               |
+-------------------------------------------------------------+
```

---

## 2. How We Plan to Release

### 2.1 Open Source Release

ZEO is already published on GitHub as an open source project under the **MIT License**.

- Repository: `github.com/OrosiTororo/Zero-Employee-Orchestrator`
- Documentation: 3-language support (Japanese, English, Chinese)
- Community: CONTRIBUTING.md / CODE_OF_CONDUCT.md prepared

### 2.2 Release Plan

| Timeline | Version | Content |
|----------|---------|---------|
| Current | v0.1 | 9-layer architecture foundation, 23-screen UI, Plugin/Extension manifests |
| +3 months | v0.2 | E2E flow complete, Tool Connector implementation, ai-self-improvement Plugin |
| +6 months | v0.3 | Meta-skills, A2A communication, community foundation |
| +12 months | v0.4 | Skill marketplace, multi-user support |
| +18 months | v1.0 | Production quality, governance & compliance |

### 2.3 Post-Project Actions

1. **Community expansion** — Build a Skill / Plugin sharing ecosystem
2. **Academic presentation** — Present research results on multi-agent coordination and AI quality assurance
3. **Enterprise partnerships** — Explore managed service (SaaS version)
4. **Educational use** — Publish AI orchestration teaching materials and tutorials

---

## 3. Innovation Claims and Expected Impact

### 3.1 Comparison with Existing Technologies

| | AutoGPT / CrewAI | n8n / Make / Zapier | **Zero-Employee Orchestrator** |
|---|---|---|---|
| **Input Method** | Text / code | Flow design / node placement | **Natural language only** |
| **AI Team** | Limited (fixed roles) | None (API calls) | **Role-based + dynamic composition** |
| **Quality Assurance** | None or self-evaluation | Rule-based only | **Judge Layer two-stage verification** |
| **Failure Recovery** | Stop or simple retry | Stop | **Self-Healing DAG auto-replanning** |
| **Approval Flow** | None (fully automatic) | Manual setup | **Auto-detection of dangerous ops + mandatory approval** |
| **Experience Learning** | None | None | **Experience Memory + Failure Taxonomy** |
| **Extensibility** | Requires code changes | Plugins (limited) | **Skill / Plugin / Extension 3-tier** |
| **Audit Logs** | None or limited | Limited | **Full operation recording + complete traceability** |
| **Model Selection** | Fixed | Fixed | **Dynamic catalog + automatic quality mode selection** |
| **Cost** | API pay-per-use only | SaaS monthly subscription | **Completely free (local LLM supported)** |

### 3.2 Innovation — What Is New

**1. Architecture that designs AI as an "organization"**

Existing AI agents follow the philosophy of "have one AI do everything." ZEO adopts an **organizational structure where different AI handle planning, execution, verification, and improvement**, structurally guaranteeing quality and reliability.

**2. Judge Layer — AI output verified by a separate AI**

The mechanism where AI-generated output is cross-verified by a different model is equivalent to human double-checking. ZEO-Bench (200-question benchmark) has verified that cross-model verification accuracy exceeds single-model self-evaluation.

**3. Self-Healing DAG — Automatic recovery from failures**

Traditional workflow automation tools halt entirely when a single step fails. ZEO's Self-Healing DAG automatically selects alternative strategies (retry, skip, replan) on failure and continues business operations. Recovery rate and time have been quantitatively verified through chaos tests (20+ fault injections).

**4. AI Self-Improvement — AI improves itself**

ZEO's ultimate goal is achieving the cycle of "AI improving AI." The foundations of Experience Memory and Failure Taxonomy are already implemented, and the ai-self-improvement Plugin design is complete.

**5. Can operate completely free**

Fully offline operation is possible with Ollama (local LLM) + SQLite. All major features are available even with zero cloud API costs.

### 3.3 Expected Impact

| Target | Impact |
|--------|--------|
| **Individual developers / freelancers** | Have an AI team. Automate business, improve quality, save time |
| **Small and medium businesses** | Zero initial cost for AI adoption. Gradually expand automation scope |
| **AI researchers** | Experimental platform for multi-agent coordination, quality assurance, and Self-Improvement |
| **Educational institutions** | Teaching material for AI orchestration. Practical AI utilization learning |
| **Open source community** | Knowledge accumulation through Skill / Plugin sharing ecosystem |

---

## 4. Specific Approach and Budget

### (1) Primary Development Location

Home (Tokyo). Primarily remote work.

### (2) Computing Environment

| Item | Specifications |
|------|---------------|
| **Main development machine** | MacBook / Linux desktop |
| **OS** | macOS / Ubuntu Linux |
| **Local LLM** | Ollama (qwen3:8b, qwen3-coder:30b, etc.) |
| **Database** | SQLite (development) / PostgreSQL (production) |
| **Edge deployment** | Cloudflare Workers (free tier) |
| **CI/CD** | GitHub Actions (free tier) |

### (3) Languages and Tools

| Category | Technology |
|----------|-----------|
| **Backend** | Python 3.12+ / FastAPI / SQLAlchemy 2.x / Alembic |
| **Frontend** | React 19 / TypeScript / Vite / Tailwind CSS / shadcn/ui |
| **Desktop** | Tauri v2 (Rust) |
| **LLM Connection** | LiteLLM / Ollama / g4f |
| **Edge** | Cloudflare Workers / Hono / D1 |
| **Package Management** | uv (Python) / pnpm (Node.js) |
| **Lint / Format** | ruff (Python) / ESLint + Prettier (TypeScript) |
| **Testing** | pytest / pytest-asyncio / Playwright (E2E) |

### (4) Work Distribution

Individual development project. Maximizing development efficiency by leveraging AI agents (Claude Code, etc.).

### (5) Software Development Methodology

- **Agile development** — Progressive feature releases in 2-week sprints
- **Test-driven** — Combining unit tests, integration tests, and chaos tests
- **Document-driven** — Write design documents (DESIGN.md) first, validate through implementation
- **AI-assisted development** — Pair programming with Claude Code

### (6) Development Timeline

```
2026
+--------+--------+--------+--------+--------+--------+
| Apr    | May    | Jun    | Jul    | Aug    | Sep    |
+--------+--------+--------+--------+--------+--------+
| v0.2 Development        | v0.3 Development          |
|                          |                           |
| * E2E flow integration   | * Meta-skill impl         |
| * Tool Connector impl    | * A2A bidirectional comm   |
| * UI data connection     | * Skill marketplace base   |
| * ai-self-improvement    | * RSS/ToS auto-update      |
|   Plugin implementation  | * Avatar co-evolution loop |
| * E2E test construction  | * Community formation      |
| * Worker core logic      |                           |
+--------+--------+--------+--------+--------+--------+

+--------+--------+--------+--------+--------+--------+
| Oct    | Nov    | Dec    | 2027   |        |        |
|        |        |        | Jan    | Feb    | Mar    |
+--------+--------+--------+--------+--------+--------+
| v0.4 Development        | v1.0 Preparation          |
|                          |                           |
| * Skill marketplace      | * Governance & compliance  |
| * Multi-user support     |                           |
| * Web browser automation | * 24/365 long-run exec    |
| * File upload            | * Security audit           |
| * Obsidian integration   | * Documentation complete   |
|                          | * v1.0 release             |
+--------+--------+--------+--------+--------+--------+
```

### (7) Development Hours and Schedule

| Period | Hours | Weekly Hours |
|--------|-------|-------------|
| Weekdays | Evenings (19:00-24:00) | ~25 hours |
| Weekends | All day (10:00-22:00) | ~20 hours |
| **Total** | | **40-45 hours/week** |

By leveraging AI agents (Claude Code), achieving 2-3x productivity compared to traditional development.

### (8) Project Expense Breakdown

| Expense | Details | Amount (Annual) |
|---------|---------|----------------|
| **LLM API usage** | Claude API / OpenAI API (for development/testing) | 120,000 JPY |
| **Cloud infrastructure** | Cloudflare Workers Pro / VPS | 36,000 JPY |
| **Domain / SSL** | Documentation site / demo site | 5,000 JPY |
| **Development tools** | GitHub Pro (CI/CD extension) | 12,000 JPY |
| **GPU resources** | For local model verification (as needed) | 50,000 JPY |
| **Books / conferences** | AI/LLM technical books / attendance fees | 30,000 JPY |
| **Hardware** | GPU-equipped development machine (as needed) | 150,000 JPY |
| **Total** | | **403,000 JPY** |

> **Note**: Basic development is possible with Ollama (local LLM) + SQLite + GitHub free tier.
> The above expenses are for quality improvement, large-scale testing, and community operations.

---

## 5. Demonstrating the Proposer's Capabilities

### 5.1 Project Achievements

Designed and implemented individually as Zero-Employee Orchestrator v0.1:

| Deliverable | Scale |
|-------------|-------|
| **Python backend** | FastAPI-based, 18+ modules, 24 route modules, 40+ API endpoints |
| **React frontend** | 23 screens, TypeScript + Tailwind CSS |
| **Tauri desktop app** | Windows / macOS / Linux compatible |
| **Cloudflare Workers** | Edge deployment (Proxy + Full, 2 methods) |
| **Test suite** | 13 test modules, 20+ chaos test cases, ZEO-Bench 200 questions |
| **Documentation** | 3-language (Japanese, English, Chinese), 20+ documents |
| **CI/CD** | 6 GitHub Actions workflows |

### 5.2 Available Languages and Tools

| Category | Skills |
|----------|--------|
| **Languages** | Python, TypeScript, JavaScript, Rust, SQL |
| **Backend** | FastAPI, SQLAlchemy, Alembic, uvicorn |
| **Frontend** | React, Next.js, Vite, Tailwind CSS, shadcn/ui |
| **Desktop** | Tauri, Electron |
| **AI/LLM** | LiteLLM, Ollama, OpenAI API, Anthropic API, Gemini API |
| **Infrastructure** | Cloudflare Workers, Docker, GitHub Actions |
| **Database** | PostgreSQL, SQLite, D1 |
| **Development tools** | Git, ruff, ESLint, pytest |

### 5.3 AI-Assisted Development Expertise

Established a methodology for designing and implementing large-scale projects as an individual using AI-assisted development with Claude Code. Efficiently progressing development through pair programming with AI agents, from 9-layer architecture design to implementation.

---

## 6. Special Notes for Project Execution

- No plans for enrollment, employment, or job change during the project period
- Environment is prepared for full project dedication
- Ongoing maintenance as an open source project is planned

---

## 7. Studies, Skills, Life, and Hobbies Outside IT

- **Design philosophy**: Strong interest in "trust between AI and humans," pursuing architecture design that ensures AI functions as a human partner without going rogue
- **Multilingual**: Personally writing documentation in Japanese and English. International community formation is in scope
- **Education**: Passionate about communicating AI orchestration concepts in an accessible way; planning to create tutorials and demo videos

---

## 8. Thoughts and Aspirations About the Future of IT

### AI Evolves from "Tool" to "Organization"

Current AI is an excellent "tool." However, just as human organizations can produce results that exceed the sum of individual capabilities, AI operated as a "team" can achieve quality and reliability that single AI cannot reach.

What ZEO aims to build is the operational platform for that "AI organization."

### Safety Cannot Be Added Later

Many AI agent projects take the approach of "build something that works first, think about safety later." However, the more AI becomes embedded in core business operations, the harder it becomes to add safety after the fact.

ZEO **incorporates approval flows, audit logs, and Judge Layer into the architecture from the very beginning**, achieving both safety and functionality. This demonstrates that "safe AI" is not a technical constraint but a matter of design philosophy.

### AI Self-Improvement — Greatest Possibility and Greatest Responsibility

The ability for AI to improve itself brings accelerated technological progress, but also carries risks of loss of control. ZEO's AI Self-Improvement strictly adheres to the following principles:

1. **Human approval is the final authority** — AI proposes, humans decide
2. **Transparency** — Everything about what and how AI improved is recorded and traceable
3. **Reversibility** — All improvements can be rolled back
4. **Gradual delegation** — Users explicitly expand the scope of delegation

AI Self-Improvement based on these principles will realize not "a future where AI runs rogue" but "a future where AI evolves as a human partner."

### Democratization of Software

ZEO is open source. Without depending on expensive SaaS services, anyone can experience AI orchestration completely free using Ollama (local LLM).

The benefits of AI should reach not only large corporations but also individual developers, freelancers, small and medium businesses, and educational institutions. ZEO aims to be the platform that bridges that gap.

**AI works as an organization, evolving itself.
Achieving that cycle safely, transparently, while preserving human decision-making.**

This is the future that Zero-Employee Orchestrator aims for.

---

## Checklist

| # | Item | Status |
|---|------|--------|
| 0 | Title — Technology and challenge identifiable at a glance | OK |
| 1 | What we are building — Background, purpose, goals, architecture diagram | OK |
| 2 | How we plan to release — OSS release, release plan, post-project actions | OK |
| 3 | Innovation claims — Existing tech comparison table, 5 innovations, expected impact | OK |
| 4 | Specific approach and budget — All items (1)-(8) documented | OK |
| 5 | Proposer's capabilities — v0.1 achievements, technical skills, AI-assisted development expertise | OK |
| 6 | Special notes — Project execution environment | OK |
| 7 | Outside IT — Design philosophy, multilingual, interest in education | OK |
| 8 | Future of IT — AI as organization, safety, Self-Improvement, democratization | OK |

---

*Zero-Employee Orchestrator — AI works as an organization.*
