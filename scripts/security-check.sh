#!/bin/bash
# scripts/security-check.sh
# 公開前セキュリティチェックスクリプト
# 使い方: ./scripts/security-check.sh

PASS=0
WARN=0
FAIL=0

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pass() { echo "✅ $1"; PASS=$((PASS + 1)); }
warn() { echo "⚠️  $1"; WARN=$((WARN + 1)); }
fail() { echo "❌ $1"; FAIL=$((FAIL + 1)); }

echo "=========================================="
echo " Zero-Employee Orchestrator 公開前チェック"
echo "=========================================="
echo ""

# ──────────────────────────────────────────────
# 1. .env ファイルが .gitignore に含まれているか
# ──────────────────────────────────────────────
GITIGNORE="$REPO_ROOT/.gitignore"
if grep -qE '^\.env$|^\.env(\s|$)' "$GITIGNORE" 2>/dev/null; then
  pass ".env が .gitignore に登録されています"
else
  fail ".env が .gitignore に登録されていません（シークレットが漏洩するリスクがあります）"
fi

# ──────────────────────────────────────────────
# 2. SECRET_KEY がデフォルト値のままでないか
# ──────────────────────────────────────────────
DEFAULT_SECRET="change-this-to-a-random-secret-key"
# .env ファイルと .env.example を除くすべての設定ファイルで検索
# (config.py はバリデーション用比較値を含むため除外)
if grep -rq "SECRET_KEY=${DEFAULT_SECRET}" "$REPO_ROOT/apps/api/" 2>/dev/null; then
  fail "SECRET_KEY がデフォルト値のままです（apps/api/.env に設定されています）"
elif [ -f "$REPO_ROOT/apps/api/.env" ] && grep -q "^SECRET_KEY=${DEFAULT_SECRET}" "$REPO_ROOT/apps/api/.env" 2>/dev/null; then
  fail "apps/api/.env の SECRET_KEY がデフォルト値のままです"
else
  pass "SECRET_KEY のデフォルト値は設定ファイルに存在しません"
fi

# ──────────────────────────────────────────────
# 3. apps/edge/proxy/wrangler.toml の KV namespace id
# ──────────────────────────────────────────────
PROXY_WRANGLER="$REPO_ROOT/apps/edge/proxy/wrangler.toml"
if [ -f "$PROXY_WRANGLER" ]; then
  if grep -q 'id = "placeholder-id"' "$PROXY_WRANGLER"; then
    fail "apps/edge/proxy/wrangler.toml の KV namespace id が placeholder-id のままです"
  else
    pass "apps/edge/proxy/wrangler.toml の KV namespace id が設定されています"
  fi
else
  warn "apps/edge/proxy/wrangler.toml が見つかりません（Cloudflare Proxy を使わない場合は無視してください）"
fi

# ──────────────────────────────────────────────
# 4. apps/edge/full/wrangler.toml の D1 database_id
# ──────────────────────────────────────────────
FULL_WRANGLER="$REPO_ROOT/apps/edge/full/wrangler.toml"
if [ -f "$FULL_WRANGLER" ]; then
  if grep -q 'database_id = "placeholder-id"' "$FULL_WRANGLER"; then
    fail "apps/edge/full/wrangler.toml の D1 database_id が placeholder-id のままです"
  else
    pass "apps/edge/full/wrangler.toml の D1 database_id が設定されています"
  fi
else
  warn "apps/edge/full/wrangler.toml が見つかりません（Cloudflare Full を使わない場合は無視してください）"
fi

# ──────────────────────────────────────────────
# 5. Tauri 署名鍵（pubkey）が空でないか
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
    warn "Tauri の自動更新 pubkey が空です（デスクトップアプリを配布しない場合は無視してください）"
  else
    pass "Tauri の自動更新 pubkey が設定されています"
  fi
else
  warn "apps/desktop/src-tauri/tauri.conf.json が見つかりません（デスクトップアプリを使わない場合は無視してください）"
fi

# ──────────────────────────────────────────────
# 6. CORS_ORIGINS がデフォルト（localhost）のまま
# ──────────────────────────────────────────────
ENV_FILE="$REPO_ROOT/apps/api/.env"
if [ -f "$ENV_FILE" ]; then
  CORS_VALUE=$(grep '^CORS_ORIGINS=' "$ENV_FILE" | head -1 | cut -d= -f2-)
  if echo "$CORS_VALUE" | grep -qi "localhost"; then
    warn "CORS_ORIGINS が localhost のままです（本番公開前に実際のドメインに変更してください）"
  else
    pass "CORS_ORIGINS が localhost 以外に設定されています"
  fi
