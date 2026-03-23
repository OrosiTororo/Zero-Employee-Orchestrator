# User Setup Guide

> [日本語](../../USER_SETUP.md) | English | [中文](../zh/USER_SETUP.md)

> ZEO is designed to work in a minimal initial state, allowing users to expand functionality as needed.
> All settings below are optional; configure them according to the features you want to use.
>
> For settings related to ZEO development and quality assurance (Sentry, security testing, etc.), see `DEVELOPER_SETUP.md`.
>
> Last updated: 2026-03-23

---

## 1. Connecting an LLM Provider

ZEO can be used without an API key. There are three ways to get started:

```bash
# Method 1: Subscription mode (no key required)
zero-employee config set DEFAULT_EXECUTION_MODE subscription

# Method 2: Ollama local LLM (fully offline, no key required)
zero-employee config set DEFAULT_EXECUTION_MODE free
zero-employee pull qwen3:8b

# Method 3: Multi-LLM platform (access multiple models with a single key)
zero-employee config set OPENROUTER_API_KEY <your-key>
```

> **ZEO itself does not charge any fees.** LLM API costs are paid directly by users to each provider.
> There is no dependency on any specific provider. When new platforms or services become available, they can be supported simply by adding configuration.

### External API Key Configuration (Optional)

If you want to use higher-quality models or specific providers, configure their API keys. All are optional.

#### LLM Providers

```bash
# OpenRouter (multi-LLM platform — access multiple models with a single key)
zero-employee config set OPENROUTER_API_KEY <your-key>

# OpenAI (GPT series)
zero-employee config set OPENAI_API_KEY <your-key>

# Anthropic (Claude series)
zero-employee config set ANTHROPIC_API_KEY <your-key>

# Google (Gemini series) — free tier available
zero-employee config set GEMINI_API_KEY <your-key>

# Mistral
zero-employee config set MISTRAL_API_KEY <your-key>

# Cohere
zero-employee config set COHERE_API_KEY <your-key>

# DeepSeek
zero-employee config set DEEPSEEK_API_KEY <your-key>
```

### Media Generation

```bash
# DALL-E (image generation) — uses the same OpenAI API key
# Stability AI (Stable Diffusion)
zero-employee config set STABILITY_API_KEY <your-key>

# Replicate (Flux, SVD, etc.)
zero-employee config set REPLICATE_API_TOKEN <your-key>

# ElevenLabs (voice generation)
zero-employee config set ELEVENLABS_API_KEY <your-key>

# Suno (music generation)
zero-employee config set SUNO_API_KEY <your-key>

# Runway ML (video generation)
zero-employee config set RUNWAY_API_KEY <your-key>
```

### External Tool Integration

```bash
# GitHub
zero-employee config set GITHUB_TOKEN <your-token>

# Slack
zero-employee config set SLACK_BOT_TOKEN <your-token>
zero-employee config set SLACK_SIGNING_SECRET <your-secret>

# Discord
zero-employee config set DISCORD_BOT_TOKEN <your-token>

# Notion
zero-employee config set NOTION_API_KEY <your-key>

# Jira
zero-employee config set JIRA_URL <your-url>
zero-employee config set JIRA_API_TOKEN <your-token>

# Figma (via MCP)
zero-employee config set FIGMA_ACCESS_TOKEN <your-token>

# LINE Bot
zero-employee config set LINE_CHANNEL_SECRET <your-secret>
zero-employee config set LINE_CHANNEL_ACCESS_TOKEN <your-token>
```

---

## 2. iPaaS Integration Webhook Configuration

Configure these settings when connecting ZEO to external iPaaS services.

### n8n

1. Start an n8n instance (self-hosted or n8n.cloud)
2. Create a Webhook node and copy the URL
3. Register it in ZEO:

```bash
# Via API
POST /api/v1/ipaas/workflows
{
  "name": "n8n-workflow-1",
  "provider": "n8n",
  "webhook_url": "https://your-n8n.example.com/webhook/xxx",
  "event_types": ["task_completed", "approval_required"]
}
```

