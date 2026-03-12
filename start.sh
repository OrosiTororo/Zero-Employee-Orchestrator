#!/bin/bash
# =============================================================================
# Zero-Employee Orchestrator — 起動スクリプト
# バックエンド・フロントエンドを同時に起動します
# =============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ---------------------------------------------------------------------------
# セットアップ済みかチェック — 未完了なら自動セットアップ
# ---------------------------------------------------------------------------
NEED_SETUP=false

if [ ! -d "$ROOT_DIR/apps/api/.venv" ]; then
    NEED_SETUP=true
fi

if [ ! -d "$ROOT_DIR/apps/desktop/ui/node_modules" ]; then
    NEED_SETUP=true
fi

if [ "$NEED_SETUP" = true ]; then
    warn "セットアップが完了していません。自動セットアップを実行します..."
    echo ""

    # Python venv + 依存関係
    if [ ! -d "$ROOT_DIR/apps/api/.venv" ]; then
        info "Python 仮想環境を作成しています..."
        cd "$ROOT_DIR/apps/api"
        if command -v uv &> /dev/null; then
            uv venv .venv && uv pip install -e "."
        else
            python3 -m venv .venv && .venv/bin/pip install -e "."
        fi
        ok "Python 依存関係をインストールしました"
        cd "$ROOT_DIR"
    fi

    # .env ファイル自動生成
    if [ ! -f "$ROOT_DIR/apps/api/.env" ]; then
        info ".env ファイルを生成しています..."
        SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || echo "auto-$(date +%s)")
        cat > "$ROOT_DIR/apps/api/.env" <<ENVEOF
DATABASE_URL=sqlite+aiosqlite:///./zero_employee_orchestrator.db
SECRET_KEY=${SECRET}
DEBUG=true
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","tauri://localhost","https://tauri.localhost"]
DEFAULT_EXECUTION_MODE=subscription
USE_G4F=true
ENVEOF
        ok ".env ファイルを作成しました"
    fi

    # フロントエンド依存関係
    if [ ! -d "$ROOT_DIR/apps/desktop/ui/node_modules" ]; then
        info "フロントエンド依存関係をインストールしています..."
        cd "$ROOT_DIR/apps/desktop/ui"
        if command -v pnpm &> /dev/null; then
            pnpm install
        else
            npm install
        fi
        ok "フロントエンド依存関係をインストールしました"
        cd "$ROOT_DIR"
    fi

    echo ""
    ok "自動セットアップが完了しました"
    echo ""
fi

# ---------------------------------------------------------------------------
# クリーンアップ用トラップ
# ---------------------------------------------------------------------------
PIDS=()

cleanup() {
    echo ""
    info "サーバーを停止しています..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    ok "すべてのサーバーを停止しました"
    exit 0
}

trap cleanup SIGINT SIGTERM

PURPLE='\033[38;5;99m'
INDIGO='\033[38;5;105m'
VIOLET='\033[38;5;141m'
LAVENDER='\033[38;5;183m'
DIM='\033[2m'
BOLD='\033[1m'

echo ""
echo -e "  ${PURPLE}    ███████╗███████╗ ██████╗ ${NC}"
echo -e "  ${PURPLE}    ╚══███╔╝██╔════╝██╔═══██╗${NC}"
echo -e "  ${INDIGO}      ███╔╝ █████╗  ██║   ██║${NC}"
echo -e "  ${INDIGO}     ███╔╝  ██╔══╝  ██║   ██║${NC}"
echo -e "  ${VIOLET}    ███████╗███████╗╚██████╔╝${NC}"
echo -e "  ${VIOLET}    ╚══════╝╚══════╝ ╚═════╝ ${NC}"
echo ""
echo -e "  ${BOLD}${LAVENDER}Zero-Employee Orchestrator${NC}"
echo -e "  ${DIM}AI Orchestration Platform${NC}"
echo ""

# ---------------------------------------------------------------------------
# バックエンド起動
# ---------------------------------------------------------------------------
info "バックエンド API サーバーを起動しています (port 18234)..."
cd "$ROOT_DIR/apps/api"
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 18234 &
PIDS+=($!)
cd "$ROOT_DIR"

# ---------------------------------------------------------------------------
# フロントエンド起動
# ---------------------------------------------------------------------------
info "フロントエンド開発サーバーを起動しています (port 5173)..."
cd "$ROOT_DIR/apps/desktop/ui"
pnpm dev &
PIDS+=($!)
cd "$ROOT_DIR"

echo ""
echo "=============================================="
echo -e "  ${GREEN}起動完了！${NC}"
echo "=============================================="
echo ""
echo "  バックエンド API:  http://localhost:18234"
echo "  API ドキュメント:  http://localhost:18234/api/v1/openapi.json"
echo "  フロントエンド:    http://localhost:5173"
echo ""
echo "  停止するには Ctrl+C を押してください"
echo ""

# ---------------------------------------------------------------------------
# プロセスを待機
# ---------------------------------------------------------------------------
wait
