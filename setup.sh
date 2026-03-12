#!/bin/bash
# =============================================================================
# Zero-Employee Orchestrator — セットアップスクリプト
# ダウンロード後に一度だけ実行してください
# =============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

echo ""
echo "=============================================="
echo "  Zero-Employee Orchestrator  セットアップ"
echo "=============================================="
echo ""

# ---------------------------------------------------------------------------
# 1. 前提条件の確認と自動インストール
# ---------------------------------------------------------------------------
info "前提条件を確認しています..."

# パッケージマネージャーの検出
detect_pkg_manager() {
    if command -v brew &> /dev/null; then
        echo "brew"
    elif command -v apt-get &> /dev/null; then
        echo "apt"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v pacman &> /dev/null; then
        echo "pacman"
    else
        echo ""
    fi
}

PKG_MANAGER=$(detect_pkg_manager)

install_with_pkg_manager() {
    local name="$1"
    shift
    case "$PKG_MANAGER" in
        brew)   info "$name をインストールしています (brew)..."; brew install "$@" ;;
        apt)    info "$name をインストールしています (apt)..."; sudo apt-get update -qq && sudo apt-get install -y "$@" ;;
        dnf)    info "$name をインストールしています (dnf)..."; sudo dnf install -y "$@" ;;
        pacman) info "$name をインストールしています (pacman)..."; sudo pacman -S --noconfirm "$@" ;;
        *)      return 1 ;;
    esac
}

FAILED=()

# --- Python 3.12+ ---
if command -v python3 &> /dev/null; then
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 12 ]; then
        ok "Python $PY_VER"
    else
        warn "Python $PY_VER が見つかりましたが 3.12 以上が推奨です"
    fi
else
    info "Python が見つかりません。インストールを試みます..."
    case "$PKG_MANAGER" in
        brew)   install_with_pkg_manager "Python" python@3.12 && ok "Python をインストールしました" ;;
        apt)    install_with_pkg_manager "Python" python3 python3-venv python3-pip && ok "Python をインストールしました" ;;
        dnf)    install_with_pkg_manager "Python" python3 python3-pip && ok "Python をインストールしました" ;;
        pacman) install_with_pkg_manager "Python" python python-pip && ok "Python をインストールしました" ;;
        *)      FAILED+=("python3 (3.12+) -- パッケージマネージャーが見つかりません") ;;
    esac
    if ! command -v python3 &> /dev/null; then
        FAILED+=("python3 (3.12+)")
    fi
fi

# --- Node.js 20+ ---
if command -v node &> /dev/null; then
    NODE_VER=$(node -v | sed 's/v//')
    NODE_MAJOR=$(echo "$NODE_VER" | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 20 ]; then
        ok "Node.js v$NODE_VER"
    else
        warn "Node.js v$NODE_VER が見つかりましたが v20 以上が推奨です"
    fi
else
    info "Node.js が見つかりません。インストールを試みます..."
    case "$PKG_MANAGER" in
        brew)   install_with_pkg_manager "Node.js" node && ok "Node.js をインストールしました" ;;
        apt)    install_with_pkg_manager "Node.js" nodejs npm && ok "Node.js をインストールしました" ;;
        dnf)    install_with_pkg_manager "Node.js" nodejs && ok "Node.js をインストールしました" ;;
        pacman) install_with_pkg_manager "Node.js" nodejs npm && ok "Node.js をインストールしました" ;;
        *)      FAILED+=("node (v20+) -- パッケージマネージャーが見つかりません") ;;
    esac
    if ! command -v node &> /dev/null; then
        FAILED+=("node (v20+)")
    fi
fi

# --- pnpm ---
if command -v pnpm &> /dev/null; then
    ok "pnpm $(pnpm -v)"
else
    info "pnpm が見つかりません。インストールを試みます..."
    if command -v npm &> /dev/null; then
        npm install -g pnpm && ok "pnpm をインストールしました (npm)"
    elif command -v corepack &> /dev/null; then
        corepack enable && corepack prepare pnpm@latest --activate && ok "pnpm をインストールしました (corepack)"
    elif [ "$PKG_MANAGER" = "brew" ]; then
        install_with_pkg_manager "pnpm" pnpm && ok "pnpm をインストールしました (brew)"
    else
        FAILED+=("pnpm (9+)")
    fi