### Zapier

1. Create a new Zap in Zapier
2. Select "Webhooks by Zapier -> Catch Hook" as the trigger
3. Register the issued Webhook URL in ZEO

### Make (Integromat)

1. Create a scenario in Make
2. Add a Webhook module and copy the URL
3. Register it in ZEO

---

## 3. Google Workspace Integration (OAuth2)

To integrate with Google Docs, Sheets, etc.:

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Go to "APIs & Services" -> "Credentials" -> Create an OAuth 2.0 Client ID
3. Add `http://localhost:18234/api/v1/auth/google/callback` as a redirect URI
4. Configure:

```bash
zero-employee config set GOOGLE_CLIENT_ID <client-id>
zero-employee config set GOOGLE_CLIENT_SECRET <client-secret>
```

---

## 4. Security Configuration (Required for Production)

When running ZEO in a production environment, be sure to configure the following.

### Generating a Secret Key

```bash
# Generate a SECRET_KEY (must be changed for production)
python -c "import secrets; print(secrets.token_urlsafe(32))"
zero-employee config set SECRET_KEY <generated-key>
```

### CORS Configuration

```bash
# Allow only production domains
zero-employee config set CORS_ORIGINS '["https://your-domain.com"]'

# Development environment (default)
zero-employee config set CORS_ORIGINS '["http://localhost:5173","http://localhost:18234"]'
```

### Authentication Middleware (Important)

ZEO implements JWT-based authentication, and protected endpoints require authentication via the `get_current_user` dependency function.

**Be sure to verify the following for production environments:**

1. **SECRET_KEY is set for production** -- With the default ephemeral key, all tokens are invalidated on server restart
2. **Authentication is enabled on all business API routes** -- Run `scripts/security-check.sh` to check for unauthenticated routes
3. **SecurityHeadersMiddleware is enabled** -- Ensures security headers such as CSP, HSTS, and X-Frame-Options are applied

```bash
# Pre-deployment security check
./scripts/security-check.sh

# Verify that red team tests detect no authentication bypasses
curl -X POST http://localhost:18234/api/v1/security/redteam/run \
  -H 'Content-Type: application/json' -d '{}'
```

> **Warning**: Endpoints exposed without authentication risk unauthorized data manipulation and data leakage. When adding new routes, always include `Depends(get_current_user)`.

---

## 5. Database Configuration

### Development / Personal Use (SQLite, No Configuration Required)

SQLite is used by default. No additional configuration is needed.

### Production / Team Use (PostgreSQL Recommended)

```bash
# PostgreSQL connection string
zero-employee config set DATABASE_URL "postgresql+asyncpg://user:password@localhost:5432/zeo"

# Run migrations
zero-employee db upgrade
```

---

## 6. Deployment Configuration

### Docker Compose (Recommended)

```bash
# Create an environment variable file
cp .env.example .env
# Edit the .env file to set API keys

# Start
docker compose up -d
```

### Cloudflare Workers

```bash
cd apps/edge/full
cp wrangler.toml.example wrangler.toml
# Edit wrangler.toml

npm install
npm run deploy
```

### Cloud Providers

Install the CLI for your cloud service of choice:

```bash
# AWS
pip install awscli
aws configure

# Google Cloud
# After installing the gcloud CLI:
gcloud auth application-default login

# Azure
# After installing the az CLI:
az login
```

---

## 7. Workspace Environment (Initial Configuration)

ZEO is designed with a **security-first** approach. In its initial state, AI agents operate in a **fully isolated workspace** with no access to local files or cloud storage.

### Initial State (Default)

```
Workspace:              Isolated environment (internal storage only)
Local file access:      Disabled
Cloud storage access:   Disabled
Knowledge sources:      Only files uploaded by the user
```

