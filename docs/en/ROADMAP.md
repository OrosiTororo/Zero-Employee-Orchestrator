> [日本語](../../ROADMAP.md) | English | [中文](../zh/ROADMAP.md)

# Roadmap

> Last updated: 2026-03-18
> Current version: v0.1

---

## Current State (v0.1)

v0.1 includes all features originally planned for v0.2 through v1.0, implemented ahead of schedule.

### Implemented in v0.1

**Foundation:**
- Full 9-layer architecture, ZEO-Bench, Self-Healing DAG, Experience Memory, AI Self-Improvement Plugin

**Connectivity (formerly v0.2):**
- Tool Connector (REST/MCP/GraphQL/CLI/Webhook), iPaaS (n8n/Zapier/Make), Artifact Export, User Input Requests, Resource Import, File Upload API, E2E Test Framework, LLM Response Mocking

**Advanced AI Organization (formerly v0.3):**
- Meta-Skills (Feeling/Seeing/Dreaming/Making/Learning), AI Repurpose Engine, RSS/ToS Monitor, Red-team Security, A2A Communication, Avatar Co-evolution

**Ecosystem (formerly v0.4):**
- Skill Marketplace, Multi-user/Team, Browser Automation, Obsidian Integration, LSP Integration

**Production Quality (formerly v1.0):**
- Governance & Compliance (GDPR/HIPAA/SOC2/ISO27001/CCPA/APPI), 24/365 Scheduler, Cloud Native Integration (AWS/GCP/Azure), Smart Device & VR/AR Hub

**Workspace Isolation & Privacy:**
- Isolated workspace (no local/cloud access by default), internal storage (AI only accesses user-uploaded files), gradual access permission (users can allow local folders/cloud storage via settings), per-task environment customization, chat instruction vs. settings consistency check (AI asks for approval when chat instructions differ from settings), flexible storage location selection

---

## Future Roadmap

The following items require community growth and resource allocation.

### v0.2 — Frontend Completion & Community

| Priority | Feature | Description |
|:--------:|---------|-------------|
| High | **Frontend Data Connection** | Complete 12 screens' backend connections |
| High | **features/ Module Separation** | Extract logic from pages to features/ |
| High | **packages/ Shared Libraries** | Extract and package shared code |
| High | **Plugin Loader Implementation** | Manifest-based dynamic loading |
| Medium | **E2E Flow Integration** | Natural language input to artifact generation |
| Medium | **Playwright Frontend E2E Tests** | Browser UI automated testing |
| Medium | **Worker Core Logic Enhancement** | Strengthen TaskRunner / HeartbeatRunner |

### v0.3 — Accelerating AI Self-Improvement

| Priority | Feature | Description |
|:--------:|---------|-------------|
| High | **Community Skill Ecosystem** | Large-scale Skill/Plugin sharing |
| High | **Anonymous Feedback Aggregation** | Privacy-preserving Experience Memory sharing |
| Medium | **Cross-Model Large-scale Verification** | Massive verification data accumulation |
| Medium | **Multilingual Experience Memory** | Knowledge accumulation in Japanese, English, Chinese, etc. |
| Medium | **Contributor Guide** | CONTRIBUTING.md and Skill development tutorials |

### v1.0 — True AI Self-Improvement

| Priority | Feature | Description |
|:--------:|---------|-------------|
| High | **Self-Improvement Loop** | Auto-cycle: propose → test → verify → apply |
| High | **Cross-Orchestrator Learning** | Knowledge sharing between ZEO instances |
| Medium | **Fine-tuning Infrastructure** | Auto-create specialized domain models |
| Medium | **AI Architecture Self-Improvement** | AI proposes system-design-level improvements |
| Low | **Meta-Learning** | Learning "how to improve efficiently" itself |
