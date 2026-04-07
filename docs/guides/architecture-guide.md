[← Back to README](../../README.md)

# Architecture Deep Dive

> Zero-Employee Orchestrator — 9-Layer AI Orchestration Architecture

---

## Table of Contents

- [Overview](#overview)
- [9-Layer Architecture](#9-layer-architecture)
  - [Layer 1: User Layer](#layer-1-user-layer)
  - [Layer 2: Design Interview](#layer-2-design-interview)
  - [Layer 3: Task Orchestrator](#layer-3-task-orchestrator)
  - [Layer 4: Skill Layer](#layer-4-skill-layer)
  - [Layer 5: Judge Layer](#layer-5-judge-layer)
  - [Layer 6: Re-Propose](#layer-6-re-propose)
  - [Layer 7: State & Memory](#layer-7-state--memory)
  - [Layer 8: Provider Interface](#layer-8-provider-interface)
  - [Layer 9: Skill Registry](#layer-9-skill-registry)
- [Self-Healing DAG](#self-healing-dag)
- [Judge Layer Deep Dive](#judge-layer-deep-dive)
- [Experience Memory](#experience-memory)
- [A2A Communication](#a2a-communication)
- [Meta-Skills](#meta-skills)
- [3-Tier Extensibility](#3-tier-extensibility)
- [Model Catalog](#model-catalog)
- [Data Flow](#data-flow)

---

## Overview

ZEO is designed as a **9-layer architecture** that transforms natural language business requirements into executable, verifiable, and improvable AI workflows. Unlike simple prompt-chaining frameworks, ZEO treats AI as an organization with role-based delegation, quality verification, and institutional memory.

```
┌──────────────────────────────────────────────────────────┐
│                    User Input (NL)                        │
│                         ↓                                │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  1. User Layer        GUI / CLI / TUI               │ │
│  │  2. Design Interview  Requirements exploration      │ │
│  │  3. Task Orchestrator  DAG decomposition & cost est. │ │
│  │  4. Skill Layer       Specialized execution          │ │
│  │  5. Judge Layer       Two-stage verification         │ │
│  │  6. Re-Propose        Dynamic DAG rebuild            │ │
│  │  7. State & Memory    Experience Memory              │ │
│  │  8. Provider          LLM Gateway (LiteLLM)         │ │
│  │  9. Skill Registry    Publish / Search / Import     │ │
│  └─────────────────────────────────────────────────────┘ │
│                         ↓                                │
│                  Verified Output                         │
└──────────────────────────────────────────────────────────┘
```

---

## 9-Layer Architecture

### Layer 1: User Layer

The entry point for all interactions. Supports multiple interfaces:

| Interface | Description | Port |
|-----------|-------------|------|
| **Web UI** | React 19 + Tauri v2 desktop app | 5173 (dev) |
| **REST API** | FastAPI with 46 route modules, 387 endpoints | 18234 |
| **CLI** | `zero-employee` command with chat, serve, config subcommands | — |
| **WebSocket** | Real-time event streaming and browser assist | 18234 |

All input is natural language. Users describe business workflows, and ZEO decomposes them into executable tasks.

### Layer 2: Design Interview

An interactive requirements exploration phase (壁打ち — "bouncing ideas off a wall").

```
User: "I want to automate our weekly report"
  ↓
Design Interview:
  → What data sources?
  → Who are the stakeholders?
  → What format? (PDF, Slack, email)
  → What approval flow?
  → What's the budget for LLM calls?
  ↓
Structured Specification
```

The Design Interview ensures ambiguous requests are refined before execution. It produces:

- **Spec** — Structured requirement document
- **Plan** — Execution strategy with cost estimates
- **Task breakdown** — Individual executable units

### Layer 3: Task Orchestrator

The core scheduling engine. Decomposes plans into a **Directed Acyclic Graph (DAG)** of tasks.

```
         ┌──── Task A ────┐
         │                 │
Start ───┤                 ├──── Task D ──── End
         │                 │
         └──── Task B ─────┘
                │
                └──── Task C ────────────────┘
```

Key capabilities:

| Feature | Description |
|---------|-------------|
| **DAG decomposition** | Breaks plans into parallel/sequential task graphs |
| **Cost estimation** | Pre-calculates LLM token costs per task |
| **Quality mode switching** | quality / speed / cost / free / subscription modes |
| **Dynamic scheduling** | Adjusts execution order based on dependencies and failures |
| **Budget awareness** | Respects cost limits and alerts on overruns |

### Layer 4: Skill Layer

Specialized execution units with domain knowledge.

**Built-in Skills (8):**

| Skill | Purpose |
|-------|---------|
| `spec-writer` | Generates structured specifications |
| `plan-writer` | Creates execution plans |
| `task-breakdown` | Decomposes tasks into subtasks |
| `review-assistant` | Reviews and critiques outputs |
| `artifact-summarizer` | Summarizes intermediate artifacts |
| `local-context` | Injects project-specific context |
| `domain-skills` | Domain-specific knowledge |
| `browser-assist` | Browser automation and screen analysis |

Each skill receives **Local Context** — project-specific information that helps the AI understand the user's environment.

### Layer 5: Judge Layer

Quality verification using a **Two-stage + Cross-Model** approach.

```
              Output from Skill
                    ↓
        ┌─── Stage 1: Rule-based ───┐
        │   Fast pattern matching    │
        │   28+ detection rules      │
        │   Format validation        │
        └───────────┬───────────────┘
                    ↓
              Pass? ──── No → Re-Propose (Layer 6)
                    ↓ Yes
        ┌─── Stage 2: Cross-Model ──┐
        │   Different LLM verifies   │
        │   Semantic quality check   │
        │   Factual consistency      │
        └───────────┬───────────────┘
                    ↓
              Pass? ──── No → Re-Propose (Layer 6)
                    ↓ Yes
              Approved Output
```

### Layer 6: Re-Propose

When the Judge Layer rejects an output, Re-Propose handles recovery:

1. **Analyze failure** — Categorize the rejection reason
2. **Update DAG** — Dynamically reconstruct the task graph
3. **Re-assign** — May switch to a different Skill or LLM model
4. **Retry with context** — Include failure information for improved next attempt

This creates a **self-healing loop** — tasks automatically recover from failures without human intervention (within safety boundaries).

### Layer 7: State & Memory

Persistent state management with learning capabilities.

**Experience Memory** stores:

```json
{
  "task_type": "report_generation",
  "model_used": "anthropic/claude-opus",
  "execution_mode": "quality",
  "success": true,
  "duration_ms": 4200,
  "token_cost": 0.045,
  "quality_score": 0.92,
  "failure_taxonomy": null,
  "context_hash": "abc123",
  "lessons_learned": ["Include data source citations"]
}
```

**Failure Taxonomy** categorizes errors for pattern recognition:

| Category | Example |
|----------|---------|
| `model_limitation` | Token limit exceeded |
| `context_insufficient` | Missing required information |
| `quality_below_threshold` | Judge rejected output |
| `external_dependency` | API timeout |
| `safety_violation` | Prompt injection detected |

### Layer 8: Provider Interface

LLM gateway powered by LiteLLM with intelligent routing.

```
                Request
                  ↓
        ┌── Model Catalog ──┐
        │  model_catalog.json │
        │  Family-based IDs   │
        │  Auto-version resolve│
        └────────┬───────────┘
                 ↓
        ┌── Router ──────────┐
        │  Quality mode      │
        │  Cost optimization │
        │  Fallback chains   │
        │  Rate limiting     │
        └────────┬───────────┘
                 ↓
    ┌────────┬───────┬────────┐
    │        │       │        │
  Claude   GPT   Gemini   Ollama
```

**Execution Modes:**

| Mode | Use Case | Example Models |
|------|----------|----------------|
| `quality` | High-stakes tasks | Claude Opus, GPT, Gemini Pro |
| `speed` | Fast iteration | Claude Haiku, GPT Mini, Gemini Flash |
| `cost` | Budget-conscious | Haiku, Mini, Flash Lite, DeepSeek |
| `free` | No API cost | Ollama local models |
| `subscription` | No key needed | via g4f |

### Layer 9: Skill Registry

Community-driven skill ecosystem.

| Operation | API Endpoint |
|-----------|-------------|
| **Publish** | `POST /api/v1/registry/skills` |
| **Search** | `GET /api/v1/registry/skills/search` |
| **Import** | `POST /api/v1/registry/skills/import` |
| **Generate** | `POST /api/v1/registry/skills/generate` |

Natural language skill generation includes **18 dangerous pattern checks** before registration.

---

## Self-Healing DAG

The Self-Healing DAG is ZEO's automatic recovery mechanism.

```
Normal Flow:
  Task A → Task B → Task C → Done ✓

Failure Flow:
  Task A → Task B → ✗ FAIL
                     ↓
              Analyze Failure
                     ↓
              Re-Propose (new DAG)
                     ↓
  Task A → Task B' → Task C' → Done ✓
```

**How it works:**

1. **Detection** — Judge Layer identifies quality issues
2. **Classification** — Failure Taxonomy categorizes the error
3. **Strategy selection** — Choose recovery approach:
   - **Retry** — Same task, different prompt or temperature
   - **Re-route** — Different model or skill
   - **Decompose** — Break failed task into smaller subtasks
   - **Escalate** — Request human input via approval gate
4. **DAG reconstruction** — Build new execution graph
5. **Memory update** — Record failure and recovery for future reference

---

## Judge Layer Deep Dive

### Stage 1: Rule-Based Detection

Fast, deterministic checks:

- Format validation (JSON schema, markdown structure)
- Length and completeness checks
- Prohibited content detection
- Code syntax verification
- Data consistency checks

### Stage 2: Cross-Model Verification

A different LLM model evaluates the output:

- Semantic coherence assessment
- Factual consistency check
- Task requirement alignment
- Quality scoring (0.0 — 1.0)

**Why cross-model?** Using a different model family reduces bias. If Claude generated the output, GPT or Gemini verifies it, and vice versa.

---

## Experience Memory

### Learning Cycle

```
Execute Task → Judge Evaluates → Store Result
      ↑                              ↓
      └──── Apply Lessons ←── Analyze Patterns
```

### What it learns:

- **Model performance** per task type (which model works best for what)
- **Cost efficiency** patterns (speed vs. quality trade-offs)
- **Failure patterns** (common failure modes and their solutions)
- **Context requirements** (what context is needed for task types)

---

## A2A Communication

Agent-to-Agent (A2A) protocol for peer-to-peer messaging:

| Feature | Description |
|---------|-------------|
| **Direct messaging** | Point-to-point agent communication |
| **Channels** | Topic-based group communication |
| **Negotiation** | Multi-agent consensus for complex decisions |
| **Broadcast** | System-wide announcements |

---

## Meta-Skills

AI capabilities for learning how to learn:

| Meta-Skill | Description |
|------------|-------------|
| **Feeling** | Sentiment and context awareness |
| **Seeing** | Pattern recognition across tasks |
| **Dreaming** | Hypothetical scenario generation |
| **Making** | Creative problem-solving |
| **Learning** | Self-improvement from experience |

---

## 3-Tier Extensibility

```
┌─────────────────────────────────┐
│  Extension                       │
│  (System integration)            │
│  ┌───────────────────────────┐  │
│  │  Plugin                    │  │
│  │  (Skill bundles)           │  │
│  │  ┌─────────────────────┐  │  │
│  │  │  Skill               │  │  │
│  │  │  (Single purpose)    │  │  │
│  │  └─────────────────────┘  │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

| Tier | Count | Purpose | Examples |
|------|-------|---------|---------|
| **Skill** | 8 built-in | Single-purpose processing | spec-writer, review-assistant |
| **Plugin** | 10 | Bundle multiple skills | ai-secretary, youtube |
| **Extension** | 5 | System integration | mcp, oauth, notifications |

---

## Model Catalog

Models are managed by **family ID**, not version-pinned:

```json
{
  "family_id": "anthropic/claude-opus",
  "latest_model_id": "claude-opus-4-6",
  "execution_modes": ["quality"],
  "provider": "anthropic"
}
```

When a new model version releases, only `latest_model_id` needs updating — no code changes required. `ModelRegistry.resolve_api_id()` handles the family → version resolution automatically.

---

## Data Flow

Complete request lifecycle:

```
User Input (NL)
    ↓
[1] User Layer — Parse input, route to appropriate handler
    ↓
[2] Design Interview — Refine requirements (if needed)
    ↓
[3] Task Orchestrator — Build DAG, estimate costs
    ↓
[4] Skill Layer — Execute tasks with domain context
    ↓
[5] Judge Layer — Verify quality (two-stage)
    ↓ (fail → [6] Re-Propose → back to [3] or [4])
[7] State & Memory — Store results, update experience
    ↓
[8] Provider — LLM calls routed through gateway
    ↓
[9] Registry — Skills resolved from registry
    ↓
Verified Output → User
```

---

## Further Reading

- [Quickstart Guide](quickstart-guide.md) — Get up and running
- [Security Guide](security-guide.md) — Security architecture details
- [Main README](../../README.md) — Project overview