The knowledge and files used by AI agents are limited to what users upload to this isolated environment. Local folders and cloud data (Google Drive, etc.) are not accessible.

### How the Workspace Works

```
┌─────────────────────────────────────────┐
│  Isolated Workspace (Internal Storage)  │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌────────┐  │
│  │Knowledge │  │Artifacts│  │  Temp  │  │
│  │(Reference)│ │ (Output)│  │ Files  │  │
│  └─────────┘  └─────────┘  └────────┘  │
│                                         │
│  * Only files uploaded by the user      │
│  * AI can only read/write here          │
└─────────────────────────────────────────┘
          ^ Upload        v Export
      ────────────────────────────────
          ↕ Only when permitted by user
┌─────────────────┐  ┌─────────────────┐
│  Local Folders   │  │ Cloud Storage   │
│ (Default: Off)   │  │ (Default: Off)  │
└─────────────────┘  └─────────────────┘
```

---

## 8. Granting Access to Local Folders and Cloud Storage

Users can expand the access scope as needed.

### Configuring via GUI

Go to Settings > Security > Workspace Environment and configure the following:

- **Add local folders**: Select permitted folders using the file picker
- **Connect cloud storage**: Connect Google Drive / OneDrive / Dropbox, etc.
- **Specify save location**: Choose where to save artifacts from "Internal Storage", "Local", or "Cloud"

### Configuring via CLI / TUI

```bash
# Enable access to local folders
zero-employee config set WORKSPACE_LOCAL_ACCESS_ENABLED true
zero-employee config set SANDBOX_ALLOWED_PATHS "/home/user/documents,/home/user/projects"

# Enable access to cloud storage
zero-employee config set WORKSPACE_CLOUD_ACCESS_ENABLED true
zero-employee config set WORKSPACE_CLOUD_PROVIDERS '["google_drive"]'

# Set artifact save location
zero-employee config set WORKSPACE_STORAGE_LOCATION internal  # internal / local / cloud

# Change data transfer policy (when enabling local/cloud access)
zero-employee config set SECURITY_TRANSFER_POLICY restricted
```

### Via API

```bash
# Check workspace settings
GET /api/v1/security/workspace

# Update workspace settings
PUT /api/v1/security/workspace
{
  "local_access_enabled": true,
  "cloud_access_enabled": false,
  "allowed_local_paths": ["/home/user/documents"],
  "cloud_providers": [],
  "storage_location": "internal"
}

# Add an allowed path to the sandbox
POST /api/v1/security/sandbox/allowed-paths
{ "path": "/home/user/documents" }
```

---

## 9. Per-Task Environment and Permission Customization

Separately from system-wide settings, you can **specify the environment, permissions, and knowledge scope individually for each task (ticket)**.

### Instructing via Chat

You can instruct the AI via chat to set per-task environments:

```
"For this task, also reference the local /home/user/project-x folder"
"I'd like you to also use the materials in the shared Google Drive folder"
"Save the artifacts for this task to the local /home/user/output directory"
```

**Important**: If chat instructions differ from the system settings, the AI will ask the user for permission during the planning phase.

Example:
```
AI: "This task requires access to /home/user/project-x, but local access
     is currently disabled in the workspace settings.
     Would you like to allow the following access for this task only?
     - Read: /home/user/project-x
     - Write: /home/user/output
     [Allow] [Deny] [Change settings permanently]"
```

### Setting Per-Task Permissions via API

```bash
POST /api/v1/security/workspace/tasks/{task_id}/override
{
  "additional_local_paths": ["/home/user/project-x"],
  "additional_cloud_sources": ["google_drive://shared/project-x"],
  "storage_location": "local",
  "output_path": "/home/user/output"
}
```

---

## 10. File Sandbox

Additional settings to restrict which folders the AI can access.

### Levels

| Level | Description | Default |
|-------|-------------|---------|
| **STRICT** | Only folders on the allow list are accessible | **Default** |
| MODERATE | Allow list + read access for common file extensions | - |
| PERMISSIVE | Everything except the deny list (not recommended) | - |

