#!/bin/bash
# scripts/security-check.sh
# Pre-release security check script
# Usage: ./scripts/security-check.sh

PASS=0
WARN=0
FAIL=0

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pass() { echo "✅ $1"; PASS=$((PASS + 1)); }
warn() { echo "⚠️  $1"; WARN=$((WARN + 1)); }
fail() { echo "❌ $1"; FAIL=$((FAIL + 1)); }

echo "=========================================="
echo " Zero-Employee Orchestrator Pre-Release Check"
echo "=========================================="
echo ""

# ──────────────────────────────────────────────
# 1. Check that .env is in .gitignore
# ──────────────────────────────────────────────
GITIGNORE="$REPO_ROOT/.gitignore"
if grep -qE '^\.env$|^\.env(\s|$)' "$GITIGNORE" 2>/dev/null; then
  pass ".env is listed in .gitignore"
else
  fail ".env is NOT in .gitignore (risk of leaking secrets)"
fi

# ──────────────────────────────────────────────
# 2. Check that SECRET_KEY is not the default value
# ──────────────────────────────────────────────
DEFAULT_SECRET="change-this-to-a-random-secret-key"
# Search all config files except .env.example
# (config.py is excluded because it contains the default for validation)
if grep -rq "SECRET_KEY=${DEFAULT_SECRET}" "$REPO_ROOT/apps/api/" 2>/dev/null; then
  fail "SECRET_KEY is still the default value (set in apps/api/.env)"
elif [ -f "$REPO_ROOT/apps/api/.env" ] && grep -q "^SECRET_KEY=${DEFAULT_SECRET}" "$REPO_ROOT/apps/api/.env" 2>/dev/null; then
  fail "SECRET_KEY in apps/api/.env is still the default value"
else
  pass "SECRET_KEY default value is not present in config files"
fi

# ──────────────────────────────────────────────
# 3. Check KV namespace id in apps/edge/proxy/wrangler.toml
# ──────────────────────────────────────────────
PROXY_WRANGLER="$REPO_ROOT/apps/edge/proxy/wrangler.toml"
if [ -f "$PROXY_WRANGLER" ]; then
  if grep -q 'id = "placeholder-id"' "$PROXY_WRANGLER"; then
    fail "KV namespace id in apps/edge/proxy/wrangler.toml is still placeholder-id"
  else
    pass "KV namespace id in apps/edge/proxy/wrangler.toml is configured"
  fi
else
  warn "apps/edge/proxy/wrangler.toml not found (ignore if not using Cloudflare Proxy)"
fi

# ──────────────────────────────────────────────
# 4. Check D1 database_id in apps/edge/full/wrangler.toml
# ──────────────────────────────────────────────
FULL_WRANGLER="$REPO_ROOT/apps/edge/full/wrangler.toml"
if [ -f "$FULL_WRANGLER" ]; then
  if grep -q 'database_id = "placeholder-id"' "$FULL_WRANGLER"; then
    fail "D1 database_id in apps/edge/full/wrangler.toml is still placeholder-id"
  else
    pass "D1 database_id in apps/edge/full/wrangler.toml is configured"
  fi
else
  warn "apps/edge/full/wrangler.toml not found (ignore if not using Cloudflare Full)"
fi

# ──────────────────────────────────────────────
# 5. Check Tauri signing key (pubkey) is not empty
# ──────────────────────────────────────────────
TAURI_CONF="$REPO_ROOT/apps/desktop/src-tauri/tauri.conf.json"
if [ -f "$TAURI_CONF" ]; then
  if command -v jq &>/dev/null; then
    PUBKEY=$(jq -r '.plugins.updater.pubkey // ""' "$TAURI_CONF" 2>/dev/null)
  else
    PUBKEY=$(python3 - "$TAURI_CONF" <<'PYEOF' 2>/dev/null
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    print(d.get('plugins', {}).get('updater', {}).get('pubkey', ''))
except Exception:
    print('')
PYEOF
)
  fi
  if [ -z "$PUBKEY" ]; then
    warn "Tauri auto-update pubkey is empty (ignore if not distributing desktop app)"
  else
    pass "Tauri auto-update pubkey is configured"
  fi
else
  warn "apps/desktop/src-tauri/tauri.conf.json not found (ignore if not using desktop app)"
fi

# ──────────────────────────────────────────────
# 6. Check CORS_ORIGINS is not still localhost
# ──────────────────────────────────────────────
ENV_FILE="$REPO_ROOT/apps/api/.env"
if [ -f "$ENV_FILE" ]; then
  CORS_VALUE=$(grep '^CORS_ORIGINS=' "$ENV_FILE" | head -1 | cut -d= -f2-)
  if echo "$CORS_VALUE" | grep -qi "localhost"; then
    warn "CORS_ORIGINS is still set to localhost (change to your production domain before deploying)"
  else
    pass "CORS_ORIGINS is set to a non-localhost value"
  fi
