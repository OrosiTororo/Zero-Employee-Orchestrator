# Configuration Separation Guide: Developer vs User

> A guide that clearly separates ZEO configuration items into
> "what developers should configure" and "what end users should configure."
>
> Last updated: 2026-03-30

---

## ZEO Configuration Principles

ZEO's configuration system is built on the following design principles:

1. **No API key required to start** — Instantly usable via g4f (subscription) or Ollama (local)
2. **No specific provider recommended** — All options presented equally
3. **ZEO itself is free** — LLM API costs are paid directly by users to each provider
4. **Security-first** — Defaults are LOCKDOWN/STRICT; users explicitly expand access
5. **Full offline operation guaranteed** — All core features work with Ollama + SQLite
6. **Many features work with zero configuration** — Design Interview, Judge Layer, approval flows, etc.

### Responsibility Boundary

- **DEVELOPER_SETUP.md** scope: ZEO core development and quality management (Sentry, red-team testing)
- **USER_SETUP.md** scope: Everything else (security, DB, deployment, API keys, workspace, etc.)

---

## 1. Developer-Configured Items

> Items configured by those who develop, maintain, and release the ZEO codebase.
> End users do not need to touch these.

### 1.1 CI/CD — GitHub Repository Secrets

| Secret | Purpose | Workflow | Status |
|---|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | AI code review and task automation | `claude.yml`, `claude-code-review.yml` | Required |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Workers deployment | `deploy-workers.yml` | Edge deployment only |
| `CLOUDFLARE_API_TOKEN` | Cloudflare Workers authentication | `deploy-workers.yml` | Edge deployment only |
| `TAURI_SIGNING_PRIVATE_KEY` | Desktop app code signing | `release.yml` | Required for releases |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | Signing key password | `release.yml` | Required for releases |
| `SENTRY_DSN` | Error monitoring (dev team) | `ci.yml`, `deploy-api.yml` | Optional |
| `SECRET_KEY` | Encryption key for deployment | `deploy-api.yml` | Required for deployment |

### 1.2 Production Deployment Settings

| Setting | Default | Production Action |
|---|---|---|
| `SECRET_KEY` | Auto-generated (ephemeral) | Must change to a fixed, strong key |
| `DEBUG` | `true` | Must change to `false` |
| `CORS_ORIGINS` | localhost origins | Must change to production domain |
| `DATABASE_URL` | SQLite | PostgreSQL recommended |
| `JWT_SECRET` (Workers) | Not set | Set via `wrangler secret put` |

### 1.3 Quality Management

| Setting | Purpose | Scope |
|---|---|---|
| `SENTRY_DSN` | Bug tracking and error monitoring for ZEO itself | Dev team only |
| Red-team testing | ZEO vulnerability verification | Run before/after releases |
| `scripts/security-check.sh` | Security check | Run before deployment |

### 1.4 Release and Distribution

| Setting | Purpose | Notes |
|---|---|---|
| Tauri signing key | Desktop app code signing | minisign public key embedded in `tauri.conf.json` |
| PyPI publishing | `pip install zero-employee-orchestrator` | Automated via OIDC authentication |
| Cloudflare Workers | Edge deployment | Optional (D1/KV already configured) |

---

## 2. User-Configured Items

> Items that end users configure as needed.
> Configuration methods: UI (Settings page), CLI (`zero-employee config set`), REST API

### 2.1 Features That Work Without Configuration

The following work with zero configuration (see USER_SETUP.md Section 14):

- Design Interview (brainstorming and requirements exploration)
- Task Orchestrator (DAG decomposition, progress management)
- Judge Layer (quality verification)
- Self-Healing DAG (automatic replanning)
- Experience Memory / Failure Taxonomy
- Approval flows and audit logs
- Automatic PII detection and masking
- Prompt injection defense
- File sandbox

### 2.2 LLM Providers

| Setting | Default | Required |
|---|---|---|
| `DEFAULT_EXECUTION_MODE` | `quality` | Optional (changeable) |
| `USE_G4F` | `true` | Optional (no-key mode) |
| Provider API keys | Empty (not required) | Optional (for quality improvement) |
| `OLLAMA_BASE_URL` | `localhost:11434` | When using Ollama |
| `OLLAMA_DEFAULT_MODEL` | Auto-detected | Optional |

### 2.3 Language

| Setting | Default | Notes |
|---|---|---|
| `LANGUAGE` | `en` | UI + AI agent output language |

