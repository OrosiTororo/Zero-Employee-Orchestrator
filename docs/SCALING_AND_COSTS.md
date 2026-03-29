> English | [日本語](ja-JP/SCALING_AND_COSTS.md) | [中文](zh/SCALING_AND_COSTS.md)

# Zero-Employee Orchestrator — Cost, Constraints & Large-Scale Project Guide

> v0.1 | Last updated: 2026-03-12

---

## Table of Contents

1. [Features That Incur Costs](#1-features-that-incur-costs)
2. [Free Usage Scope](#2-free-usage-scope)
3. [Hardware & Environment Constraints](#3-hardware--environment-constraints)
4. [Features Not Implemented in v0.1](#4-features-not-implemented-in-v01)
5. [Large-Scale Project Use Cases](#5-large-scale-project-use-cases)
6. [Cost Optimization Tips](#6-cost-optimization-tips)

---

## 1. Features That Incur Costs

### LLM API Usage Fees

The primary cost of this system is LLM API usage fees.

| Provider | Approximate Cost (per 1,000 tokens) | Notes |
|---|---|---|
| Claude Opus | Input $0.015 / Output $0.075 | Highest quality, high cost |
| Claude Sonnet | Input $0.003 / Output $0.015 | Balance of quality and cost |
| Claude Haiku | Input $0.001 / Output $0.005 | Fast, low cost |
| GPT | Input $0.005 / Output $0.015 | OpenAI's high-performance model |
| GPT Mini | Input $0.00015 / Output $0.0006 | OpenAI's lightweight model |
| Gemini Pro | Input $0.002 / Output $0.018 | Google's high-performance model |
| Gemini Flash | Input $0.00025 / Output $0.0015 | Free tier available |
| DeepSeek Chat | Input $0.00014 / Output $0.00028 | Low cost |
| Ollama (Local) | **Free** | Electricity cost only |
| g4f (Free provider) | **Free** | Note stability and terms of service |

> Cost information is managed in `model_catalog.json` and can be updated via the API or by editing the file when providers change their pricing.

### Cloud Infrastructure

| Service | Purpose | Estimated Cost |
|---|---|---|
| Cloudflare Workers | Edge deployment (optional) | Free tier available (100K requests/day) |
| Cloudflare D1 | Edge DB (optional) | Free tier available (5GB) |
| PostgreSQL | Production database | $5–$50/month (varies by scale) |
| VPS / Cloud server | Backend runtime environment | $5–$100/month |

### External Service Integrations

| Service | Purpose | Notes |
|---|---|---|
| Google OAuth | User authentication (optional) | Free |
| Sentry | Error monitoring (optional) | Free tier available |
| GitHub Actions | CI/CD | Free tier available (2,000 min/month) |

---

## 2. Free Usage Scope

Fully free operation is possible using the following methods.

### Method 1: Ollama Local Mode

- **Cost**: Electricity only
- **Required hardware**: PC with 8GB+ RAM (16GB recommended)
- **Recommended models**: `qwen3:8b` (8GB RAM), `qwen3:32b` (32GB RAM)
- **Limitations**: Model performance may be inferior to cloud APIs

### Method 2: Gemini Free API Key

- **Cost**: Free (with rate limits)
- **How to get**: [Google AI Studio](https://aistudio.google.com/)
- **Limitations**: 15 requests/minute, 1,500 requests/day

### Method 3: Subscription Mode (g4f)

- **Cost**: Existing subscriptions such as ChatGPT Plus / Gemini Advanced
- **Limitations**: May have lower stability. Terms of service risks exist

### Features Included for Free

- Full 9-layer architecture
- Design Interview, Spec / Plan / Tasks
- Self-Healing DAG
- Judge Layer
- Approval flow
- Audit logs
- Experience Memory
- All 23 UI screens
- Skill / Plugin / Extension management
- SQLite database (for development and personal use)

---

## 3. Hardware & Environment Constraints

### When Using Local LLMs

| Model Size | Required RAM | Recommended GPU | Response Speed |
|---|---|---|---|
| 1B–3B | 4 GB | Not required | Fast |
| 7B–8B | 8 GB | Not required (faster with one) | Moderate |
| 13B–14B | 16 GB | VRAM 8GB+ recommended | Somewhat slow |
| 30B–34B | 32 GB | VRAM 16GB+ recommended | Slow |
| 70B+ | 64 GB+ | VRAM 24GB+ required | Slow |

### Database Constraints

| DB | Concurrent Connections | Data Size Limit | Recommended Use |
|---|---|---|---|
| SQLite | 1 (write) | Practically unlimited | Personal use, development |
| PostgreSQL | Hundreds | Practically unlimited | Team, production |

### Network

- When using cloud LLMs: Internet connection required
- Ollama local mode: Fully offline operation possible
- WebSocket: Browser connection required for real-time notifications

---

## 4. Features Not Implemented in v0.1

The following features have been designed but are not implemented or only partially implemented in v0.1.

### Planned for Future Versions

| Feature | Overview | Reason for Constraint |
|---|---|---|
| Multi-tenant production operation | Complete isolation of multiple organizations | Requires infrastructure setup and testing |
| GPU cluster support | Distributed LLM inference | Requires dedicated hardware |
| End-to-end encryption | Full encryption of communications and stored data | Requires key management infrastructure |
| Real-time voice input | Instructions via speech-to-text conversion | Requires speech recognition model integration |
| Mobile app | iOS / Android native apps | Requires development resources |
| SSO (SAML / OIDC) | Enterprise single sign-on | Requires IdP setup and testing |
| Bidirectional Webhook integration | Receiving events from external services | Requires security verification |
| Fine-tuning integration | Model fine-tuning with proprietary data | Requires GPU resources and data |

### Partially Implemented (with limitations)

| Feature | Current Status | Limitation |
|---|---|---|
| Judge Layer cross-model verification | Logic implemented | Requires multiple API keys configured |
| Cloudflare Workers deployment | wrangler.toml prepared | Requires Cloudflare account |
| Docker deployment | Dockerfile / compose prepared | Requires Docker environment |
| Tauri desktop build | Build configured | Requires Rust toolchain |

---

## 5. Large-Scale Project Use Cases

### Example 1: Corporate Marketing Department

**Scale**: Replacing the work of a 10-person marketing team with an AI team

**Task examples**:
- Automatic creation of weekly SNS posting calendars
- Periodic generation of competitive analysis reports
- Drafting press releases and multilingual translation
- Creating A/B test proposals for ad copy

**Estimated cost**: $50–$200/month (Sonnet + Flash combination)

**Required environment**:
- Cloud server (2 vCPU / 4 GB RAM)
- PostgreSQL database
- LLM API key (OpenRouter / OpenAI / Anthropic, etc. — any provider)

---

### Example 2: Software Development Team

**Scale**: Medium-scale development project (equivalent of 5–20 people)

**Task examples**:
- Automated code review (using Judge Layer)
- Automatic decomposition of bug reports into fix tasks
- Automatic test plan generation
- Automatic documentation updates
- Automated incident investigation (using AI Investigator)

**Estimated cost**: $100–$500/month (depends on quality mode)

**Required environment**:
- Cloud server (4 vCPU / 8 GB RAM)
- PostgreSQL + GitHub integration
- Sentry integration (optional)

---

### Example 3: Customer Support Department

**Scale**: Handling 1,000+ inquiries per month

**Task examples**:
- Automatic classification and routing of inquiries
- FAQ-based automatic responses (sent after approval)
- Escalation determination
- Automatic generation of response quality reports

**Estimated cost**: $30–$150/month (primarily Flash / Haiku)

**Required environment**:
- Cloud server (2 vCPU / 4 GB RAM)
- Email service integration (Plugin)
- CRM integration (Plugin)

---

### Example 4: Research & Analysis Team

**Scale**: Analysis of large volumes of documents

**Task examples**:
- Automatic summarization and classification of papers and patents
- Analysis of market research data and report generation
- Parallel hypothesis verification (using Hypothesis Engine)
- Automatic knowledge base construction

**Estimated cost**: $200–$1,000/month (high-quality mode primarily using Opus / GPT)

**Required environment**:
- Large-capacity storage
- Document search via local RAG
- PostgreSQL

---

### Example 5: Personal Use (Freelancer / Sole Proprietor)

**Scale**: Productivity enhancement for one person

**Task examples**:
- Invoice creation automation
- Drafting email responses
- Schedule management and reminders
- Blog post structure and drafts

**Estimated cost**: **Free** (Ollama local or Gemini free tier)

**Required environment**:
- PC (8 GB+ RAM)
- Ollama installed

---

## 6. Cost Optimization Tips

### Using Execution Modes Strategically

| Mode | Use Case | Cost Estimate |
|---|---|---|
| `quality` | Important decisions, before external submissions | High |
| `speed` | Internal processing, drafts | Medium |
| `cost` | Bulk processing, routine tasks | Low |
| `free` | Personal use, testing | Free |

### Recommended Strategies

1. **Use `cost` mode for daily tasks**: Haiku / Flash / Mini provides sufficient quality
2. **Use `quality` mode only for important deliverables**: Final review with Opus / GPT
3. **Use `speed` mode for Judge Layer**: Prioritize speed for verification
4. **Set budget policies**: Prevent unexpected costs with daily / monthly limits
5. **Combine local models with cloud**: Drafts locally, finishing touches in the cloud

### Budget Management Features

- Set daily / weekly / monthly budget limits
- Warning at 80% usage, automatic stop at 100%
- Transaction-level tracking with cost ledger
- Real-time cost visualization on dashboard
