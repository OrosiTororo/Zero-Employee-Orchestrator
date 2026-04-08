# ZEO Positioning: vs Autonomous AI Agents

> Updated: 2026-04-08
> Context: Copilot Cowork (Microsoft, March 2026), Claude Cowork (Anthropic, January 2026)

---

## 1. Landscape: Three Paradigms of AI Agents

### 1.1 Desktop Autonomous Agent (Claude Cowork)
- Runs locally on macOS, sandboxed file access
- Executes multi-step workflows on local files
- Chrome extension for browser automation (workflow recording, scheduled tasks, multi-tab)
- Single-model (Claude), single-user, individual-first
- $20–200/month subscription

### 1.2 Enterprise Graph Agent (Copilot Cowork)
- Runs in Microsoft 365 cloud, integrated into Outlook/Teams/Excel/SharePoint
- Work IQ: understands organizational context (emails, meetings, files, chats)
- Task statuses: In Progress → Needs Input → Done / Failed
- Plan → Approve checkpoints → Execute → Steer
- Enterprise governance: permission scopes, approval workflows, execution logging
- $30–55/user/month (E3/E5/Frontier license)

### 1.3 Meta-Orchestrator (ZEO) — Our Position
- **Orchestrator of orchestrators**: doesn't replace AI tools, unifies them
- Connects CrewAI, AutoGen, LangChain, Dify as sub-workers under approval gates
- Connects n8n, Zapier, Make as automation backends
- 34+ app connectors, 22 model families, multi-provider
- Free and open source; users pay LLM providers directly
- Self-hostable (Docker, Cloudflare Workers, Tauri desktop)

---

## 2. ZEO's Unique Value Proposition

| Dimension | Claude Cowork | Copilot Cowork | ZEO |
|-----------|--------------|----------------|-----|
| **Model freedom** | Claude only | Claude+GPT (MS choice) | 22 families, user's choice |
| **Self-hosting** | No | No | Yes (Docker, edge, desktop) |
| **Cost** | $20-200/mo | $30-55/user/mo | Free (pay LLM providers) |
| **Offline mode** | No | No | Yes (Ollama) |
| **Meta-orchestration** | No | No | Yes (CrewAI, AutoGen, Dify, n8n) |
| **Security layers** | Sandbox + approval | M365 governance | 14-layer defense |
| **Browser automation** | Chrome extension (full) | Within M365 apps | Browser Assist (guidance + tiered approval) |
| **Enterprise governance** | Basic | Deep (Work IQ, RBAC) | Approval gates + autonomy boundaries |
| **App ecosystem** | macOS local apps | M365 suite | 34+ apps via connectors |

---

## 3. Adopted Features (採長補短)

### 3.1 From Copilot Cowork (Adopted in v0.1.5)

| Feature | Copilot Cowork | ZEO Implementation |
|---------|---------------|-------------------|
| **Plan preview** | Plan → Review → Execute | `preview_only=true` in dispatch, plan step display |
| **Needs Input checkpoint** | Task pauses, asks user | `needs_input` status + resume endpoint |
| **Steering** | Interrupt & redirect mid-task | `/dispatch/{id}/steer` endpoint |
| **Status indicators** | In Progress, Needs Input, Done, Failed | 7 statuses with color-coded badges |
| **Task tabs** | Active / Scheduled / Done | Active / Done / All tabs in DispatchPage |
| **Approval preview** | Shows what action will do | `generate_preview()` + risk badge in UI |
| **CLI task management** | N/A (GUI only) | `/dispatch`, `/tasks`, `/status`, `/approve`, `/reject`, `/cancel` |

### 3.2 From Claude Cowork (Architectural Alignment)

| Feature | Claude Cowork | ZEO Approach |
|---------|-------------|--------------|
| **Local file sandbox** | Sandboxed folder access | `sandbox.py` — 3 security levels, whitelist paths |
| **Chrome extension** | Native messaging + workflow recording | Browser Assist — overlay chat + screenshot analysis |
| **Background execution** | Runs while user works | Dispatch system — fire-and-forget with status polling |
| **Multi-step planning** | DAG-style decomposition | `executor.py` — DAG with parallel node execution |

### 3.3 Not Adopted (By Design)

| Feature | Why Not |
|---------|---------|
| **Desktop-native file editing** | ZEO is a meta-orchestrator, not a desktop agent. File ops go through sandbox. |
| **Work IQ (org graph)** | Requires deep M365 integration. ZEO connects to apps via connectors instead. |
| **Single-vendor model lock-in** | Counter to ZEO's multi-model philosophy. |
| **Closed-source execution** | ZEO is open source with full audit trail transparency. |

---

## 4. ZEO Browser Assist vs Claude Chrome Extension

### Current State
ZEO Browser Assist is an **advisory overlay** — screenshot analysis + guidance, not autonomous control:
- Chrome extension with floating chat widget
- Multimodal LLM screenshot analysis (5 action types)
- WebSocket + REST hybrid connection to local backend
- Consent-based privacy model with audit logging

### Why Not Full Browser Automation?
1. **Security-first philosophy**: Autonomous clicking/form-filling requires stronger safety guarantees
2. **Meta-orchestrator role**: ZEO delegates browser automation to specialized tools (browser-use plugin, Playwright adapters)
3. **Tiered approval model**: 10-level permission hierarchy (navigate < click < type < submit < login < payment) already implemented in `browser_automation.py`

### Roadmap for Browser Enhancement
- **Phase 1** (current): Advisory overlay + tiered automation via plugins
- **Phase 2**: DOM element inspection + guided form filling (user confirms each field)
- **Phase 3**: Workflow recording + replay (Claude Cowork pattern)
- **Phase 4**: Native messaging for CLI ↔ browser coordination

---

## 5. GUI / CLI / Web Integration Strategy

| Interface | Role | Status |
|-----------|------|--------|
| **Desktop (Tauri v2)** | Primary GUI — task management, monitoring, approvals | 29 pages, full i18n |
| **CLI** | Developer-first — chat, dispatch, config, health | Slash commands, Ollama local mode |
| **Web UI (Vite)** | Same React app, runs in browser | Dev server on port 5173 |
| **Chrome Extension** | Browser-side advisory + screenshot analysis | Overlay chat widget |
| **API** | Headless automation, CI/CD integration | 395 endpoints, full REST |
| **Edge (Cloudflare)** | Serverless proxy, 24/365 availability | Hono-based workers |

All interfaces converge on the same FastAPI backend (port 18234), ensuring feature parity across GUI, CLI, and API consumers.

---

## 6. Summary: ZEO's Identity

> **ZEO is not a desktop agent. ZEO is not a cloud agent. ZEO is the orchestration layer that connects, governs, and audits all agents.**

Claude Cowork automates your desktop. Copilot Cowork automates your M365 suite. ZEO connects both — plus CrewAI, AutoGen, n8n, and 34+ apps — under unified approval gates, multi-model freedom, and full audit transparency.

The right answer is not "ZEO vs Cowork" — it's "ZEO + Cowork": ZEO can delegate tasks to Claude Cowork or Copilot Cowork as sub-workers while maintaining approval oversight and audit trails.