else
  warn "apps/api/.env not found (skipping CORS_ORIGINS check)"
fi

# ──────────────────────────────────────────────
# 7. Check authentication middleware is enabled
# ──────────────────────────────────────────────
# Verify get_current_user auth dependency is defined
AUTH_DEP_FILE="$REPO_ROOT/apps/api/app/api/routes/auth.py"
if [ -f "$AUTH_DEP_FILE" ]; then
  if grep -q "async def get_current_user" "$AUTH_DEP_FILE"; then
    pass "Auth dependency get_current_user is defined"
  else
    fail "Auth dependency get_current_user is NOT defined in auth.py"
  fi
else
  fail "apps/api/app/api/routes/auth.py not found"
fi

# Check that route files use get_current_user
ROUTE_DIR="$REPO_ROOT/apps/api/app/api/routes"
AUTH_ROUTES=0
UNPROTECTED_ROUTES=0
UNPROTECTED_LIST=""

# Whitelist: files that don't need authentication (with reasons)
# __init__.py     — Router registration only (no endpoints)
# auth.py         — Auth endpoints themselves (login/register/anonymous-session)
# models.py       — Model catalog (public info, read-only)
# health.py       — Health check (for infra monitoring)
#
# MIXED files (some public, some authenticated — have get_current_user inside):
# ai_tools.py       — GET: public tool list / POST: auth required
# marketplace.py    — GET: public browse / POST: auth required
# media_generation.py — GET: public provider list / POST: auth required
# org_setup.py      — GET /interview/questions: public / POST: auth required
AUTH_WHITELIST="__init__.py auth.py models.py health.py"

for route_file in "$ROUTE_DIR"/*.py; do
  basename=$(basename "$route_file")
  # Skip whitelisted files
  skip=false
  for wl in $AUTH_WHITELIST; do
    if [ "$basename" = "$wl" ]; then
      skip=true
      break
    fi
  done
  if $skip; then continue; fi

  # Check if file has route definitions
  if grep -q '@router\.' "$route_file" 2>/dev/null; then
    if grep -q 'get_current_user\|get_optional_user' "$route_file" 2>/dev/null; then
      AUTH_ROUTES=$((AUTH_ROUTES + 1))
    else
      UNPROTECTED_ROUTES=$((UNPROTECTED_ROUTES + 1))
      UNPROTECTED_LIST="$UNPROTECTED_LIST $basename"
    fi
  fi
done

if [ "$UNPROTECTED_ROUTES" -eq 0 ] && [ "$AUTH_ROUTES" -gt 0 ]; then
  pass "All route files ($AUTH_ROUTES files) have authentication enabled"
elif [ "$UNPROTECTED_ROUTES" -gt 0 ]; then
  fail "Route files without authentication found ($UNPROTECTED_ROUTES files):$UNPROTECTED_LIST"
else
  warn "No route files found (skipping authentication check)"
fi

# Check SecurityHeadersMiddleware is registered in main.py
MAIN_PY="$REPO_ROOT/apps/api/app/main.py"
if [ -f "$MAIN_PY" ]; then
  if grep -q 'SecurityHeadersMiddleware' "$MAIN_PY"; then
    pass "SecurityHeadersMiddleware is registered in main.py"
  else
    fail "SecurityHeadersMiddleware is NOT registered in main.py (security headers disabled)"
  fi
fi

# ──────────────────────────────────────────────
# 8. Quick scan of git log for potential secrets
# ──────────────────────────────────────────────
# Patterns:
#   sk-...       : OpenAI API key
#   AIza...      : Google API key
#   AKIA...      : AWS access key ID
#   ghp_...      : GitHub Personal Access Token
#   xox[baprs]-. : Slack token
SECRET_PATTERNS='(sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z\-_]{35}|AKIA[0-9A-Z]{16}|ghp_[0-9a-zA-Z]{36}|xox[baprs]-[0-9a-zA-Z\-]{10,})'
if command -v git &>/dev/null && git -C "$REPO_ROOT" rev-parse --git-dir &>/dev/null; then
  MATCHES=$(git -C "$REPO_ROOT" log --all -p --no-merges 2>/dev/null | grep -oE "$SECRET_PATTERNS" | head -5)
  if [ -n "$MATCHES" ]; then
    fail "Potential secrets found in git log (please review):"
    echo "   $MATCHES" | head -3
  else
    pass "No potential secrets found in git log"
  fi
else
  warn "git not available or not a git repository (skipping git log check)"
fi

# ──────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────
echo ""
echo "=========================================="
echo " Check Results Summary"
echo "=========================================="
echo "  ✅ Passed  : $PASS"
echo "  ⚠️  Warnings: $WARN"
echo "  ❌ Failed  : $FAIL"
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo "Please fix the failed items before publishing."
  exit 1
elif [ "$WARN" -gt 0 ]; then
  echo "There are warnings. Please review them."
  exit 0
else
  echo "All checks passed!"
  exit 0
fi
