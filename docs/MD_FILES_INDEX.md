> English | [日本語](ja-JP/MD_FILES_INDEX.md) | [中文](zh/MD_FILES_INDEX.md)

# Markdown Files Index

> Last updated: 2026-03-26 (v0.1)
>
> This document is an index listing the purpose, overview, and intended audience of every `.md` file in the Zero-Employee Orchestrator repository.

---

## Table of Contents

1. [Root-Level Documents](#1-root-level-documents)
2. [docs/ -- User-Facing Documents](#2-docs----user-facing-documents)
3. [docs/dev/ -- Developer Documents](#3-docsdev----developer-documents)
4. [docs/guides/ -- Guide Documents](#4-docsguides----guide-documents)
5. [apps/edge/ Documents](#5-appsedge-documents)
6. [.github/ Documents](#6-github-documents)
7. [Multilingual Documents](#7-multilingual-documents)
8. [Document Reference Priority](#8-document-reference-priority)

---

## 1. Root-Level Documents

### User-Facing

| File | Purpose | Audience |
|------|---------|----------|
| `README.md` | Project overview, features, installation, tech stack | All users and developers |
| `USER_SETUP.md` | Setup guide for using, operating, and extending ZEO | All users |
| `ROADMAP.md` | Roadmap from v0.2 to v1.0 | Users, developers, contributors |
| `CODE_OF_CONDUCT.md` | Community code of conduct (Contributor Covenant 2.1) | All contributors and users |
| `CONTRIBUTING.md` | How to contribute to the project | Contributors, developers |
| `SECURITY.md` | Vulnerability reporting procedures | Security reporters |

### Developer-Facing (Root)

| File | Purpose | Audience |
|------|---------|----------|
| `CLAUDE.md` | Development guide for Claude Code (AI agent) | Claude Code |

---

## 2. docs/ -- User-Facing Documents

The base language for `docs/` is English. Translations are in language-specific subdirectories.

| File | Purpose | Audience |
|------|---------|----------|
| `docs/ABOUT.md` | "Why ZEO is needed" -- explanatory document | Non-engineers, executives, evaluators |
| `docs/USER_GUIDE.md` | End-user operations manual | End users |
| `docs/OVERVIEW.md` | Comprehensive guide for first-time visitors | Everyone |
| `docs/FEATURES.md` | Complete implemented feature list (80 sections) | Feature reviewers, evaluators, developers |
| `docs/SECURITY.md` | Security policy and pre-deployment checklist | Operators, deployment engineers |
| `docs/CHANGELOG.md` | Version-by-version change history | All users and developers |
| `docs/SCALING_AND_COSTS.md` | Costs, hardware constraints, use cases | Prospective adopters, operators, executives |
| `docs/Zero-Employee Orchestrator.md` | **Top-level reference document**. Philosophy, requirements, MVP (Japanese) | Designers, PO, AI agents |
| `docs/MD_FILES_INDEX.md` | **This document**. Index of all `.md` files | All users and developers |

---

## 3. docs/dev/ -- Developer Documents

| File | Purpose | Audience |
|------|---------|----------|
| `docs/dev/DESIGN.md` | Implementation design (DB, API, state transitions, phases) | Implementers, AI agents |
| `docs/dev/MASTER_GUIDE.md` | AI implementation approach, reference order, decision criteria | AI agents, implementation leads |
| `docs/dev/BUILD_GUIDE.md` | Build from scratch guide (phase-by-phase) | Developers building from source |
| `docs/dev/FEATURE_BOUNDARY.md` | Core features vs Skill/Plugin/Extension boundary definition | Developers, designers |
| `docs/dev/DEVELOPER_SETUP.md` | Developer setup (Sentry, red-team testing, etc.) | ZEO developers |
| `docs/dev/SKILL.md` | SKILL.md file creation guide | Skill developers |
| `docs/dev/PROPOSAL.md` | Project proposal document | Grant reviewers, sponsors |
| `docs/dev/AI_SELF_IMPROVEMENT_ROADMAP.md` | AI self-improvement roadmap | Developers, researchers |

---

## 4. docs/guides/ -- Guide Documents

| File | Purpose | Audience |
|------|---------|----------|
| `docs/guides/quickstart-guide.md` | Installation, first workflow, CLI basics | New users |
| `docs/guides/architecture-guide.md` | 9-layer architecture deep dive | Developers, architects |
| `docs/guides/security-guide.md` | Security architecture and best practices | Security engineers, operators |

---

## 5. apps/edge/ Documents

| File | Purpose | Audience |
|------|---------|----------|
| `apps/edge/README.md` | Cloudflare Workers deployment comparison (Proxy / Full) | Deployment engineers |
| `apps/edge/full/README.md` | Full Workers setup and deployment | CF Workers developers |
| `apps/edge/proxy/README.md` | Proxy approach setup and deployment | CF Workers developers |

---

## 6. .github/ Documents

| File | Purpose | Audience |
|------|---------|----------|
| `.github/SECURITY_SETUP_CHECKLIST.md` | Pre-release security setup checklist | DevOps, security engineers |
| `.github/copilot-instructions.md` | Copilot coding instructions | GitHub Copilot |

---

## 7. Multilingual Documents

The base language is **English** (at `docs/` root and repository root). Translations are organized in language-specific subdirectories:

| Language | Directory | Contents |
|----------|-----------|----------|
| Japanese | `docs/ja-JP/` | ABOUT, USER_GUIDE, OVERVIEW, FEATURES, SECURITY, CHANGELOG, SCALING_AND_COSTS, MD_FILES_INDEX, README |
| Chinese (Simplified) | `docs/zh/` | ABOUT, USER_GUIDE, OVERVIEW, FEATURES, SECURITY, CHANGELOG, SCALING_AND_COSTS, MD_FILES_INDEX, ROADMAP, CODE_OF_CONDUCT, CONTRIBUTING, USER_SETUP |
| Chinese (Simplified) | `docs/zh-CN/` | README |
| Chinese (Traditional) | `docs/zh-TW/` | README |
| Korean | `docs/ko-KR/` | README |
| Portuguese (Brazil) | `docs/pt-BR/` | README |
| Turkish | `docs/tr/` | README |

---

## 8. Document Reference Priority

### For Developers and Implementers

```
1. docs/Zero-Employee Orchestrator.md  <- Top-level reference (philosophy, requirements, MVP)
2. docs/dev/DESIGN.md                  <- Implementation design (DB, API, state transitions)
3. docs/dev/MASTER_GUIDE.md            <- Operational guide (approach, criteria, prohibitions)
4. CLAUDE.md                           <- AI agent development guide
5. docs/dev/BUILD_GUIDE.md             <- Build from scratch guide (phase-by-phase)
```

### For Users

```
First-time visitors  -> docs/OVERVIEW.md
Why it's needed      -> docs/ABOUT.md
Setup                -> USER_SETUP.md or docs/USER_GUIDE.md
Feature review       -> docs/FEATURES.md
Costs & constraints  -> docs/SCALING_AND_COSTS.md
Deployment           -> apps/edge/README.md + docs/SECURITY.md
Change history       -> docs/CHANGELOG.md
```

---

*This index corresponds to Section 11 "Document List" in `docs/OVERVIEW.md`.*
