> [日本語](../USER_GUIDE.md) | English | [中文](../zh/USER_GUIDE.md)

# English User Guide

> **v0.1** | Last updated: 2026-03-10

## 1. What is this software?

**Zero-Employee Orchestrator** is an **AI Business Orchestration Platform** where you simply instruct tasks in natural language, and multiple AI agents form teams to automatically plan, execute, verify, and report.

### What it can do

- Enter "Research competitors' pricing and create a report" — the AI team automatically takes action
- **Dangerous operations** (posting, sending, billing) **always require human approval**
- Complete **audit logs** of what was done, by which model, and when
- Automatic re-planning and recovery (Self-Healing) on failure

### Difference from other AI agents

| | Other AI Agents (AutoGPT, CrewAI, etc.) | Zero-Employee Orchestrator |
|---|---|---|
| Task management | Tracked during execution only | Structured as Tickets / Spec / Plan |
| Quality verification | None or single model | Judge Layer (two-stage + Cross-Model) |
| Approval flow | None (fully autonomous) | Dangerous operations blocked, human approval required |
| Failure recovery | Stop or simple retry | Self-Healing DAG with automatic re-planning |
| Audit logs | None or limited | All operations recorded and traceable |
| Cost management | None | Real-time token & budget tracking |
| Experience learning | None | Experience Memory for success/failure patterns |
| Extensibility | Requires code changes | Flexible Skill / Plugin / Extension system |

---

## 2. Key Features

### Design Interview
After receiving a task request, the AI asks additional questions to clarify requirements.

### Spec / Plan / Tasks
Request content is structured as "Specification → Plan → Task breakdown" and saved. Modifications and rollbacks are possible at any stage.

### Self-Healing DAG
Task dependencies are managed as a directed acyclic graph (DAG). If some tasks fail, the system automatically re-plans to avoid blockers.

### Judge Layer (Quality Verification)
AI output is always verified in two stages:
1. **Rule-based check**: Fast check for prohibited operations, credential leaks, etc.
2. **Cross-Model Verification**: Compare outputs from multiple LLMs for reliability

### Skill / Plugin / Extension
- **Skill**: Single-purpose processing (e.g., web scraping, email sending)
- **Plugin**: External service integration (e.g., Slack, Google Drive) — installable from GitHub repos
- **Extension**: UI and behavior customization

---

## 3. System Requirements

| Item | Requirement |
|------|-------------|
| OS | Windows 10+, macOS 12+, Ubuntu 22.04+ |
| Python | 3.12 or higher |
| Node.js | 18 or higher |
| Memory | 4 GB+ (8 GB+ recommended for local LLM) |
| Storage | 500 MB+ (model files require additional space) |

---

## 4. LLM (AI) Connection Methods

| Method | Cost | API Key | Setup | Recommended For |
|--------|------|---------|-------|-----------------|
| **Google Gemini Free API** | **Free** (with limits) | Required (free) | Easy | Best starting point |
| **Ollama (Local)** | **Completely Free** | Not required | Model DL needed | Offline / Privacy |
| **Subscription Mode** | **Free** | **Not required** | **Almost zero** | Testing |
| OpenRouter | Pay-per-use | Required | Normal | Multi-model management |
| OpenAI / Anthropic / Google | Pay-per-use | Required | Normal | Production / High quality |

---

## 5. Installation

### Desktop App (GUI — Easy)

1. Download the latest version from the [Releases page](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases)
2. Run the installer
3. Launch the app and follow the setup wizard

### From Source (For Developers)

```bash
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
chmod +x setup.sh start.sh
./setup.sh
cp apps/api/.env.example apps/api/.env
# Edit .env to add LLM API keys
./start.sh
```

Open **http://localhost:5173** in your browser.

---

## 6. Screens and Basic Operations

### Dashboard
- **Task request box**: Enter tasks in natural language
- **Active tickets**: List of ongoing tasks
- **Pending approvals**: Actions requiring your confirmation
- **Agent status**: AI agent states
- **Cost summary**: Today / this week / this month API costs

### Approval Screen
When the AI requests an operation requiring approval:
- **Approve**: Allow execution
- **Reject**: Cancel execution
- **Request modification**: Send comments to the AI for reconsideration

---

## 7. Skills and Plugins

### Adding Skills
1. Open "Skills" → "Create Skill"
2. Describe the skill in natural language
3. AI automatically generates the skill code
4. Review and save

### Adding Plugins from GitHub
Plugins can be installed from GitHub repositories:

```
POST /api/v1/registry/plugins/search-external?query=keyword
POST /api/v1/registry/plugins/import?source_uri=https://github.com/user/plugin-repo
```

Users can share and publish plugins without requiring developer intervention.

### Built-in Plugins

| Plugin | Purpose |
|--------|---------|
| `ai-avatar` (Avatar AI) | Learns your judgment criteria and writing style for proxy reviews |
| `ai-secretary` (Secretary AI) | Morning briefings, action proposals, bridges you and AI org |
| `discord-bot` | Create tickets, check progress, approve from Discord |
| `slack-bot` | Create tickets, check progress, approve from Slack |
| `line-bot` | Create tickets, check progress, approve from LINE |

---

## 8. Frequently Asked Questions (FAQ)

### Q: Can I use it for free?

**A:** Yes. Three methods:
1. **Google Gemini Free API (recommended)**: Get a free API key from Google AI Studio (no credit card required)
2. **Ollama (Local LLM)**: Download models to your PC — completely free, offline, unlimited
3. **Subscription Mode**: No API key required (but less stable)

### Q: Where is data stored?

**A:** By default, data is stored locally in `apps/api/zero_employee_orchestrator.db` (SQLite). Nothing is sent to the cloud.

### Q: Can I create my own Avatar AI or Secretary AI?

**A:** Yes. They can be added as Plugins. Avatar AI learns your judgment criteria and writing style. Secretary AI generates morning briefings and connects you with the AI organization.

### Q: Can I operate from Discord / Slack?

**A:** Yes. Install the Bot Plugin for Discord / Slack / LINE to create tickets, check progress, approve operations, and chat with AI directly from your messaging app.

---

## Related Documents

| File | Content |
|------|---------|
| `README.md` | Quick start & tech stack |
| `docs/SECURITY.md` | Security configuration & production deployment |
| `docs/dev/DESIGN.md` | Implementation design (DB, API, state transitions) |
| `docs/dev/BUILD_GUIDE.md` | Developer build guide |
