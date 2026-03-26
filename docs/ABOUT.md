> English | [日本語](ja-JP/ABOUT.md) | [中文](zh/ABOUT.md)

# Zero-Employee Orchestrator — Why This System Is Needed

> From the era of "using" AI to the era of "having AI work for you."

---

## Are You Experiencing These AI Challenges?

"Every time I ask ChatGPT a question, I have to re-enter the same background information."

"I manually copy AI responses and paste them as input for the next step."

"I have to verify every AI answer myself to check if it's correct."

"I can't keep track of how far yesterday's AI task has progressed."

"When I ask AI to do something, I worry it might accidentally delete important data or send emails to the wrong people."

These are **structural limitations** of AI chat tools. Zero-Employee Orchestrator was built to fundamentally solve these problems.

---

## What Is Zero-Employee Orchestrator?

**From "a tool used by one person" to "infrastructure that makes AI function as an organization"**

Zero-Employee Orchestrator is an **AI business orchestration platform** where you simply give instructions in natural language, and multiple AI agents form a team to autonomously plan, execute, verify, and improve tasks.

It is not just an automation tool. It is an entirely new platform that **brings an entire AI organization into your business**.

---

## Comparison with Existing Systems

### Differences from Other AI Agents (AutoGPT, CrewAI, etc.)

| Aspect | Other AI Agents | Zero-Employee Orchestrator |
|--------|----------------|---------------------------|
| **Multi-AI Collaboration** | Limited (single-agent focused) | Role-assigned AI teams execute in parallel |
| **Memory** | Runtime only (lost on exit) | Persistent memory of experiences, patterns, and failures |
| **Task Management** | Tracked only during execution | Structured storage via Spec / Plan / Tasks |
| **Quality Assurance** | None or single model | Judge Layer with two-stage + Cross-Model Verification |
| **Dangerous Operation Guards** | None (fully automatic execution) | Mandatory blocking via approval flow |
| **Failure Recovery** | Stops or simple retry | Self-Healing DAG with automatic re-planning |
| **Audit Logs** | None or limited | Full tracking and recording of all operations |
| **Cost Management** | None | Real-time tracking of token consumption and budgets |
| **Extensibility** | Requires code changes | Flexible extension via Skill / Plugin / Extension |

### Differences from RPA / Traditional Business Automation Tools

| Aspect | Traditional RPA | Zero-Employee Orchestrator |
|--------|----------------|---------------------------|
| **Configuration Difficulty** | Manual flow/script design required | Just give instructions in natural language |
| **Adaptability to Change** | Manual flow modifications required | AI autonomously re-plans |
| **Non-routine Tasks** | Difficult to handle | Handled using natural language |
| **Judgment & Reasoning** | Rule-based | Advanced reasoning via LLM |
| **Approval Flow** | Manual setup required | Automatic detection and approval requests for dangerous operations |

### Differences from n8n / Make (Low-Code Automation)

| Aspect | n8n / Make | Zero-Employee Orchestrator |
|--------|-----------|---------------------------|
| **Task Definition** | Arrange nodes in GUI | A single natural language sentence |
| **Dynamic Re-planning** | Static flows | Automatic DAG reconstruction on failure |
| **Deep AI Integration** | Added as API blocks | AI is the orchestrator itself |
| **Quality Verification** | None | Cross-Model Verification |

---

## What Makes This System Outstanding

### 1. Your AI Organization Starts Working with "Just One Command"

```
"Create this month's SNS posting calendar and compile drafts for each post."
```

Just enter this, and:
1. AI deepens the requirements (Design Interview)
2. Tasks are automatically decomposed and scheduled in parallel (DAG)
3. Each AI agent executes their assigned tasks
4. The Judge Layer verifies quality and safety
5. Your approval is always requested before posting

The only manual work is "pressing the approve button."

---

### 2. Safety Is Built In at the Architecture Level

The biggest concern when delegating work to AI is the fear that "it might go out of control."

Zero-Employee Orchestrator solves this **at the architecture level**:

```
External transmission → Always requires approval dialog
File deletion        → Always requires approval dialog
Billing operations   → Always requires approval dialog
Permission changes   → Always requires approval dialog
```

Dangerous operations are physically blocked. AI cannot execute them directly.

Additionally, the **Judge Layer** verifies AI output in two stages:
- **Stage 1**: Rule-based fast checks (detection of prohibited operations and credential leaks)
- **Stage 2**: Cross-Model Verification by a different model (mutual confirmation of answer quality)

---

### 3. AI "Learns from Experience"

Traditional AI chats forget everything when the conversation ends.

Zero-Employee Orchestrator uses **Experience Memory** to:
- Memorize and reuse past success patterns
- Classify failure causes (Failure Taxonomy) and prevent recurrence
- Become smarter with every task execution

The more you repeat similar types of work, the more accurate and faster the AI team becomes.

---

### 4. Self-Healing — It Doesn't Stop When It Fails

Complex tasks can fail midway.

With traditional automation tools, the result is "an error occurred, so it stopped."

Zero-Employee Orchestrator's **Self-Healing DAG**:
1. Detects the failure
2. Analyzes the cause
3. Automatically generates alternative approaches (Re-Propose Layer)
4. Reconstructs the DAG and continues execution

It autonomously avoids many obstacles without human intervention.

---

### 5. Complete Transparency and Auditability

"Not knowing what AI did" is a major barrier to enterprise AI adoption.

Zero-Employee Orchestrator records all important operations in audit logs:
- **Who** requested what
- **Which AI model** executed it
- **How much** it cost
- **What** was output
- **Who** approved it

Fully compatible with compliance, internal auditing, and cost management.

