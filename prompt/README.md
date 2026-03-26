**Language:** English | [日本語](docs/ja-JP/README.md) | [简体中文](docs/zh-CN/README.md) | [繁體中文](docs/zh-TW/README.md) | [한국어](docs/ko-KR/README.md) | [Português (Brasil)](docs/pt-BR/README.md) | [Türkçe](docs/tr/README.md)

# Zero-Employee Orchestrator

[![Stars](https://img.shields.io/github/stars/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/stargazers)
[![Forks](https://img.shields.io/github/forks/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/network/members)
[![Contributors](https://img.shields.io/github/contributors/OrosiTororo/Zero-Employee-Orchestrator?style=flat)](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/graphs/contributors)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/-FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/-React-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?logo=typescript&logoColor=white)
![Rust](https://img.shields.io/badge/-Rust-000000?logo=rust&logoColor=white)
![Docker](https://img.shields.io/badge/-Docker-2496ED?logo=docker&logoColor=white)

> **AI Orchestration Platform — Design · Execute · Verify · Improve**

---

<div align="center">

**🌐 Language / 言語 / 语言**

[**English**](README.md) | [日本語](docs/ja-JP/README.md) | [简体中文](docs/zh-CN/README.md) | [繁體中文](docs/zh-TW/README.md) | [한국어](docs/ko-KR/README.md) | [Português (Brasil)](docs/pt-BR/README.md) | [Türkçe](docs/tr/README.md)

</div>

---

**The platform for running AI as an organization — not just a chatbot.**

Define business workflows in natural language, orchestrate multiple AI agents with role-based delegation, and execute tasks with human approval gates and full auditability. Built with a 9-layer architecture featuring Self-Healing DAG, Judge Layer, and Experience Memory.

ZEO itself is free and open source. LLM API costs are paid directly by users to each provider.

---

## The Guides

This repo is the platform itself. The guides explain the architecture and philosophy.

<table>
<tr>
<td width="33%">
<a href="docs/guides/quickstart-guide.md">
<img src="assets/images/guides/quickstart-guide.png" alt="Quickstart Guide" />
</a>
</td>
<td width="33%">
<a href="docs/guides/architecture-guide.md">
<img src="assets/images/guides/architecture-guide.png" alt="Architecture Deep Dive" />
</a>
</td>
<td width="33%">
<a href="docs/guides/security-guide.md">
<img src="assets/images/guides/security-guide.png" alt="Security Guide" />
</a>
</td>
</tr>
<tr>
<td align="center"><b>Quickstart Guide</b><br/>Installation, first workflow, CLI basics. <b>Read this first.</b></td>
<td align="center"><b>Architecture Deep Dive</b><br/>9-layer architecture, DAG orchestration, Judge Layer, Experience Memory.</td>
<td align="center"><b>Security Guide</b><br/>Prompt injection defense, approval gates, IAM, sandbox, PII protection.</td>
</tr>
</table>

| Topic | What You'll Learn |
|-------|-------------------|
| 9-Layer Architecture | User → Design Interview → Task Orchestrator → Skill → Judge → Re-Propose → Memory → Provider → Registry |
| Self-Healing DAG | Automatic re-planning and re-proposal on task failure |
| Judge Layer | Two-stage + Cross-Model quality verification |
| Skill / Plugin / Extension | 3-tier extensibility with natural language skill generation |
| Human-in-the-Loop | 12 categories of dangerous operations require human approval |
| Security-First Design | Prompt injection defense (40+ patterns), PII masking, file sandbox |

---

## What's New

### v0.1.0 — Initial Release (Mar 2026)

- **9-layer architecture** — User Layer → Design Interview → Task Orchestrator → Skill Layer → Judge Layer → Re-Propose → State & Memory → Provider → Skill Registry
- **Self-Healing DAG** — Automatic re-planning on task failure with dynamic DAG reconstruction
- **Judge Layer** — Rule-based first-pass + Cross-Model high-accuracy verification
- **Experience Memory** — Learns from past executions to improve future performance
- **Skill / Plugin / Extension** — 3-tier extensibility: 8 built-in skills, 10 plugins, 5 extensions
- **Natural language skill generation** — Describe a skill in plain language and AI auto-generates it (with safety checks)
- **Browser Assist** — Chrome extension overlay chat with real-time screen sharing and error diagnosis
- **Media generation** — Image (DALL-E, SD), video (Runway ML, Pika), audio (TTS, ElevenLabs), music (Suno), 3D (dynamic provider registration)
- **AI tool integration** — 25+ external tools (GitHub, Slack, Jira, Figma, etc.) operable by AI
- **Security-first** — Prompt injection defense (5 categories, 40+ patterns), approval gates, IAM, PII protection, file sandbox
- **Multi-model support** — Dynamic model catalog via `model_catalog.json`, auto-fallback for deprecated models
- **i18n** — Japanese / English / Chinese — UI, AI responses, and CLI all switch seamlessly
- **Autonomous operation** — Docker / Cloudflare Workers for 24/365 background execution
- **Self-Improvement** — AI analyzes and improves its own skills (with approval)
- **A2A communication** — Peer-to-peer agent messaging, channels, and negotiation

---

## 🚀 Quick Start

Get up and running in under 2 minutes:

### Step 1: Install

```bash
# PyPI
pip install zero-employee-orchestrator

# or from source
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator && pip install .

# or Docker
docker compose up -d
```

### Step 2: Configure (No API Key Required)

```bash
# Option A: Subscription mode (no key needed)
zero-employee config set DEFAULT_EXECUTION_MODE subscription

# Option B: Ollama local LLM (fully offline)
zero-employee config set DEFAULT_EXECUTION_MODE free
zero-employee pull qwen3:8b

# Option C: Multi-LLM platform (one key, many models)
zero-employee config set OPENROUTER_API_KEY <your-key>

# Option D: Individual provider keys
zero-employee config set GEMINI_API_KEY <your-key>
```

> **ZEO itself is free.** LLM API costs are paid directly to each provider. See [USER_SETUP.md](USER_SETUP.md) for details.

### Step 3: Start

```bash
# Web UI
zero-employee serve
# → http://localhost:18234

# Local chat (Ollama)
zero-employee local --model qwen3:8b --lang en
```

✨ **That's it!** You now have a full AI orchestration platform with human approval gates and auditability.

---

## 📦 What's Inside

```
Zero-Employee-Orchestrator/
├── apps/
│   ├── api/                  # FastAPI backend
│   │   └── app/
│   │       ├── core/               # Config, DB, security, i18n
│   │       ├── api/routes/         # 39 REST API route modules
│   │       ├── api/ws/             # WebSocket
│   │       ├── models/             # SQLAlchemy ORM
│   │       ├── schemas/            # Pydantic DTO
│   │       ├── services/           # Business logic
│   │       ├── repositories/       # DB I/O abstraction
│   │       ├── orchestration/      # DAG, Judge, state machine
│   │       ├── providers/          # LLM gateway, Ollama, RAG
│   │       ├── security/           # IAM, secrets, sanitize, prompt defense
│   │       ├── policies/           # Approval gates, autonomy boundaries
│   │       ├── integrations/       # Sentry, MCP, external skills, Browser Assist
│   │       └── tools/              # External tool connectors
│   ├── desktop/              # Tauri v2 + React UI
│   ├── edge/                 # Cloudflare Workers
│   └── worker/               # Background workers
├── skills/                   # 8 built-in skills
├── plugins/                  # 10 plugin manifests
├── extensions/               # 5 extension manifests
│   └── browser-assist/
│       └── chrome-extension/ # Chrome extension for Browser Assist
├── packages/                 # Shared NPM packages
├── docs/                     # Multi-language docs & guides
│   ├── ja-JP/                # 日本語
│   ├── zh-CN/                # 简体中文
│   ├── zh-TW/                # 繁體中文
│   ├── ko-KR/                # 한국어
│   ├── pt-BR/                # Português (Brasil)
│   ├── tr/                   # Türkçe
│   └── guides/               # Architecture, security, quickstart guides
└── assets/
    └── images/
        ├── guides/           # Guide header images
        └── logo/             # Logo assets
```

---

## 🏗️ 9-Layer Architecture

```
┌─────────────────────────────────────────┐
│  1. User Layer       — Natural language input          │
│  2. Design Interview — Requirements exploration        │
│  3. Task Orchestrator — DAG decomposition & scheduling  │
│  4. Skill Layer      — Specialized Skills + Context     │
│  5. Judge Layer      — Two-stage + Cross-Model QA       │
│  6. Re-Propose       — Rejection → dynamic DAG rebuild  │
│  7. State & Memory   — Experience Memory               │
│  8. Provider         — LLM Gateway (LiteLLM)           │
│  9. Skill Registry   — Publish / Search / Import        │
└─────────────────────────────────────────┘
```

---

## 🎯 Key Features

### Core Orchestration

| Feature | Description |
|---------|-------------|
| **Design Interview** | Natural language requirements exploration and refinement |
| **Spec / Plan / Tasks** | Structured intermediate artifacts — reusable, auditable, reversible |
| **Task Orchestrator** | DAG-based planning with cost estimation and quality mode switching |
| **Judge Layer** | Rule-based first pass + Cross-Model high-accuracy verification |
| **Self-Healing / Re-Propose** | Automatic re-planning on failure with dynamic DAG reconstruction |
| **Experience Memory** | Learns from past executions to improve future performance |

### Extensibility

| Feature | Description |
|---------|-------------|
| **Skill / Plugin / Extension** | 3-tier extensibility with full CRUD management |
| **Natural Language Skill Generation** | Describe in plain language → AI auto-generates (with safety checks) |
| **Skill Marketplace** | Community skill publishing, search, review, and installation |
| **External Skill Import** | Import skills from GitHub repositories |
| **Self-Improvement** | AI analyzes and improves its own skills (with approval) |
| **Meta-Skills** | AI learns how to learn (Feeling / Seeing / Dreaming / Making / Learning) |

### AI Capabilities

| Feature | Description |
|---------|-------------|
| **Browser Assist** | Chrome extension overlay — AI sees your screen in real-time |
| **Media Generation** | Image, video, audio, music, 3D — with dynamic provider registration |
| **AI Tool Integration** | 25+ external tools (GitHub, Slack, Jira, Figma, etc.) |
| **A2A Communication** | Peer-to-peer agent messaging, channels, and negotiation |
| **Avatar AI** | Learns your decision patterns and evolves with you |
| **Secretary AI** | Brain dump → structured tasks, bridges you and the AI org |
| **Repurpose Engine** | Auto-convert 1 content to 10 media formats |

### Security

| Feature | Description |
|---------|-------------|
| **Prompt Injection Defense** | 5 categories, 40+ detection patterns |
| **Approval Gates** | 12 categories of dangerous operations require human approval |
| **File Sandbox** | AI can only access user-permitted folders (default: STRICT) |
| **Data Protection** | Upload/download policy control (default: LOCKDOWN) |
| **PII Protection** | Auto-detect and mask 13 categories of personal information |
| **IAM** | Human/AI account separation, AI denied admin/secret access |
| **Red-team Security** | 8-category, 20+ test self-vulnerability assessment |

### Operations

| Feature | Description |
|---------|-------------|
| **Multi-model Support** | Dynamic catalog, auto-fallback, per-task provider override |
| **i18n** | Japanese / English / Chinese — UI, AI responses, CLI |
| **Autonomous Operation** | Docker / Cloudflare Workers — runs when your PC is off |
| **24/365 Scheduler** | 9 trigger types: cron, ticket creation, budget threshold, etc. |
| **iPaaS Integration** | n8n / Zapier / Make webhook integration |
| **Cloud Native** | AWS / GCP / Azure / Cloudflare abstraction layer |
| **Governance & Compliance** | GDPR / HIPAA / SOC2 / ISO27001 / CCPA / APPI |

---

## 🔒 Security

ZEO is designed **security-first** with multi-layered defense:

| Layer | Description |
|-------|-------------|
| **Prompt Injection Defense** | Detects and blocks instruction injection from external inputs (5 categories, 40+ patterns) |
| **Approval Gates** | 12 categories of dangerous operations (send, delete, billing, permission changes) require human approval |
| **Autonomy Boundaries** | Explicitly limits what AI can do autonomously |
| **IAM** | Separate human/AI accounts; AI denied secrets and admin permissions |
| **Secret Management** | Fernet encryption, auto-masking, rotation support |
| **Sanitization** | Auto-removal of API keys, tokens, and PII |
| **Security Headers** | CSP, HSTS, X-Frame-Options on all responses |
| **Rate Limiting** | slowapi-based API rate limiting |
| **Audit Logging** | All critical operations recorded (built-in from design, not bolted on) |

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

---

## 🖥️ CLI Reference

```bash
zero-employee serve              # Start API server
zero-employee serve --port 8000  # Custom port
zero-employee serve --reload     # Hot reload

zero-employee chat               # Chat mode (all providers)
zero-employee chat --mode free   # Free mode (Ollama / g4f)
zero-employee chat --lang en     # Language selection

zero-employee local              # Local chat (Ollama)
zero-employee local --model qwen3:8b --lang ja

zero-employee models             # List installed models
zero-employee pull qwen3:8b      # Download model

zero-employee config list        # Show all settings
zero-employee config set <KEY>   # Set a value
zero-employee config get <KEY>   # Get a value

zero-employee db upgrade         # Run DB migrations
zero-employee health             # Health check
zero-employee security status    # Security status
zero-employee update             # Update to latest version
```

---

## 🤖 Supported LLM Models

Managed via `model_catalog.json` — swap models without code changes.

| Mode | Description | Examples |
|------|-------------|---------|
| **Quality** | Highest quality | Claude Opus, GPT-5.4, Gemini 2.5 Pro |
| **Speed** | Fast response | Claude Haiku, GPT-5 Mini, Gemini 2.5 Flash |
| **Cost** | Low cost | Haiku, Mini, Flash Lite, DeepSeek |
| **Free** | Free | Gemini free tier, Ollama local |
| **Subscription** | No API key needed | via g4f |

Per-task provider override is supported — specify provider, model, and execution mode per task.

---

## 🧩 Skill / Plugin / Extension

### 3-Tier Extensibility

| Type | Description | Examples |
|------|-------------|---------|
| **Skill** | Single-purpose specialized processing | spec-writer, review-assistant, browser-assist |
| **Plugin** | Bundles multiple Skills | ai-secretary, ai-self-improvement, youtube |
| **Extension** | System integration & infrastructure | mcp, oauth, notifications, browser-assist |

### Generate Skills with Natural Language

```bash
POST /api/v1/registry/skills/generate
{
  "description": "A skill that summarizes long documents into 3 key points"
}
```

16 dangerous patterns are auto-detected. Only skills passing safety checks are registered.

---

## 🌐 Browser Assist

Chrome extension overlay chat — AI sees your screen in real-time and guides you.

- **Overlay Chat**: Chat UI directly on any website
- **Real-time Screen Sharing**: AI sees what you see (no manual screenshots)
- **Error Diagnosis**: AI reads error messages on screen and suggests fixes
- **Form Assistance**: Step-by-step field-by-field guidance
- **Privacy-first**: Screenshots processed temporarily, PII auto-masked, password fields blurred

### Setup

```
1. Load extensions/browser-assist/chrome-extension/ in Chrome
   → chrome://extensions → Developer mode → "Load unpacked"
2. Click the chat icon on any website
3. Ask questions or share your screen with the screenshot button
```

---

## 🛠️ Tech Stack

### Backend
- Python 3.12+ / FastAPI / uvicorn
- SQLAlchemy 2.x (async) + Alembic
- SQLite (dev) / PostgreSQL (production)
- LiteLLM Router SDK
- bcrypt / Fernet encryption
- slowapi rate limiting

### Frontend
- React 19 + TypeScript + Vite
- shadcn/ui + Tailwind CSS
- TanStack Query + Zustand

### Desktop
- Tauri v2 (Rust) + Python sidecar

### Deploy
- Docker + docker-compose
- Cloudflare Workers (serverless)

---

## ❓ FAQ

<details>
<summary><b>Do I need API keys to start?</b></summary>

No. You can use subscription mode (no key needed) or Ollama for fully offline local AI. See the Quick Start section above.
</details>

<details>
<summary><b>How much does it cost?</b></summary>

ZEO itself is free. LLM API costs are paid directly by you to each provider (OpenAI, Anthropic, Google, etc.). You can also run completely free with Ollama local models.
</details>

<details>
<summary><b>Can I use multiple LLM providers simultaneously?</b></summary>

Yes. ZEO supports per-task provider override — you can use Claude for high-quality spec reviews and GPT for fast task execution in the same workflow.
</details>

<details>
<summary><b>Is my data safe?</b></summary>

ZEO is self-hosted by design. Your data stays on your infrastructure. File sandbox defaults to STRICT, data transfer defaults to LOCKDOWN, and PII auto-detection is enabled by default.
</details>

<details>
<summary><b>How is this different from AutoGen / CrewAI / LangGraph?</b></summary>

ZEO is a **business workflow platform**, not a developer framework. It provides human approval gates, audit logging, a 3-tier extensibility system, browser assist, media generation, and a complete REST API — all designed for running AI as an organization, not just chaining prompts.
</details>

---

## 🧪 Development

```bash
# Setup
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
pip install -e ".[dev]"

# Start (hot reload)
zero-employee serve --reload

# Test
pytest apps/api/app/tests/

# Lint
ruff check apps/api/app/
ruff format apps/api/app/
```

---

## 🤝 Contributing

Contributions are welcome.

1. Fork → Branch → PR (standard flow)
2. Security issues: follow [SECURITY.md](SECURITY.md) for private reporting
3. Coding standards: ruff format, type hints required, async def

---

## 💜 Sponsors

This project is free and open source. Sponsors help keep it maintained and growing.

[**Become a Sponsor**](https://github.com/sponsors/OrosiTororo)

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=OrosiTororo/Zero-Employee-Orchestrator&type=Date)](https://star-history.com/#OrosiTororo/Zero-Employee-Orchestrator&Date)

---

## 📄 License

MIT — Use freely, modify as needed, contribute back if you can.

---

<p align="center">
  <strong>Zero-Employee Orchestrator</strong> — Run AI as an organization.<br>
  Built with security, auditability, and human oversight in mind.
</p>
