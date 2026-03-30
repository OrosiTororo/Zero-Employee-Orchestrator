# Zero-Employee Orchestrator -- Complete User Guide

> Last updated: 2026-03-30

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Core Concepts](#2-core-concepts)
3. [Daily Operations](#3-daily-operations)
4. [Settings and Configuration](#4-settings-and-configuration)
5. [Skills, Plugins, and Extensions](#5-skills-plugins-and-extensions)
6. [Security](#6-security)
7. [CLI Reference](#7-cli-reference)

---

## 1. Getting Started

### What is ZEO?

Zero-Employee Orchestrator (ZEO) is an open-source AI orchestration platform that lets you run AI as an organization, not just a chatbot. You describe business workflows in plain language, and ZEO decomposes them into tasks, delegates work across specialized AI agents, verifies quality through a Judge Layer, and delivers results -- all with human approval gates and full audit trails. ZEO itself is free; you only pay LLM providers directly if you choose to use paid models.

### Installation Methods

#### Desktop App (Recommended for Non-Technical Users)

Download the installer for your operating system from the [Releases](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases) page:

| OS | File |
|---|---|
| Windows | `-setup.exe` (x64) |
| macOS | `.dmg` (Intel + Apple Silicon) |
| Linux | `.AppImage`, `.deb`, or `.rpm` |

Run the installer and the setup wizard will guide you through language, LLM provider, and your first task.

#### CLI (For Developers)

```bash
pip install zero-employee-orchestrator
```

Or install from source:

```bash
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator && pip install .
```

**System requirements:** Python 3.12+, 4 GB RAM minimum. Ollama local models need 8 GB+ RAM.

#### Docker (For Self-Hosting / Production)

```bash
docker compose -f docker/docker-compose.yml up -d
```

This starts the API server (port 18234), frontend (port 5173), and a background worker. Requires a `SECRET_KEY` environment variable for production use.

### First Launch and Setup Wizard

When you first launch ZEO (desktop or web), a setup wizard walks you through three steps:

1. **Language** -- Choose from English, Japanese, Chinese, Korean, Portuguese, or Turkish. You can change this later in Settings.
2. **LLM Provider** -- Pick how the AI runs. No API key is required for subscription mode (g4f) or local mode (Ollama).
3. **First Task** -- Select a quick-start template or describe your own workflow to begin immediately.

### 5 Quick-Start Templates

The Dashboard offers five business templates to get productive in under 10 minutes:

| Template | What It Does |
|----------|-------------|
| **Content Ops** | Plan, draft, review, and publish content with AI agents handling each stage |
| **Sales Research** | Research prospects, compile briefings, and prepare outreach materials |
| **FAQ / Knowledge Base** | Extract common questions from documents and generate structured Q&A |
| **Meeting to Tasks** | Convert meeting notes or transcripts into assigned, trackable tasks |
| **Pre-publish Review** | Run quality, compliance, and fact-checking passes before publication |

Select a template from the Dashboard, provide your input, and ZEO handles the rest -- with approval gates at each critical step.

---

## 2. Core Concepts

### The 9-Layer Architecture

ZEO processes work through nine layers, each with a distinct responsibility:

| Layer | Name | What It Does |
|-------|------|-------------|
| 1 | **User Layer** | Accepts input via the desktop app, web UI, or CLI |
| 2 | **Design Interview** | Explores and refines your requirements through an interactive conversation |
| 3 | **Task Orchestrator** | Breaks work into a DAG (directed acyclic graph) of tasks with cost estimates and scheduling |
| 4 | **Skill Layer** | Assigns specialized Skills (spec-writer, reviewer, etc.) plus local context to each task |
| 5 | **Judge Layer** | Verifies output quality using rule-based checks and cross-model verification |
| 6 | **Re-Propose** | If a task fails or is rejected, automatically rebuilds the plan and retries |
| 7 | **State and Memory** | Stores execution history, failure patterns, and lessons learned for future improvement |
| 8 | **Provider Interface** | Routes requests to the right LLM through a unified gateway (LiteLLM) |
| 9 | **Skill Registry** | Manages publishing, searching, and importing of Skills, Plugins, and Extensions |

### How Tasks Flow

A typical workflow moves through these stages:

```
Natural Language Input
    -> Design Interview (clarify requirements)
    -> Spec (structured specification document)
    -> Plan (DAG of tasks with dependencies)
    -> Execute (AI agents work on each task)
    -> Judge (verify quality, check for errors)
    -> Deliver (final output to you)
```

If the Judge rejects a result, the Re-Propose layer kicks in -- it rebuilds the relevant part of the plan and re-executes without starting over from scratch. The system learns from each failure to improve future runs.

### Approval Gates

ZEO requires human approval before executing dangerous operations. There are 12 categories of gated actions:

| Category | Examples |
|----------|---------|
| Send | Emails, messages, API calls to external services |
| Delete | Files, records, resources |
| Billing | Purchases, subscriptions, cost-incurring actions |
| Permission | Access changes, role modifications |
| Publish | Making content public |
| Install | New software, packages, plugins |
| Execute | Shell commands, scripts |
| Deploy | Production deployments |
| Data Transfer | Uploads, downloads, exports |
| Security | Credential changes, policy modifications |
| External API | Calls to third-party services |
| System | Configuration changes, restarts |

When an approval is needed, ZEO pauses execution and presents the request with context: what will happen, the estimated cost, risk level, affected data, and whether the action is reversible.

### Judge Layer

The Judge Layer uses a tiered approach to balance verification thoroughness against cost:

| Tier | When Used | What It Does |
|------|-----------|-------------|
| **LIGHTWEIGHT** | Low-risk, routine tasks | Rule-based checks only (format, completeness, basic quality) |
| **STANDARD** | Normal tasks | Rules + policy compliance checks |
| **HEAVY** | High-risk or high-value tasks | Rules + policy + cross-model verification (a second LLM reviews the first LLM's work) |

The system automatically selects the appropriate tier based on task risk level. You do not need to configure this manually.

---

## 3. Daily Operations

### Dashboard Overview

The Dashboard is your command center. It includes:

- **Natural language input** -- Type what you want done in plain language
- **Quick actions** -- One-click access to common operations
- **Status grid** -- Overview of active tasks, pending approvals, and agent status
- **Chat history** -- Previous conversations and their outcomes
- **Quick-start templates** -- Five business workflow templates (see Getting Started)

Use the Command Palette (`Ctrl+K` or `Cmd+K`) to quickly search across all pages and actions.

### Creating Tickets

Tickets are the primary unit of work in ZEO. Create them in two ways:

**Via natural language (recommended):** Type a description of what you need in the Dashboard input or chat. For example: "Write a product comparison report for our Q2 planning meeting." ZEO will run a Design Interview to clarify requirements, then generate a spec, plan, and begin execution.

**Via the Tickets page:** Click "New Ticket" in the Activity Bar, fill in the title and description, and optionally set priority, assignee, and deadline.

### Brainstorm Sessions

The Brainstorm page lets you compare responses from multiple AI models side by side. Select models from the dropdown (or type a custom model name), enter your prompt, and see how each model responds. This is useful for evaluating different approaches before committing to a plan.

### Secretary Brain Dumps

The Secretary AI acts as a bridge between you and the AI organization. Use it for unstructured "brain dumps" -- type or speak your raw thoughts, ideas, and notes. The Secretary will:

- Organize your input into structured items
- Convert actionable items into tickets
- File reference information into the knowledge base
- Flag items that need clarification

Access the Secretary from the Activity Bar.

### Agent Monitoring

The Agent Monitor page shows you:

- **Active executions** -- What each AI agent is currently working on
- **Reasoning traces** -- Step-by-step visualization of AI decision-making
- **Approval queue** -- Pending approvals with risk levels (approve or reject each one)
- **Sessions** -- Active and historical agent sessions
- **Error monitor** -- Failed tasks and their error details

### Kill Switch (Emergency Stop)

If something goes wrong, the Kill Switch immediately halts all active AI executions. Access it from:

- The Agent Monitor page (Emergency Stop button)
- The API: `POST /api/v1/kill-switch/activate`

Once activated, no new executions can start until you explicitly resume operations. This is a safety mechanism -- use it if agents are behaving unexpectedly or consuming excessive resources.

---

## 4. Settings and Configuration

Access Settings from the Activity Bar (gear icon). The Settings page uses a sidebar table of contents with a search bar for quick navigation.

### Theme and Language

- **Themes:** Dark (default), Light, and High Contrast. Select in Settings. Custom themes can be added via extensions.
- **Language:** 6 built-in languages -- English, Japanese, Chinese, Korean, Portuguese, Turkish. Changing the language affects the UI, AI agent responses, and CLI output. Additional languages can be added via the language-pack extension.

To change language via CLI:

```bash
zero-employee config set LANGUAGE en
```

### LLM Provider Setup

ZEO supports 11+ LLM providers. No API key is required to get started.

**Option A: Subscription mode (no key needed)**
Uses free web AI services via g4f. Set the execution mode to `subscription` in Settings or CLI.

**Option B: Local models via Ollama (fully offline)**
Install Ollama, download a model, and set execution mode to `free`. No internet connection needed.

**Option C: API key (best quality, pay-per-use)**
Enter your API key for any supported provider: OpenAI, Anthropic, Google (Gemini), Mistral, Cohere, DeepSeek, OpenRouter, and others. Use the dropdown selector in Settings to pick your provider and paste your key.

OpenRouter deserves special mention: a single OpenRouter API key gives you access to multiple LLM providers through one account.

### Execution Modes

| Mode | Description | Cost |
|------|-------------|------|
| **Quality** | Best models (Claude Opus, GPT, Gemini Pro) | Highest |
| **Speed** | Fast models (Claude Haiku, GPT Mini, Gemini Flash) | Medium |
| **Cost** | Budget models (Haiku, Mini, Flash Lite, DeepSeek) | Low |
| **Free** | Local models via Ollama | None |
| **Subscription** | Web AI via g4f | None |

You can override the execution mode per task -- for example, use Quality mode for a critical spec review and Speed mode for routine summaries.

### Provider Connections

Connect ZEO to external services (12+ providers with category filter):

- **Communication:** Slack, Discord, LINE
- **Project Management:** Jira, Linear, Asana, Trello, ClickUp
- **Knowledge:** Notion, Obsidian, Logseq, Confluence
- **Cloud Storage:** Google Drive, OneDrive, Dropbox
- **Code:** GitHub, GitLab
- **Productivity:** Google Workspace, Microsoft 365

The Settings page includes a note explaining that ZEO acts as a judgment and audit layer -- it coordinates and verifies, rather than replacing these tools.

You can also register custom apps not in the built-in list.

### Agent Behavior (Autonomy Levels)

Control how independently AI agents operate:

| Level | Behavior |
|-------|----------|
| **Observe** | AI watches and suggests, but takes no action |
| **Assist** | AI drafts work for your review before execution |
| **Semi-Auto** (default) | AI executes routine tasks, asks approval for dangerous operations |
| **Autonomous** | AI executes most tasks independently (dangerous operations still gated) |

Additional settings:
- **Browser automation:** Enable Chrome control and Web AI sessions (approval-gated)
- **Workspace access:** Enable local file access and cloud storage connections (both opt-in, disabled by default)

---

## 5. Skills, Plugins, and Extensions

### What Each Type Does

| Type | Purpose | Examples |
|------|---------|---------|
| **Skill** | A single-purpose specialist that handles one task well | spec-writer, plan-writer, review-assistant, browser-assist |
| **Plugin** | A bundle of related Skills that work together | ai-secretary, ai-avatar, research, browser-use |
| **Extension** | System-level integration or infrastructure | MCP, OAuth, notifications, language-pack, Obsidian, Chrome extension |

ZEO ships with 8 built-in Skills, 10 Plugins, and 11 Extensions. Built-in system Skills (like spec-writer and review-assistant) are always active and cannot be disabled.

### Creating Custom Skills

You have two options for creating new Skills:

**Natural language generation:** Describe what you want the Skill to do in plain language. ZEO generates the Skill code automatically, runs safety checks (18 dangerous patterns are scanned), and registers it if safe.

Example: Tell ZEO "Create a skill that summarizes long documents into 3 key points" and it will generate, validate, and register the Skill.

**Manual creation:** Create a manifest file following the Skill format and register it via the API or UI.

### Installing from the Marketplace

The Marketplace page (accessible from the Activity Bar) provides a unified view of community-created Skills, Plugins, and Extensions. Browse, search, and install with one click. Each listing shows a description, author, ratings, and safety analysis.

You can also install via natural language: say "add browser-use" or "add image generation tool" in the chat, and the Plugin Loader handles installation automatically.

### Natural Language Skill Generation

The Skill generation endpoint accepts a plain-language description and produces a working Skill:

1. You describe the desired behavior
2. ZEO generates the Skill code
3. Safety analysis runs automatically (18 dangerous pattern categories)
4. If the Skill passes, it is registered and enabled
5. HIGH-risk Skills are blocked unless you explicitly force installation

---

## 6. Security

ZEO is built security-first with multiple defense layers. All security features are active by default.

### Prompt Injection Defense

ZEO detects and blocks attempts to manipulate AI agents through injected instructions. The system scans for 28+ patterns across 5 categories of prompt injection attacks. All external data passed to LLMs is wrapped with boundary markers to prevent injection.

### Approval Gates

As described in Core Concepts, 12 categories of dangerous operations require your explicit approval. The AI cannot bypass these gates regardless of autonomy level. Each approval request includes context about cost, risk, permissions, data flow, and reversibility.

### Role-Based Tool Permissions

ZEO enforces least-privilege access through 5 default role policies:

| Role | Access Level |
|------|-------------|
| **Secretary** | Communication tools, scheduling, note-taking |
| **Researcher** | Search, knowledge base, read-only data access |
| **Reviewer** | Quality checks, comparison, validation tools |
| **Executor** | Task execution tools, file operations (within sandbox) |
| **Admin** | Full tool access (human accounts only -- AI cannot hold this role) |

AI agents are assigned roles based on their task. They cannot access tools outside their role's permissions.

### File Sandbox

AI agents can only access folders you explicitly allow. Three levels are available:

| Level | Behavior |
|-------|----------|
| **STRICT** (default) | Only folders on the allow list are accessible |
| **MODERATE** | Allow list plus read access for common file types |
| **PERMISSIVE** | Everything except denied folders (not recommended) |

By default, AI operates in an isolated internal workspace with no access to your local files or cloud storage. You opt in to expanded access through Settings.

### PII Protection

ZEO automatically detects and masks 13 categories of personal information (names, emails, phone numbers, addresses, financial data, etc.) before passing user input to AI models. Password uploads are always blocked regardless of settings.

### Memory Trust Levels

Experience Memory entries (lessons learned from past executions) carry metadata:

- **Trust level:** Score from 0.0 to 1.0
- **Source type:** Where the memory came from
- **Verification status:** Whether it has been confirmed
- **Expiry date:** When the memory should be re-evaluated

Only memories with a trust level of 0.7 or higher that have not expired are used in future decision-making. This prevents unreliable or outdated information from influencing AI behavior.

### Kill Switch

The emergency stop mechanism (see Daily Operations) immediately halts all AI agent activity. It blocks all active executions and prevents new ones from starting until you resume. Available from the Agent Monitor UI and the REST API.

---

## 7. CLI Reference

### Core Commands

| Command | Description |
|---------|-------------|
| `zero-employee serve` | Start the API server (port 18234) |
| `zero-employee serve --reload` | Start with hot reload (development) |
| `zero-employee serve --port 8000` | Start on a custom port |
| `zero-employee chat` | Interactive chat mode (all providers) |
| `zero-employee chat --mode free` | Chat using Ollama / g4f only |
| `zero-employee chat --lang en` | Chat in a specific language |
| `zero-employee local` | Local chat via Ollama |
| `zero-employee local --model qwen3:8b` | Local chat with a specific model |
| `zero-employee config list` | Show all configuration values |
| `zero-employee config set KEY value` | Set a configuration value |
| `zero-employee config get KEY` | Get a configuration value |
| `zero-employee models` | List available LLM models |
| `zero-employee pull qwen3:8b` | Download an Ollama model |
| `zero-employee health` | Check server health status |
| `zero-employee security status` | Show security configuration status |
| `zero-employee db upgrade` | Run database migrations |
| `zero-employee update` | Update to the latest version |
| `zero-employee update --check` | Check for updates without installing |

### Chat Mode Slash Commands

When inside `zero-employee chat`, these slash commands provide file and shell operations similar to a code editor:

| Command | Description |
|---------|-------------|
| `/read <path>` | Read a file (respects sandbox permissions) |
| `/write <path>` | Write content to a file |
| `/edit <path>` | View a file for editing |
| `/run <command>` | Execute a shell command (30-second timeout) |
| `/ls [path]` | List directory contents |
| `/cd <path>` | Change working directory |
| `/pwd` | Show current working directory |
| `/find <pattern>` | Find files matching a glob pattern |
| `/grep <pattern> [path]` | Search file contents |
| `/lang <code>` | Switch language (en, ja, zh, ko, pt, tr) |

All file operations are checked against the sandbox. Shell commands block dangerous patterns and enforce a 30-second timeout. These commands give you the same operational capabilities as the desktop UI, directly from the terminal.

### Quick Start from CLI

```bash
# 1. Install and configure (no API key needed)
pip install zero-employee-orchestrator
zero-employee config set DEFAULT_EXECUTION_MODE subscription

# 2. Start the server and chat
zero-employee serve &
zero-employee chat
```

From the chat, type your request in natural language. ZEO will interview you for requirements, build a plan, and execute it with approval gates at each critical step.

---

*Zero-Employee Orchestrator -- Complete User Guide*
