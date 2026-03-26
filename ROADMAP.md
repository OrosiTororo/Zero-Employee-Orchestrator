# Roadmap

> Last updated: 2026-03-26
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

**App Connector Hub:**
- 35+ app integrations (Obsidian, Notion, Logseq, Joplin, Anytype, Roam Research, Google Workspace, Microsoft 365, Jira, Linear, Asana, Trello, ClickUp, HubSpot, Salesforce, etc.)
- Per-connection permission control (read/write/delete/sync/export + path restrictions)
- Custom app registration

**Production Quality (formerly v1.0):**
- Governance & Compliance (GDPR/HIPAA/SOC2/ISO27001/CCPA/APPI), 24/365 Scheduler, Cloud Native Integration (AWS/GCP/Azure), Smart Device & VR/AR Hub

**Quality & Insights:**
- Prerequisite change monitoring, Spec contradiction detection, Task replay & comparison, Judgment review reports, Plan quality verification (MECE)

**Workspace Isolation & Privacy:**
- Isolated workspace (no local/cloud access by default), internal storage only, gradual access permission, per-task environment customization, chat instruction vs. settings consistency check, flexible storage location selection

---

## Future Roadmap

The following items require community growth and resource allocation.

### Features Requiring Community, Funding, or Large-Scale Infrastructure

The following features have code foundations implemented in v0.1, but require user base, hardware, or legal costs for production operation:

| Feature | Required Resources | Current State |
|---------|-------------------|---------------|
| **Marketplace production operation** | User base needed for reviews/install counts | API & UI implemented, awaiting community |
| **VR/AR & IoT integration** | Hardware dependent, device diversity | Protocol abstraction layer implemented |
| **Enterprise governance** | HIPAA/SOC2 certification costs and legal | Policy framework implemented |
| **Large-scale multi-tenant operation** | Infrastructure scaling, operations team | Team & permission models implemented |

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
| High | **Self-Improvement Loop** | Auto-cycle: propose -> test -> verify -> apply |
| High | **Cross-Orchestrator Learning** | Knowledge sharing between ZEO instances |
| Medium | **Fine-tuning Infrastructure** | Auto-create specialized domain models |
| Medium | **AI Architecture Self-Improvement** | AI proposes system-design-level improvements |
| Low | **Meta-Learning** | Learning "how to improve efficiently" itself |
