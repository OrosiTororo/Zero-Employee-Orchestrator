# Developer Setup Checklist

> Items that require manual configuration by the repository owner.
> Code-level changes are handled automatically. This covers non-code settings only.
> Last verified: 2026-04-08

---

## 1. Quick Start (Minimum for Development)

```bash
# 1. Clone and install
git clone https://github.com/OrosiTororo/Zero-Employee-Orchestrator.git
cd Zero-Employee-Orchestrator
pip install -e ".[dev]"

# 2. Configure environment
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
# → Copy the output to SECRET_KEY= in .env

# 3. Choose ONE LLM provider (pick the easiest):
#   Option A: No API key (subscription mode via g4f)
#     → Set DEFAULT_EXECUTION_MODE=subscription in .env
#
#   Option B: Local Ollama (fully offline)
#     → curl -fsSL https://ollama.ai/install.sh | sh
#     → ollama pull llama3.2
#
#   Option C: Google Gemini free tier
#     → Visit https://aistudio.google.com/apikey
#     → Set GEMINI_API_KEY=your_key in .env
#
#   Option D: OpenRouter / OpenAI / Anthropic (paid)
#     → Set the respective API key in .env

# 4. Start the server
zero-employee serve --reload

# 5. Open http://localhost:18234 (API) or start the desktop app
```

---

## 2. GitHub Secrets

Go to **Settings → Secrets and variables → Actions** in your GitHub repository.

### Required for Desktop Releases (release.yml)

| Secret | How to Generate | Status |
|---|---|---|
| `TAURI_SIGNING_PRIVATE_KEY` | `npx tauri signer generate -w ~/.tauri/signing.key` → copy private key | **Set** (v0.1.0-v0.1.4 releases confirmed) |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | Password you set during key generation | **Set** |

### Required for Edge Deployment (deploy-workers.yml)

| Secret | How to Get | Status |
|---|---|---|
| `CLOUDFLARE_API_TOKEN` | Cloudflare Dashboard → API Tokens → Create Token → "Edit Cloudflare Workers" template | **Set** |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Dashboard → Overview → right sidebar "Account ID" | **Set** |

### Required for Claude Code Integration (claude.yml)

| Secret | How to Get | Status |
|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | Run `claude-code auth` and follow the OAuth flow | **Set** |

### Required for API Deployment (deploy-api.yml)

| Secret | How to Get | Status |
|---|---|---|
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` | Set per deployment |
| `DEPLOY_HOST` | Your VPS hostname (e.g., `my-server.example.com`) | If using VPS |
| `DEPLOY_USER` | SSH username (e.g., `deploy`) | If using VPS |
| `DEPLOY_SSH_KEY` | `ssh-keygen -t ed25519` → copy private key | If using VPS |
| `FLY_API_TOKEN` | `flyctl tokens create deploy` | If using Fly.io |

### PyPI Publishing (publish-pypi.yml)

| Setting | How | Status |
|---|---|---|
| OIDC Trusted Publisher | pypi.org → Your project → Settings → Publishing → Add GitHub as trusted publisher. Set owner=`OrosiTororo`, repo=`Zero-Employee-Orchestrator`, workflow=`publish-pypi.yml` | **Set** |

---

## 3. GitHub Repository Settings

Go to **Settings** in your GitHub repository.

| Setting | Location | How | Status |
|---|---|---|---|
| Branch protection | Settings → Branches → Add rule for `master` | Require PR review + status checks | **Set** |
| Secret scanning | Settings → Code security → Secret scanning → Enable | Auto-detects leaked API keys | **Set** |
| Dependabot | Already configured in `.github/dependabot.yml` | 7 ecosystems (pip, npm, cargo, actions) | **Active** |
| Environments | Settings → Environments → New: `production` | Add required reviewers for deploy | **Set** |

---

## 4. Chrome Extension (Browser Assist)

The Chrome extension is distributed via **GitHub Releases** (not Chrome Web Store).

### For Users:
1. Download `chrome-extension.zip` from the [Releases](https://github.com/OrosiTororo/Zero-Employee-Orchestrator/releases) page
2. Extract the zip
3. Open `chrome://extensions` in Chrome
4. Enable "Developer mode" (top right toggle)
5. Click "Load unpacked"
6. Select the extracted `chrome-extension/` folder

### For Development:
```bash
# Load directly from source
# chrome://extensions → Load unpacked → extensions/browser-assist/chrome-extension/
```

---

## 5. Production Deployment Checklist

```bash
# 1. Generate production SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. Configure .env for production
DEBUG=false
SECRET_KEY=<generated_key>
DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname
CORS_ORIGINS=https://your-domain.com

# 3. Run security check
chmod +x scripts/security-check.sh && ./scripts/security-check.sh

# 4. Deploy via Docker
docker compose up -d

# 5. Or deploy to Fly.io
flyctl launch && flyctl deploy

# 6. Verify
curl https://your-domain.com/api/v1/auth/anonymous-session
```

---

## 6. Release Workflow

To create a new release:

```bash
# Option A: Via tag push (automated)
./scripts/bump-version.sh 0.1.6
git add -A && git commit -m "release: v0.1.6"
git tag v0.1.6 && git push origin master --tags
# → release.yml automatically builds desktop + Chrome extension

# Option B: Via GitHub Actions UI
# Go to Actions → "Release - Build & Publish" → Run workflow → Enter version
```

Built artifacts uploaded to GitHub Releases:
- Windows: `-setup.exe`
- macOS: `.dmg` (Universal)
- Linux: `.AppImage`, `.deb`, `.rpm`
- Chrome: `chrome-extension.zip`
- Auto-updater: `latest.json`

---

## 7. Optional Integrations

| Integration | Env Variable | Free Tier? | Setup |
|---|---|---|---|
| Google Gemini | `GEMINI_API_KEY` | Yes | https://aistudio.google.com/apikey |
| Sentry | `SENTRY_DSN` | Yes (free plan) | https://sentry.io → Create project → Copy DSN |
| Google OAuth | `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` | Yes | Google Cloud Console → Credentials → OAuth 2.0 |
| n8n | `N8N_WEBHOOK_URL` | Yes (self-hosted) | n8n instance → Create workflow → Copy webhook URL |
| Vector DB | `VECTOR_STORE_PROVIDER` + `VECTOR_STORE_URL` + `VECTOR_STORE_API_KEY` | Varies | Supports: pinecone, qdrant, chroma |

---

## 8. v0.2 Planned (Non-Code Items)

| Item | When | Notes |
|---|---|---|
| Discord community server | v0.2 (after user growth) | Create server, set up channels, invite link in README |
| Native mobile app | v0.2+ (after PC UX validated) | React Native or Flutter, Dispatch integration |
| Vector DB production hosting | v0.2 | Qdrant Cloud free tier or self-hosted |