---

### 6. Start for Free Right Now

One of the barriers to adopting AI tools is "obtaining API keys and setting up billing."

Zero-Employee Orchestrator provides **3 free usage methods**:

1. **Google Gemini Free API (Recommended)**: Get an API key without a credit card, stable operation
2. **Ollama (Local LLM)**: Download models to your PC for completely free, offline, unlimited use
3. **Subscription Mode**: Use immediately without an API key (for trial purposes, less stable)

The most balanced way to get started:
```env
GEMINI_API_KEY=<key obtained from Google AI Studio>
DEFAULT_EXECUTION_MODE=free
```

For production use, setting up API keys for OpenRouter / OpenAI / Anthropic enables access to high-quality models such as Claude Opus 4.6, GPT-5.4, and Gemini 2.5 Pro. Supported models are dynamically managed in `model_catalog.json`, allowing you to add or switch models without code changes.

---

### 7. AI Avatar and AI Secretary — Your "Stand-Ins" at Work

**AI Avatar Plugin** learns your decision-making criteria and writing style to act "on your behalf":
- Reflects your values in Judge Layer quality assessments
- Creates drafts in your tone
- Judges task priorities based on your criteria

**AI Secretary Plugin** serves as the "hub" connecting the AI organization to you:
- Daily morning briefing (pending approvals, in-progress tasks, schedule)
- Prioritized suggestions for what to do next
- Notifications and operations via Discord / Slack / LINE

Both are installed as Plugins, so you don't need to install them if you don't need them.

---

### 8. Command Your AI Organization from Chat Tools

Install the Discord / Slack / LINE Bot Plugin, and you can operate directly from the chat apps you already use.

```
/zeo ticket Create a competitive analysis report
/zeo briefing
/zeo approve 12345
```

You can run your AI organization as an extension of your chat without even opening the web dashboard.

---

### 9. Three-Layer Extension System to Customize Your Business

Rather than building a general-purpose AI that can handle all tasks from scratch, it's far more efficient to **assemble specialized AI teams**.

```
Skill     — Single-purpose processing (e.g., web scraping, translation, analysis)
Plugin    — Business function packages (e.g., AI Avatar, AI Secretary, YouTube operations, Discord Bot)
Extension — Connection and UI extensions (e.g., Obsidian integration, MCP, notifications)
```

Just describe a skill in natural language, and the AI automatically generates the skill code. No specialized programming knowledge is required.

---

## Particularly Well-Suited Use Cases

### Information Gathering & Analysis
- Regular creation of competitive analysis reports
- News and trend monitoring with summaries
- Sentiment analysis and aggregation of customer reviews

### Content Creation
- SNS posting calendar creation and draft generation
- Blog article and newsletter draft creation
- Press release and proposal drafting

### Data Processing & Management
- Data collection and integration from multiple sources
- Automatic report and dashboard updates
- Automatic meeting minutes and summary creation

### Development & Technical Tasks
- Code review and test automation
- Document generation and updates
- Bug investigation and fix proposals

### Tasks Requiring Approval
- SNS posting (draft creation → human approval → posting)
- Email sending (draft creation → human approval → sending)
- Invoice processing (data extraction → human confirmation → processing)

---

## Expected Impact

```
Routine information gathering tasks
  Before: Staff spend 2-3 hours on manual collection
  ZEO:    15 minutes from request to completed report, 5 minutes for human review

SNS content creation (10 posts/week)
  Before: One marketer spends 8 hours/week
  ZEO:    AI team creates drafts → approval only takes 1 hour/week

Competitive monitoring (daily)
  Before: 1 hour of manual checking every morning
  ZEO:    Automatic report delivered at 8 AM, 10 minutes to review
```

---

## Enterprise Ready

### Security
- All API keys and secrets stored with encryption (SecretRef)
- Dangerous operations blocked by physical approval barriers
- Audit logs for all operations (non-deletable)

### Organization Management
- Role-based access control (Owner / Admin / User / Auditor / Developer)
- Simultaneous management of multiple teams and projects
- Budget caps and cost alert settings

### Availability
- Automatic recovery via Self-Healing DAG
- Liveness monitoring via Heartbeat
- PostgreSQL support (for production environments)

---

## Get Started Now

```bash
# Up and running in 1 minute
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
./setup.sh && ./start.sh
```

Just open `http://localhost:5173` in your browser and complete the setup wizard.

It works without an API key (Subscription Mode).

---

## Design Philosophy

Zero-Employee Orchestrator is designed based on the following belief:

> **"AI is not a tool, but a member of the organization."**

Not just one-off Q&A, but understanding business context, making plans, collaborating as a team, learning from failures, and building appropriate relationships with humans — this is what true AI utilization looks like.

To achieve this:
- **Never remove human final decision authority** — dangerous operations always require approval
- **Never create black boxes** — visualize and record all operations
- **Continuously improve** — experience memory, failure classification, quality enhancement
- **Keep it extensible** — clear boundaries between Skill / Plugin / Extension

---

## Learn More

| Document | Description |
|----------|-------------|
| [USER_GUIDE.md](../USER_GUIDE.md) | From setup to operation guide |
| [README.md](../README.md) | Quick start and tech stack |
| [DESIGN.md](../DESIGN.md) | Implementation design (DB, API, state transitions) |
| [Zero-Employee Orchestrator.md](../Zero-Employee%20Orchestrator.md) | Top-level specification document (philosophy and requirements) |
| [MD_FILES_INDEX.md](../MD_FILES_INDEX.md) | Index of all `.md` files in the repository |

---

*Zero-Employee Orchestrator — AI, working as an organization.*