else
  warn "apps/api/.env が見つかりません（CORS_ORIGINS の確認をスキップします）"
fi

# ──────────────────────────────────────────────
# 7. 認証ミドルウェアが有効であること
# ──────────────────────────────────────────────
# get_current_user 認証依存関数がルートで使用されているか確認
AUTH_DEP_FILE="$REPO_ROOT/apps/api/app/api/routes/auth.py"
if [ -f "$AUTH_DEP_FILE" ]; then
  if grep -q "async def get_current_user" "$AUTH_DEP_FILE"; then
    pass "認証依存関数 get_current_user が定義されています"
  else
    fail "認証依存関数 get_current_user が auth.py に定義されていません"
  fi
else
  fail "apps/api/app/api/routes/auth.py が見つかりません"
fi

# 保護すべきルートファイルで get_current_user が使われているか確認
ROUTE_DIR="$REPO_ROOT/apps/api/app/api/routes"
AUTH_ROUTES=0
UNPROTECTED_ROUTES=0
UNPROTECTED_LIST=""
for route_file in "$ROUTE_DIR"/*.py; do
  basename=$(basename "$route_file")
  # 認証不要のファイルはスキップ
  case "$basename" in
    __init__.py|auth.py|models.py|health.py) continue ;;
  esac
  # ルート定義があるか確認
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
  pass "全ルートファイル ($AUTH_ROUTES 個) で認証が有効です"
elif [ "$UNPROTECTED_ROUTES" -gt 0 ]; then
  warn "認証なしのルートファイルがあります ($UNPROTECTED_ROUTES 個):$UNPROTECTED_LIST"
  warn "本番環境では get_current_user による認証を有効にしてください"
else
  warn "ルートファイルが見つかりません（認証チェックをスキップします）"
fi

# SecurityHeadersMiddleware が main.py で登録されているか確認
MAIN_PY="$REPO_ROOT/apps/api/app/main.py"
if [ -f "$MAIN_PY" ]; then
  if grep -q 'SecurityHeadersMiddleware' "$MAIN_PY"; then
    pass "SecurityHeadersMiddleware が main.py に登録されています"
  else
    fail "SecurityHeadersMiddleware が main.py に登録されていません（セキュリティヘッダーが無効です）"
  fi
fi

# ──────────────────────────────────────────────
# 8. git log でシークレットっぽい文字列の簡易チェック
# ──────────────────────────────────────────────
# パターン説明:
#   sk-...       : OpenAI API キー
#   AIza...      : Google API キー
#   AKIA...      : AWS アクセスキー ID
#   ghp_...      : GitHub Personal Access Token
#   xox[baprs]-. : Slack トークン
SECRET_PATTERNS='(sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z\-_]{35}|AKIA[0-9A-Z]{16}|ghp_[0-9a-zA-Z]{36}|xox[baprs]-[0-9a-zA-Z\-]{10,})'
if command -v git &>/dev/null && git -C "$REPO_ROOT" rev-parse --git-dir &>/dev/null; then
  MATCHES=$(git -C "$REPO_ROOT" log --all -p --no-merges 2>/dev/null | grep -oE "$SECRET_PATTERNS" | head -5)
  if [ -n "$MATCHES" ]; then
    fail "git log にシークレットっぽい文字列が検出されました（要確認）:"
    echo "   $MATCHES" | head -3
  else
    pass "git log にシークレットっぽい文字列は検出されませんでした"
  fi
else
  warn "git コマンドが利用できないか、git リポジトリではありません（git log チェックをスキップします）"
fi

# ──────────────────────────────────────────────
# サマリー
# ──────────────────────────────────────────────
echo ""
echo "=========================================="
echo " チェック結果サマリー"
echo "=========================================="
echo "  ✅ パス  : $PASS 件"
echo "  ⚠️  警告  : $WARN 件"
echo "  ❌ 失敗  : $FAIL 件"
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo "❌ の項目を修正してから公開してください。"
  exit 1
elif [ "$WARN" -gt 0 ]; then
  echo "⚠️  警告項目があります。内容を確認してください。"
  exit 0
else
  echo "🎉 すべてのチェックをパスしました！"
  exit 0
fi