fi

# --- pip / uv ---
HAS_UV=false
HAS_PIP=false
if command -v uv &> /dev/null; then
    ok "uv が見つかりました"
    HAS_UV=true
elif command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    ok "pip が見つかりました"
    HAS_PIP=true
else
    FAILED+=("pip または uv (Python パッケージマネージャー)")
fi

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    error "以下のツールを自動インストールできませんでした:\n  ${FAILED[*]}\n\n手動でインストールしてから再実行してください。"
fi

echo ""

# ---------------------------------------------------------------------------
# 2. 環境変数ファイルの作成
# ---------------------------------------------------------------------------
info "環境変数ファイルを設定しています..."

ENV_FILE="$ROOT_DIR/apps/api/.env"
if [ ! -f "$ENV_FILE" ]; then
    SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || echo "change-this-$(date +%s)")
    cat > "$ENV_FILE" <<EOF
# Zero-Employee Orchestrator 環境変数
# このファイルは setup.sh により自動生成されました

# データベース (SQLite — 開発用。本番では PostgreSQL 推奨)
DATABASE_URL=sqlite+aiosqlite:///./zero_employee_orchestrator.db

# セキュリティ
SECRET_KEY=${SECRET}

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","tauri://localhost","https://tauri.localhost"]

# デバッグモード
DEBUG=true

# LLM Provider (必要に応じて設定してください)
# OPENROUTER_API_KEY=
# OPENAI_API_KEY=

# Google OAuth (オプション)
# GOOGLE_CLIENT_ID=
# GOOGLE_CLIENT_SECRET=
EOF
    ok ".env ファイルを作成しました: $ENV_FILE"
else
    ok ".env ファイルは既に存在します（スキップ）"
fi

echo ""

# ---------------------------------------------------------------------------
# 3. Python バックエンドのセットアップ
# ---------------------------------------------------------------------------
info "Python バックエンドをセットアップしています..."

cd "$ROOT_DIR/apps/api"

# 仮想環境の作成
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    ok "仮想環境を作成しました"
else
    ok "仮想環境は既に存在します"
fi

# 仮想環境を有効化して依存関係をインストール
source .venv/bin/activate

if [ "$HAS_UV" = true ]; then
    uv pip install -e "."
else
    pip install -e "."
fi
ok "Python 依存関係をインストールしました"

# データベースの初期化 (テーブル作成)
info "データベースを初期化しています..."
python3 -c "
import asyncio
from app.core.database import engine, Base
import app.models  # noqa

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('  データベーステーブルを作成しました')

asyncio.run(init())
"
ok "データベースの初期化が完了しました"

deactivate
cd "$ROOT_DIR"

echo ""

# ---------------------------------------------------------------------------
# 4. フロントエンドのセットアップ
# ---------------------------------------------------------------------------
info "フロントエンドをセットアップしています..."

cd "$ROOT_DIR/apps/desktop/ui"
pnpm install
ok "フロントエンド依存関係をインストールしました"

cd "$ROOT_DIR"

echo ""

# ---------------------------------------------------------------------------
# 5. スクリプトに実行権限を付与
# ---------------------------------------------------------------------------
chmod +x "$ROOT_DIR/setup.sh" 2>/dev/null || true
chmod +x "$ROOT_DIR/start.sh" 2>/dev/null || true
chmod +x "$ROOT_DIR/scripts/dev/"*.sh 2>/dev/null || true

# ---------------------------------------------------------------------------
# 完了
# ---------------------------------------------------------------------------
echo ""
echo "=============================================="
echo -e "  ${GREEN}セットアップが完了しました！${NC}"
echo "=============================================="
echo ""
echo "  次のステップ:"
echo ""
echo "    1. LLM API キーを設定（任意）:"
echo "       $ENV_FILE を編集して OPENROUTER_API_KEY 等を設定"
echo ""
echo "    2. アプリケーションを起動:"
echo "       ./start.sh"
echo ""
echo "    3. ブラウザでアクセス:"
echo "       http://localhost:5173"
echo ""
echo "  詳細は README.md を参照してください。"
echo ""
