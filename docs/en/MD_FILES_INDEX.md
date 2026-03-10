> [日本語](../MD_FILES_INDEX.md) | English | [中文](../zh/MD_FILES_INDEX.md)

# Markdown Files Index in the Repository

> Last updated: 2026-03-10 (v0.1)
>
> This document is an index listing the purpose, overview, and intended audience of every `.md` file contained in the Zero-Employee Orchestrator repository.

---

## Table of Contents

1. [Root-Level Documents](#1-root-level-documents)
2. [docs/ — User-Facing Documents](#2-docs--user-facing-documents)
3. [docs/dev/ — Developer Documents](#3-docsdev--developer-documents)
4. [apps/edge/ Documents](#4-appsedge-documents)
5. [.github/ Documents](#5-github-documents)
6. [Document Reference Priority](#6-document-reference-priority)

---

## 1. Root-Level Documents

### `README.md`

| Item | Description |
|------|-------------|
| **Location** | `/README.md` |
| **Purpose** | The first-impression document for the project. Summarizes the overview, key features, installation steps, and technology stack |
| **Audience** | All users and developers |
| **Key Contents** | Trilingual support (Japanese, English, Chinese). Installation instructions for both the GUI version (desktop installer) and CLI version, technology stack table, quick-start commands |

---

### `CLAUDE.md`

| Item | Description |
|------|-------------|
| **Location** | `/CLAUDE.md` |
| **Purpose** | Development guide for Claude Code (AI coding agent). Condenses the entire project overview into a single file |
| **Audience** | Claude Code (AI agent) |
| **Key Contents** | 9-layer architecture definition, technology stack, directory structure, coding conventions, design principles, DB schema overview, all API endpoints, runtime configuration management, supported LLM models, Ollama integration, Skill management v0.1, prohibited actions |

---

## 2. docs/ — User-Facing Documents

Documents intended for users (end users, evaluators, operators), or shared between users and developers.

### `docs/ABOUT.md`

| Item | Description |
|------|-------------|
| **Location** | `/docs/ABOUT.md` |
| **Purpose** | A marketing and explanatory document articulating "Why Zero-Employee Orchestrator is needed" |
| **Audience** | Non-engineers, executives, product evaluators |
| **Key Contents** | Comparison tables with other AI agents, RPA, and n8n/Make; 9 competitive advantages; enterprise readiness |

---

### `docs/USER_GUIDE.md`

| Item | Description |
|------|-------------|
| **Location** | `/docs/USER_GUIDE.md` |
| **Purpose** | End-user manual covering setup through daily operations |
| **Audience** | End users (both engineers and non-engineers) |
| **Key Contents** | Trilingual support (Japanese, English, Chinese). System requirements, LLM connection methods, installation steps, descriptions and usage of all screens, how to use tickets, approval workflow, Skill/Plugin extension methods, cost management, troubleshooting, FAQ |

---

### `docs/OVERVIEW.md`

| Item | Description |
|------|-------------|
| **Location** | `/docs/OVERVIEW.md` |
| **Purpose** | A comprehensive guide explaining the philosophy, features, and structure for those encountering the project for the first time |
| **Audience** | First-time visitors (both engineers and non-engineers) |
| **Key Contents** | What is ZEO (comparison table with other tools), why it's needed, basic usage, 9-layer architecture details, technology stack list, implementation status, offline operation, boundary between core and extension features, external tool integration, design considerations, document list, directory structure |

---

### `docs/FEATURES.md`

| Item | Description |
|------|-------------|
| **Location** | `/docs/FEATURES.md` |
| **Purpose** | A comprehensive feature list covering all implemented functionality |
| **Audience** | Feature reviewers, evaluators, developers |
| **Key Contents** | 27-section structure. 9-layer architecture feature details, Design Interview, Spec/Plan/Tasks, DAG-based Task Orchestrator, state machine, Judge Layer, Self-Healing/Re-Propose, approval workflow, audit logs, Skill/Plugin/Extension 3-tier extension system, LLM Gateway, frontend UI (21 screens), REST API, WebSocket |

---

### `docs/SECURITY.md`

| Item | Description |
|------|-------------|
| **Location** | `/docs/SECURITY.md` |
| **Purpose** | Security policy and pre-deployment checklist |
| **Audience** | Operators, deployment engineers |
| **Key Contents** | Supported versions table, vulnerability reporting procedure, deployment security checklist (SECRET_KEY / JWT_SECRET generation methods, Cloudflare credentials, CORS configuration, production DB settings, recommended security settings) |

---

### `docs/CHANGELOG.md`

| Item | Description |
|------|-------------|
| **Location** | `/docs/CHANGELOG.md` |
| **Purpose** | Version-by-version change history |
| **Audience** | All users and developers |
| **Key Contents** | [Keep a Changelog](https://keepachangelog.com/) format. Complete list of all additions in v0.1.0 (2026-03-10) |

---

### `docs/Zero-Employee Orchestrator.md`

| Item | Description |
|------|-------------|
| **Location** | `/docs/Zero-Employee Orchestrator.md` |
| **Purpose** | The project's **top-level reference document**. The definitive source integrating philosophy, requirements, MVP definition, operational policies, and implementation decision criteria |
| **Audience** | Designers, product owners, AI agents |
| **Key Contents** | Definitions and distinctions of Skill / Plugin / Extension, problems the system solves, design philosophy, MVP required features vs. deferred features, state transition design, approval workflow requirements, audit log requirements, extension architecture, Self-Healing DAG requirements |
| **Note** | Filename contains spaces |

---

### `docs/SCALING_AND_COSTS.md`

| Item | Description |
|------|-------------|
| **Location** | `/docs/SCALING_AND_COSTS.md` |
| **Purpose** | A guide covering costs, hardware constraints, and large-scale project use cases |
| **Audience** | Prospective adopters, operators, executives |
| **Key Contents** | LLM API cost list, free-tier scope, hardware requirements, v0.1 unimplemented features, 5 large-scale project use cases, cost optimization strategies |

---

### `docs/MD_FILES_INDEX.md`

| Item | Description |
|------|-------------|
| **Location** | `/docs/MD_FILES_INDEX.md` |
| **Purpose** | **This document**. An index listing all `.md` files in the repository |
| **Audience** | All users and developers |

---

## 3. docs/dev/ — Developer Documents

Documents intended for developers, implementers, and AI coding agents.

### `docs/dev/DESIGN.md`

| Item | Description |
|------|-------------|
| **Location** | `/docs/dev/DESIGN.md` |
| **Purpose** | Implementation design document. The core design specification organized at a granularity suitable for AI coding agents to begin implementation |
| **Audience** | Implementers, AI agents |
| **Key Contents** | System definition, design principles, DB table design (all column definitions), API endpoint list, state transitions (State Machine), UI screen design, implementation phases (Phase 0-9), MVP boundary |

---

### `docs/dev/MASTER_GUIDE.md`

| Item | Description |
|------|-------------|
| **Location** | `/docs/dev/MASTER_GUIDE.md` |
| **Purpose** | An operational guide summarizing the approach to implementation by AI coding agents, reference order, and decision criteria |
| **Audience** | AI agents, implementation leads |
| **Key Contents** | 6 most important rules, correspondence table of each file's role and usage, how to proceed through implementation phases, prohibited actions, decision flow when uncertain |

---

### `docs/dev/BUILD_GUIDE.md`

| Item | Description |
|------|-------------|
| **Location** | `/docs/dev/BUILD_GUIDE.md` |
| **Purpose** | A build guide explaining how to construct Zero-Employee Orchestrator from scratch, with code examples for each phase |
| **Audience** | Developers building from source |
| **Key Contents** | Prerequisites, quick-setup commands, step-by-step implementation instructions for Phase 0-9, deployment procedures |

---

### `docs/dev/FEATURE_BOUNDARY.md`

| Item | Description |
|------|-------------|
| **Location** | `/docs/dev/FEATURE_BOUNDARY.md` |
| **Purpose** | A boundary definition document explicitly delineating core features vs. Skill / Plugin / Extension |
| **Audience** | Developers, designers |
| **Key Contents** | Boundary judgment criteria, detailed list of core features, list of features to be extracted as Skill/Plugin/Extension |

---

### Implementation Instruction Files (`instructions_section*`)

Implementation instruction files are specific directive documents used by AI coding agents when implementing each phase.

| File | Location | Contents |
|------|----------|----------|
| **instructions_section2_init.md** | `/docs/dev/` | Repository initialization (directory structure, monorepo configuration, environment setup) |
| **instructions_section3_backend.md** | `/docs/dev/` | FastAPI backend construction (MVP priority implementation items, SQLAlchemy models, state machine) |
| **instructions_section4_frontend.md** | `/docs/dev/` | React frontend construction (screen list, component design guidelines, API connectivity) |
| **instructions_section5_skills.md** | `/docs/dev/` | Skills / Plugins / Extensions implementation (terminology definitions, built-in Skills, Registry API) |
| **instructions_section6_tauri.md** | `/docs/dev/` | Tauri integration and desktop application packaging (sidecar startup, auto-update) |
| **instructions_section7_test.md** | `/docs/dev/` | Testing and verification (state transition tests, approval bypass prevention tests, security tests) |

---

## 4. apps/edge/ Documents

### `apps/edge/README.md`

| Item | Description |
|------|-------------|
| **Location** | `/apps/edge/README.md` |
| **Purpose** | Comparison and selection guide for two Cloudflare Workers deployment approaches (Proxy / Full Workers) |
| **Audience** | Deployment engineers, infrastructure engineers |

---

### `apps/edge/full/README.md`

| Item | Description |
|------|-------------|
| **Location** | `/apps/edge/full/README.md` |
| **Purpose** | Setup and deployment procedure for Approach B (Full Workers) |
| **Audience** | Developers running full-stack on Cloudflare Workers |

---

### `apps/edge/proxy/README.md`

| Item | Description |
|------|-------------|
| **Location** | `/apps/edge/proxy/README.md` |
| **Purpose** | Setup and deployment procedure for Approach A (Proxy) |
| **Audience** | Developers placing Workers in front of an existing FastAPI backend |

---

## 5. .github/ Documents

### `.github/SECURITY_SETUP_CHECKLIST.md`

| Item | Description |
|------|-------------|
| **Location** | `/.github/SECURITY_SETUP_CHECKLIST.md` |
| **Purpose** | Security setup checklist for GitHub Actions |
| **Audience** | DevOps, security engineers |
| **Key Contents** | Required Secrets and configuration items, security recommendations |

---

## 6. Document Reference Priority

### For Developers and Implementers

```
1. docs/Zero-Employee Orchestrator.md  <- Top-level reference (philosophy, requirements, MVP definition)
2. docs/dev/DESIGN.md                  <- Implementation design (DB, API, state transitions, implementation order)
3. docs/dev/MASTER_GUIDE.md            <- Operational guide (approach, decision criteria, prohibited actions)
4. CLAUDE.md                           <- AI agent development guide
5. docs/dev/instructions_section2-7    <- Specific implementation instructions for each domain
```

### For Users

```
First-time visitors  -> docs/OVERVIEW.md
Why it's needed      -> docs/ABOUT.md
Setup                -> docs/USER_GUIDE.md or docs/dev/BUILD_GUIDE.md
Feature review       -> docs/FEATURES.md
Costs & constraints  -> docs/SCALING_AND_COSTS.md
Deployment           -> apps/edge/README.md + docs/SECURITY.md
Change history       -> docs/CHANGELOG.md
```

---

*This index corresponds to Section 11 "Document List" in `docs/OVERVIEW.md`.*
