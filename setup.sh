#!/bin/bash
# =============================================================================
# Zero-Employee Orchestrator — Setup Script
# Run this once after downloading
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
echo "  Zero-Employee Orchestrator  Setup"
echo "=============================================="
echo ""

# ---------------------------------------------------------------------------
# 1. Check prerequisites and auto-install
# ---------------------------------------------------------------------------
info "Checking prerequisites..."

# Detect package manager
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
        brew)   info "Installing $name (brew)..."; brew install "$@" ;;
        apt)    info "Installing $name (apt)..."; sudo apt-get update -qq && sudo apt-get install -y "$@" ;;
        dnf)    info "Installing $name (dnf)..."; sudo dnf install -y "$@" ;;
        pacman) info "Installing $name (pacman)..."; sudo pacman -S --noconfirm "$@" ;;
        *)      return 1 ;;
    esac
}

FAILED=()

# --- Python 3.12+ ---
# Find Python >= 3.12 binary (tries python3.13, python3.12, python3 in order)
find_python312() {
    for cmd in python3.13 python3.12 python3; do
        if command -v "$cmd" &> /dev/null; then
            local ver
            ver=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
            local minor
            minor=$(echo "$ver" | cut -d. -f2)
            if [ "$minor" -ge 12 ]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

PYTHON_CMD=$(find_python312 || true)

if [ -n "$PYTHON_CMD" ]; then
    PY_VER=$("$PYTHON_CMD" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    ok "Python $PY_VER ($PYTHON_CMD)"
elif command -v python3 &> /dev/null; then
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    warn "Found Python $PY_VER but 3.12 or higher is required"
    info "Attempting to install Python 3.12..."
    case "$PKG_MANAGER" in
        brew)   install_with_pkg_manager "Python 3.12" python@3.12 ;;
        apt)    install_with_pkg_manager "Python 3.12" python3.12 python3.12-venv ;;
        dnf)    install_with_pkg_manager "Python 3.12" python3.12 ;;
        pacman) install_with_pkg_manager "Python 3.12" python ;;
        *)      ;;
    esac
    PYTHON_CMD=$(find_python312 || true)
    if [ -n "$PYTHON_CMD" ]; then
        ok "Installed Python 3.12+ ($PYTHON_CMD)"
    else
        FAILED+=("python3.12+ (currently $PY_VER -- 3.12 or higher required)")
    fi
else
    info "Python not found. Attempting to install..."
    case "$PKG_MANAGER" in
        brew)   install_with_pkg_manager "Python" python@3.12 ;;
        apt)    install_with_pkg_manager "Python" python3.12 python3.12-venv ;;
        dnf)    install_with_pkg_manager "Python" python3.12 ;;
        pacman) install_with_pkg_manager "Python" python python-pip ;;
        *)      ;;
    esac
    PYTHON_CMD=$(find_python312 || true)
    if [ -n "$PYTHON_CMD" ]; then
        ok "Installed Python ($PYTHON_CMD)"
    else
        FAILED+=("python3 (3.12+) -- no package manager found")
    fi
fi

# --- Node.js 20+ ---
if command -v node &> /dev/null; then
    NODE_VER=$(node -v | sed 's/v//')
    NODE_MAJOR=$(echo "$NODE_VER" | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 20 ]; then
        ok "Node.js v$NODE_VER"
    else
        warn "Found Node.js v$NODE_VER but v20 or higher is recommended"
    fi
else
    info "Node.js not found. Attempting to install..."
    case "$PKG_MANAGER" in
        brew)   install_with_pkg_manager "Node.js" node && ok "Installed Node.js" ;;
        apt)    install_with_pkg_manager "Node.js" nodejs npm && ok "Installed Node.js" ;;
        dnf)    install_with_pkg_manager "Node.js" nodejs && ok "Installed Node.js" ;;
        pacman) install_with_pkg_manager "Node.js" nodejs npm && ok "Installed Node.js" ;;
        *)      FAILED+=("node (v20+) -- no package manager found") ;;
    esac
    if ! command -v node &> /dev/null; then
        FAILED+=("node (v20+)")
    fi
fi

# --- pnpm ---
if command -v pnpm &> /dev/null; then
    ok "pnpm $(pnpm -v)"
else
    info "pnpm not found. Attempting to install..."
    if command -v npm &> /dev/null; then
        npm install -g pnpm && ok "Installed pnpm (npm)"
    elif command -v corepack &> /dev/null; then
        corepack enable && corepack prepare pnpm@latest --activate && ok "Installed pnpm (corepack)"
    elif [ "$PKG_MANAGER" = "brew" ]; then
        install_with_pkg_manager "pnpm" pnpm && ok "Installed pnpm (brew)"
    else
        FAILED+=("pnpm (9+)")
    fi
fi

# --- pip / uv ---
HAS_UV=false
HAS_PIP=false
if command -v uv &> /dev/null; then
    ok "uv found"
    HAS_UV=true
elif command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    ok "pip found"
    HAS_PIP=true
else
    FAILED+=("pip or uv (Python package manager)")
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

# 仮想環境の作成 (Python 3.12+ を使用)
PYTHON_CMD="${PYTHON_CMD:-python3}"
if [ ! -d ".venv" ]; then
    "$PYTHON_CMD" -m venv .venv
    ok "仮想環境を作成しました ($PYTHON_CMD)"
else
    # 既存 venv の Python バージョンを確認
    VENV_PY_VER=$(.venv/bin/python -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo "0")
    if [ "$VENV_PY_VER" -lt 12 ]; then
        warn "既存の仮想環境が Python 3.$VENV_PY_VER です。3.12+ で再作成します..."
        rm -rf .venv
        "$PYTHON_CMD" -m venv .venv
        ok "仮想環境を再作成しました ($PYTHON_CMD)"
    else
        ok "仮想環境は既に存在します (Python 3.$VENV_PY_VER)"
    fi
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