```bash
# Set sandbox level
zero-employee config set SANDBOX_LEVEL strict

# Add allowed folders
zero-employee config set SANDBOX_ALLOWED_PATHS "/home/user/projects,/tmp/work"
```

---

## 11. Data Protection (Upload/Download Control)

| Policy | Description | Default |
|--------|-------------|---------|
| **LOCKDOWN** | Block all external transfers | **Default** |
| RESTRICTED | Only user-approved destinations | - |
| PERMISSIVE | Everything except the deny list (not recommended) | - |

```bash
# Set transfer policy
zero-employee config set SECURITY_TRANSFER_POLICY lockdown

# Enable uploads (approval still required)
zero-employee config set SECURITY_UPLOAD_ENABLED true
zero-employee config set SECURITY_UPLOAD_REQUIRE_APPROVAL true
```

---

## 12. Ollama Local LLM Setup

To run completely locally without an API key:

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Download recommended models
zero-employee pull qwen3:8b        # Lightweight (recommended)
zero-employee pull qwen3:32b       # High quality
zero-employee pull deepseek-coder-v2  # Coding-focused

# 3. Set execution mode to free
zero-employee config set DEFAULT_EXECUTION_MODE free
```

---

## 13. Installing the Chrome Extension

```
1. Open chrome://extensions in Chrome
2. Enable "Developer mode" in the top right
3. Click "Load unpacked"
4. Select the extensions/browser-assist/chrome-extension/ folder
5. Confirm that the ZEO server is running (http://localhost:18234)
```

---

## 14. Obsidian Integration

```bash
# Register vault path (via API)
POST /api/v1/knowledge/remember
{
  "category": "obsidian",
  "key": "vault_path",
  "value": "/path/to/your/obsidian/vault"
}
```

Installing the Obsidian plugin "Local REST API" is also recommended.

---

## 15. Heartbeat Scheduler Configuration

To set up scheduled recurring tasks:

```bash
# Register a schedule via API
POST /api/v1/companies/{company_id}/heartbeat-policies
{
  "name": "daily-report",
  "cron_expr": "0 9 * * *",
  "timezone": "Asia/Tokyo",
  "enabled": true
}

# List policies
GET /api/v1/companies/{company_id}/heartbeat-policies

# Execution history
GET /api/v1/companies/{company_id}/heartbeat-runs
```

---

## Verifying Your Configuration

Confirm that all settings are correct:

```bash
# Display all configuration values
zero-employee config list

# Health check
zero-employee health

# Security status
zero-employee security status
```

---

## Features That Work Without Configuration

The following features are available without any additional configuration:

- Design Interview (brainstorming and requirements exploration)
- Task Orchestrator (DAG decomposition and progress management)
- Judge Layer (quality verification)
- Self-Healing DAG (automatic replanning)
- Experience Memory
- Skill Registry (skill management)
- Approval flows and audit logs
- Automatic PII detection and masking
- Prompt injection defense
- File sandbox
- Meta-skills (AI learning capabilities)
- A2A bidirectional communication
- Marketplace foundation
- Team management foundation
- Governance and compliance foundation
- Repurpose engine
- User input requests
- Artifact export (local)
- E2E testing framework
- LLM response mocking (for testing)

---

## Security Default Settings Summary

```
Workspace:              Isolated environment (internal storage only)
Local access:           Disabled
Cloud access:           Disabled
Sandbox:                STRICT (allow list only)
Data transfer policy:   LOCKDOWN (external transfers blocked)
AI upload:              Disabled
AI download:            Disabled
External API calls:     Disabled
Automatic PII detection: Enabled (all categories)
PII upload blocking:    Enabled
Password transfer:      Always blocked
Upload approval:        Required
Download approval:      Required
```

---

*Zero-Employee Orchestrator -- User Setup Guide*
