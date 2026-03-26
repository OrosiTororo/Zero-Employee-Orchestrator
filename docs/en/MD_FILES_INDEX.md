> [日本語](../MD_FILES_INDEX.md) | English | [中文](../zh/MD_FILES_INDEX.md)

# Markdown Files Index in the Repository

> Last updated: 2026-03-23 (v0.1)
>
> This document is an index listing the purpose, overview, and intended audience of every `.md` file contained in the Zero-Employee Orchestrator repository.

---

## Table of Contents

1. [Root-Level Documents](#1-root-level-documents)
2. [docs/ — User-Facing Documents](#2-docs--user-facing-documents)
3. [docs/dev/ — Developer Documents](#3-docsdev--developer-documents)
4. [apps/edge/ Documents](#4-appsedge-documents)
5. [.github/ Documents](#5-github-documents)
6. [Multilingual Documents](#6-docsen-and-docszh--multilingual-documents)
7. [Document Reference Priority](#7-document-reference-priority)

---

## 1. Root-Level Documents

### User-Facing

| File | Purpose | Audience | Multilingual |
|------|---------|----------|-------------|
| `README.md` | First-impression document. Overview, features, installation, tech stack | All users and developers | ja/en/zh (inline) |
| `USER_SETUP.md` | Setup guide for using, operating, and extending ZEO | All users | ja / [en](USER_SETUP.md) / [zh](../zh/USER_SETUP.md) |
| `ROADMAP.md` | Roadmap from v0.2 to v1.0 | Users, developers, contributors | ja / [en](ROADMAP.md) / [zh](../zh/ROADMAP.md) |
| `CODE_OF_CONDUCT.md` | Community code of conduct (Contributor Covenant 2.1) | All contributors and users | ja / [en](CODE_OF_CONDUCT.md) / [zh](../zh/CODE_OF_CONDUCT.md) |
| `CONTRIBUTING.md` | How to contribute to the project | Contributors, developers | ja / [en](CONTRIBUTING.md) / [zh](../zh/CONTRIBUTING.md) |
| `SECURITY.md` | Vulnerability reporting procedures | Security reporters | en |

### Developer-Facing (Root)

| File | Purpose | Audience |
|------|---------|----------|
| `CLAUDE.md` | Development guide for Claude Code (AI agent) | Claude Code |

---

## 2. docs/ — User-Facing Documents

| File | Purpose | Audience | Multilingual |
|------|---------|----------|-------------|
| `docs/ABOUT.md` | "Why ZEO is needed" explanatory document | Non-engineers, executives, evaluators | [en](ABOUT.md) / [zh](../zh/ABOUT.md) |
| `docs/USER_GUIDE.md` | End-user operations manual | End users | ja / [en](USER_GUIDE.md) / [zh](../zh/USER_GUIDE.md) |
| `docs/OVERVIEW.md` | Comprehensive guide for first-time visitors | Everyone | [en](OVERVIEW.md) / [zh](../zh/OVERVIEW.md) |
| `docs/FEATURES.md` | Complete implemented feature list (80 sections) | Feature reviewers, evaluators, developers | [en](FEATURES.md) / [zh](../zh/FEATURES.md) |
| `docs/SECURITY.md` | Security policy and pre-deployment checklist | Operators, deployment engineers | [en](SECURITY.md) / [zh](../zh/SECURITY.md) |
| `docs/CHANGELOG.md` | Version-by-version change history | All users and developers | [en](CHANGELOG.md) / [zh](../zh/CHANGELOG.md) |
| `docs/SCALING_AND_COSTS.md` | Costs, hardware constraints, use cases | Prospective adopters, operators, executives | [en](SCALING_AND_COSTS.md) / [zh](../zh/SCALING_AND_COSTS.md) |
| `docs/Zero-Employee Orchestrator.md` | **Top-level reference document**. Philosophy, requirements, MVP | Designers, PO, AI agents | ja |
| `docs/MD_FILES_INDEX.md` | **This document**. Index of all `.md` files | All users and developers | [en](MD_FILES_INDEX.md) / [zh](../zh/MD_FILES_INDEX.md) |

---

## 3. docs/dev/ — Developer Documents

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

## 4. apps/edge/ Documents

| File | Purpose | Audience |
|------|---------|----------|
| `apps/edge/README.md` | Cloudflare Workers deployment comparison (Proxy / Full) | Deployment engineers |
| `apps/edge/full/README.md` | Full Workers setup and deployment | CF Workers developers |
| `apps/edge/proxy/README.md` | Proxy approach setup and deployment | CF Workers developers |

---

## 5. .github/ Documents

| File | Purpose | Audience |
|------|---------|----------|
| `.github/SECURITY_SETUP_CHECKLIST.md` | GitHub Actions security setup checklist | DevOps, security engineers |

---

## 6. docs/en/ and docs/zh/ — Multilingual Documents

`docs/en/` (English) and `docs/zh/` (Chinese) contain translations of the following Japanese documents:

| Japanese Original | English | Chinese |
|-------------------|---------|---------|
| `docs/ABOUT.md` | `docs/en/ABOUT.md` | `docs/zh/ABOUT.md` |
| `docs/OVERVIEW.md` | `docs/en/OVERVIEW.md` | `docs/zh/OVERVIEW.md` |
| `docs/FEATURES.md` | `docs/en/FEATURES.md` | `docs/zh/FEATURES.md` |
| `docs/SECURITY.md` | `docs/en/SECURITY.md` | `docs/zh/SECURITY.md` |
| `docs/SCALING_AND_COSTS.md` | `docs/en/SCALING_AND_COSTS.md` | `docs/zh/SCALING_AND_COSTS.md` |
| `docs/CHANGELOG.md` | `docs/en/CHANGELOG.md` | `docs/zh/CHANGELOG.md` |
| `docs/MD_FILES_INDEX.md` | `docs/en/MD_FILES_INDEX.md` | `docs/zh/MD_FILES_INDEX.md` |
| `docs/USER_GUIDE.md` | `docs/en/USER_GUIDE.md` | `docs/zh/USER_GUIDE.md` |
| `USER_SETUP.md` | `docs/en/USER_SETUP.md` | `docs/zh/USER_SETUP.md` |
| `ROADMAP.md` | `docs/en/ROADMAP.md` | `docs/zh/ROADMAP.md` |
| `CODE_OF_CONDUCT.md` | `docs/en/CODE_OF_CONDUCT.md` | `docs/zh/CODE_OF_CONDUCT.md` |
| `CONTRIBUTING.md` | `docs/en/CONTRIBUTING.md` | `docs/zh/CONTRIBUTING.md` |

---

## 7. Document Reference Priority

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