### 2.4 Security (User-Controlled)

| Setting | Default | Notes |
|---|---|---|
| Sandbox level | STRICT | User can relax |
| Data transfer policy | LOCKDOWN | User can relax |
| PII auto-detection | Enabled | Can be disabled |
| Workspace access | Internal storage only | Local/cloud can be enabled |

### 2.5 Agent Behavior

| Setting | Default | Notes |
|---|---|---|
| Autonomy level | semi_auto | observe/assist/semi_auto/autonomous |
| Budget limit | None | Configurable per day/week/month |
| Approval policy | Dangerous ops require approval | Customizable |

### 2.6 External Integrations (All Optional)

| Category | Examples | Notes |
|---|---|---|
| Communication | Slack, Discord, LINE | User configures connections |
| Project management | Jira, Linear, Asana | User configures connections |
| Knowledge | Notion, Obsidian | User configures connections |
| Media generation | Stability AI, ElevenLabs | User sets API keys |
| Cloud storage | Google Drive, OneDrive | OAuth authentication |

### 2.7 Theme and UI

| Setting | Default | Notes |
|---|---|---|
| Theme | Dark | Dark / Light / High Contrast |
| Company name / mission | Empty | Optional |

---

## 3. Repository Secrets Audit

Current secrets based on screenshot (verified 2026-03-30):

| Secret | Status | Verdict |
|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | Used by `claude.yml`, `claude-code-review.yml` | **Appropriate** |
| `CLOUDFLARE_ACCOUNT_ID` | Used by `deploy-workers.yml` | **Appropriate** |
| `CLOUDFLARE_API_TOKEN` | Used by `deploy-workers.yml` | **Appropriate** |
| `PYPI_API_TOKEN` | **Not used by any workflow** | **Deletion recommended** |
| `SENTRY_DSN` | Used by `ci.yml`, `deploy-api.yml` | **Appropriate** (dev team) |
| `TAURI_SIGNING_PRIVATE_KEY` | Used by `release.yml` | **Appropriate** |

---

## 4. Notes and Improvement Proposals

### 4.1 PYPI_API_TOKEN — Not Used by Workflows; Can Be Kept as Manual Backup

**Current state**: `PYPI_API_TOKEN` is registered in Repository Secrets, but `publish-pypi.yml`
uses OIDC (Trusted Publisher) authentication and does not reference this token.

```yaml
# publish-pypi.yml — Uses OIDC authentication
permissions:
  id-token: write  # ← OIDC token auto-generated
steps:
  - uses: pypa/gh-action-pypi-publish@release/v1  # ← No token needed
```

ZEO is published on PyPI (`pip install zero-employee-orchestrator`), and as long as
OIDC Trusted Publisher is functioning correctly, the token is unnecessary.

**Options**:
- **Delete**: Leaving unused secrets is a security risk (expanded attack surface)
- **Keep**: Retain as backup for manual uploads via `twine upload`

---

### 4.2 TAURI_SIGNING_PRIVATE_KEY_PASSWORD — Registered Without Password; No Action Needed

**Current state**: `release.yml` references `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`, but the
signing key was registered without a password.

```yaml
# release.yml line 76
TAURI_SIGNING_PRIVATE_KEY_PASSWORD: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY_PASSWORD }}
```

**Verdict**: The Tauri action does not error when the password is empty.
Since the signing key has no password, the current state is fine.

**Optional**: The line could be removed from `release.yml` to clarify intent, but keeping it
allows for future migration to a password-protected key.

---

### 4.3 SECURITY_SETUP_CHECKLIST.md Had Inconsistencies

**Previous state**: The checklist stated:

```markdown
- [ ] Replace KV namespace `placeholder-id` with your actual value
- [ ] Replace D1 `database_id` `placeholder-id` with your actual value
```

However, the actual `wrangler.toml` files already had real IDs:
- D1 database_id: `04e8c22d-10c5-442f-bc43-5b2f2ac0ae99` (configured)
- KV namespace_id: `21e5ccb52e034b4ead2781a3f0445783` (configured)

**Resolution**: Checklist items updated to reflect that real IDs are already configured. **Fixed.**

---

### 4.4 Google OAuth — User-Configured (Currently Unimplemented)

**Current state**: `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` are defined as user-configurable
in `config_manager.py` (CONFIGURABLE_KEYS). `USER_SETUP.md` instructs users to create their own
OAuth app in Google Cloud Console and configure via CLI:

