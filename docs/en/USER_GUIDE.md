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

### Avatar AI and Secretary AI

**Avatar AI** learns your judgment patterns and writing style, and acts as your "alter ego":
- Reflects your values in Judge Layer quality assessments
- Reviews tasks and judges priorities in your absence (final approval authority always remains with you)
- Drafts content in your writing style and tone

**Secretary AI** functions as a "hub" connecting you and the AI organization:
- Morning briefings (pending approvals, in-progress tasks, today's schedule)
- Prioritized suggestions for next actions
- Briefing delivery via Discord / Slack / LINE

### Operating from Chat Tools

After installing the Discord / Slack / LINE Bot Plugin, you can send instructions to the AI organization from your everyday messaging apps.

```
/zeo ticket Create a competitive analysis report    → Create ticket
/zeo status                                         → Check in-progress tasks
/zeo approve 12345                                  → Approve operation
/zeo briefing                                       → Today's briefing
/zeo ask What are the risks of this initiative?     → Ask the AI
```

Approval dialogs are also displayed within chat tools when dangerous operations require authorization.

---

## 8. Tickets (Task Requests)

### Creating a Ticket

1. Enter the task description in natural language in the dashboard input box
2. Click the "Submit" button
3. AI starts requirements clarification (Design Interview), asking questions about unclear points
4. After answering the questions, a plan is automatically created and execution begins

### Rollback / Modify Midway

From the ticket detail screen:
- **Rollback**: Return to a previous step and request modifications
- **Add comment**: Input additional instructions or information
- **Cancel**: Abort the ticket

### Reviewing Artifacts

When a ticket is completed, artifacts are saved in the "Artifacts" tab.
- Supports various formats: text, JSON, code, etc.
- Version controlled — you can revert to previous versions

---

## 9. Approval Flow

Zero-Employee Orchestrator is built on the design principle that **dangerous operations always require human approval**.

### Operations Requiring Approval

- Publishing/sending to external services (SNS, email, Slack, etc.)
- File deletion or overwriting
- Operations involving billing/payment
- Permission or access setting changes
- Deployment/release to production environments

### Approval Process

1. Dashboard "Pending Approvals" count increases with a notification
2. Open the "Approvals" screen and review the content
3. **Approve**: Allow the execution to proceed
4. **Reject**: Cancel the execution
5. **Request modification**: Add a comment and ask the AI to reconsider

> All approved operations are recorded in the audit log.

---

## 10. Cost Management

### Execution Mode Settings

You can control costs by setting `DEFAULT_EXECUTION_MODE` in `apps/api/.env`:

| Mode | Description | Recommended For |
|------|-------------|-----------------|
| `quality` | Highest quality models (Claude Opus 4.6, GPT-5.4, Gemini 2.5 Pro) | Important deliverables |
| `speed` | Fast models (Claude Haiku 4.5, GPT-5 Mini, Gemini 2.5 Flash) | Simple tasks |
| `cost` | Low-cost models (Haiku, Mini, Flash Lite, DeepSeek) | Bulk processing |
| `free` | Free models (Gemini free tier / Ollama local) | Testing / Development |
| `subscription` | Free (via g4f, no API key required) | Trial use |

### Budget Settings

Set monthly budget limits from the "Cost Management" section in Settings. Alerts are sent when spending approaches the limit.

---

## 11. Troubleshooting

### `./setup.sh` won't execute

```bash
chmod +x setup.sh start.sh
./setup.sh
```

### Port already in use

```bash
# Check which ports are in use
lsof -i :18234   # Backend
lsof -i :5173    # Frontend

# Stop the process and restart
kill <PID>
./start.sh
```

### AI doesn't respond / errors occur

1. Check that API keys are correctly set in the `.env` file
2. If using Ollama: verify `ollama serve` is running
3. **In subscription mode**: The external service may be temporarily unavailable (switching to Gemini free API or Ollama is recommended)
4. Check backend logs:
   ```bash
   cd apps/api
   source .venv/bin/activate
   uvicorn app.main:app --reload
   ```

### "g4f error" in subscription mode

Subscription mode depends on external web services and may be temporarily unavailable.

- Wait a moment and retry
- Switch to a different model (e.g., `g4f/Copilot` → `g4f/GeminiPro`)
- Switch to the more stable Gemini free API key

### Gemini API errors

- `RESOURCE_EXHAUSTED`: Free tier limit reached → wait 1 minute or upgrade to a paid plan
- `API_KEY_INVALID`: Key is incorrect → verify in Google AI Studio

### Ollama won't connect

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running
ollama serve
```

### Reset the database

```bash
# Delete the SQLite file and restart (tables are auto-created)
rm apps/api/zero_employee_orchestrator.db
./start.sh
```

### Python virtual environment errors

```bash
cd apps/api
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e "."
```

---

## 12. Frequently Asked Questions (FAQ)

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

**A:** Yes. Install the Bot Plugin for Discord / Slack / LINE to create tickets, check progress, approve operations, and chat with AI directly from your messaging app. Example command: `/zeo ticket Create a competitive analysis report`

---

### Q: Is AI safe from making mistakes?

**A:** The following mechanisms ensure safety:
- **Judge Layer**: AI output is verified in two stages
- **Approval flow**: Dangerous operations are always blocked and require human confirmation
- **Audit logs**: All operations are recorded and traceable

---

### Q: Can multiple people use it?

**A:** Yes. Users are managed per organization (Company) with role-based access control (RBAC).

| Role | Permissions |
|------|-------------|
| Owner | Full access |
| Admin | Organization settings, approvals, audit logs |
| User | Task requests, viewing |
| Auditor | Read-only |
| Developer | Skill/Plugin development |

---

### Q: Can I use it offline?

**A:** Yes. If you use Ollama for local LLM, it works without an internet connection (internet is only needed for the initial model download).

---

### Q: Can I access it from mobile?

**A:** Since it's web browser compatible, you can access it from a smartphone browser (responsive design). You can also operate via the Discord / Slack / LINE Bot Plugin from mobile chat apps.

---

## Related Documents

| File | Content |
|------|---------|
| `README.md` | Quick start & tech stack |
| `docs/SECURITY.md` | Security configuration & production deployment |
| `docs/dev/DESIGN.md` | Implementation design (DB, API, state transitions) |
| `docs/dev/BUILD_GUIDE.md` | Developer build guide |