```bash
zero-employee config set GOOGLE_CLIENT_ID <client-id>
zero-employee config set GOOGLE_CLIENT_SECRET <client-secret>
```

**However**: The Google OAuth endpoint in `auth.py` currently returns 501 (Not Implemented):

```python
@router.get("/google/authorize")
async def google_authorize():
    raise HTTPException(status_code=501, detail="Google OAuth is not yet available.")
```

**Verdict**: The design is user-configured, which aligns with ZEO's "no specific provider recommended"
principle. When OAuth implementation is complete, users will create their own Google Cloud project
and OAuth app following the `USER_SETUP.md` instructions.

---

### 4.5 Deployment Secrets — Add Based on Chosen Deployment Method

**Current state**: `deploy-api.yml` supports three deployment targets, each requiring different secrets:

| Deployment Method | Required Secrets | Notes |
|---|---|---|
| **Docker (Self-Hosted VPS)** | `SECRET_KEY`, `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY` | Most flexible |
| **Fly.io** | `SECRET_KEY`, `FLY_API_TOKEN` | Managed PaaS |
| **Railway** | `SECRET_KEY`, `RAILWAY_TOKEN` | Managed PaaS |
| **Common (optional)** | `DATABASE_URL`, `CORS_ORIGINS`, `SENTRY_DSN` | Environment-dependent |

**Local Docker Compose**: Only `SECRET_KEY` is needed to start (simplest):

```bash
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export SECRET_KEY
docker compose up -d  # → http://localhost:18234
```

**Verdict**: Secrets are added after choosing a deployment method. Currently unregistered is appropriate.

---

### 4.6 Sentry — User-Optional Is Most Cost-Efficient

**Current state**: Sentry is described differently across three locations:

| Document | Positioning |
|---|---|
| `DEVELOPER_SETUP.md` | Dev team only (not for user environments) |
| `FEATURE_BOUNDARY.md` | Should migrate to Extension (not core) |
| `config_manager.py` | User-configurable (included in CONFIGURABLE_KEYS) |

**Cost**: Sentry has a free tier, but production use can become paid ($26+/month).
When `SENTRY_DSN` is empty (default), the system falls back to a local event store
(5,000 event limit, in-memory) at **zero cost**.

**Alignment with ZEO principles**: `FEATURE_BOUNDARY.md` defines "anything that doesn't break
approval, auditing, or execution control → not core," and Sentry is classified as an Extension.
The current design where users optionally configure it is the most cost-efficient.

**Verdict**:
- Keep `SENTRY_DSN` in `config_manager.py` (configurable at runtime by both developers and users)
- Repository Secret `SENTRY_DSN` is appropriate for CI/CD dev quality management
- User environments should run without it (default), enabling only when needed

---

## 5. Configuration Priority Order

```
1. Environment variables              (highest priority)
   ↓
2. Runtime config file                (~/.zero-employee/config.json)
   ↓
3. .env file                          (project root)
   ↓
4. Settings class defaults            (config.py)
   ↓
5. Hardcoded fallbacks                (lowest priority)
```

---

## 6. Configuration Access Methods

| Method | Target | Notes |
|---|---|---|
| UI Settings page | Users | Desktop / Web |
| `zero-employee config set KEY VALUE` | Users / Developers | CLI |
| `PUT /api/v1/config` | Users / Developers | REST API |
| `.env` file | Developers | Environment variables |
| GitHub Repository Secrets | Developers | CI/CD |
| `wrangler secret put` | Developers | Cloudflare Workers |

---

## 7. Summary: Action Items

| # | Action | Priority | Status |
|---|---|---|---|
| 1 | `PYPI_API_TOKEN` — Not needed for OIDC. Decide: delete or keep as backup | Medium | Developer decision |
| 2 | `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` — No password; no action needed | — | **Resolved** |
| 3 | `SECURITY_SETUP_CHECKLIST.md` Cloudflare ID items updated | Medium | **Fixed** |
| 4 | Google OAuth — User-configured design aligns with policy; guide when implemented | Low | Awaiting implementation (501) |
| 5 | Sentry — User-optional (disabled by default) is most cost-efficient | — | **Currently appropriate** |
| 6 | Deployment secrets — Add after choosing deployment method | — | At deployment time |

---

*Zero-Employee Orchestrator -- Configuration Separation Guide*
