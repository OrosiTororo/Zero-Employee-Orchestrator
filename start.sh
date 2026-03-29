#!/bin/bash
# =============================================================================
# Zero-Employee Orchestrator — Startup Script
# Starts the backend and frontend simultaneously
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
# Check if setup is complete — run automatic setup if not
# ---------------------------------------------------------------------------
NEED_SETUP=false

if [ ! -d "$ROOT_DIR/apps/api/.venv" ]; then
    NEED_SETUP=true
fi

if [ ! -d "$ROOT_DIR/apps/desktop/ui/node_modules" ]; then
    NEED_SETUP=true
fi

if [ "$NEED_SETUP" = true ]; then
    warn "Setup is not complete. Running automatic setup..."
    echo ""

    # Python venv + dependencies (Python 3.12+ required)
    if [ ! -d "$ROOT_DIR/apps/api/.venv" ]; then
        info "Creating Python virtual environment..."
        # Find Python 3.12+
        PYTHON_CMD=""
        for cmd in python3.13 python3.12 python3; do
            if command -v "$cmd" &> /dev/null; then
                ver=$("$cmd" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo "0")
                if [ "$ver" -ge 12 ]; then
                    PYTHON_CMD="$cmd"
                    break
                fi
            fi
        done
        if [ -z "$PYTHON_CMD" ]; then
            error "Python 3.12 or higher is required. Please install python3.12."
        fi
        cd "$ROOT_DIR/apps/api"
        if command -v uv &> /dev/null; then
            uv venv --python "$PYTHON_CMD" .venv && uv pip install -e "."
        else
            "$PYTHON_CMD" -m venv .venv && .venv/bin/pip install -e "."
        fi
        ok "Python dependencies installed ($PYTHON_CMD)"
        cd "$ROOT_DIR"
    fi

    # Auto-generate .env file
    if [ ! -f "$ROOT_DIR/apps/api/.env" ]; then
        info "Generating .env file..."
        SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || echo "auto-$(date +%s)")
        cat > "$ROOT_DIR/apps/api/.env" <<ENVEOF
DATABASE_URL=sqlite+aiosqlite:///./zero_employee_orchestrator.db
SECRET_KEY=${SECRET}
DEBUG=true
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","tauri://localhost","https://tauri.localhost"]
DEFAULT_EXECUTION_MODE=subscription
USE_G4F=true
ENVEOF
        ok ".env file created"
    fi

    # Frontend dependencies
    if [ ! -d "$ROOT_DIR/apps/desktop/ui/node_modules" ]; then
        info "Installing frontend dependencies..."
        cd "$ROOT_DIR/apps/desktop/ui"
        if command -v pnpm &> /dev/null; then
            pnpm install
        else
            npm install
        fi
        ok "Frontend dependencies installed"
        cd "$ROOT_DIR"
    fi

    echo ""
    ok "Automatic setup completed"
    echo ""
fi

# ---------------------------------------------------------------------------
# Cleanup trap
# ---------------------------------------------------------------------------
PIDS=()

cleanup() {
    echo ""
    info "Stopping servers..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    ok "All servers stopped"
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
# Start backend
# ---------------------------------------------------------------------------
info "Starting backend API server (port 18234)..."
cd "$ROOT_DIR/apps/api"
# Use the venv Python directly to ensure correct environment
.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 18234 &
PIDS+=($!)
cd "$ROOT_DIR"

# Wait for backend to be ready before starting frontend
info "Waiting for backend to be ready..."
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:18234/healthz > /dev/null 2>&1; then
        ok "Backend is ready"
        break
    fi
    if [ "$i" -eq 30 ]; then
        warn "Backend not yet ready after 30s, continuing anyway..."
    fi
    sleep 1
done

# ---------------------------------------------------------------------------
# Start frontend
# ---------------------------------------------------------------------------
info "Starting frontend dev server (port 5173)..."
cd "$ROOT_DIR/apps/desktop/ui"
if command -v pnpm &> /dev/null; then
    pnpm dev &
else
    npm run dev &
fi
PIDS+=($!)
cd "$ROOT_DIR"

echo ""
echo "=============================================="
echo -e "  ${GREEN}Startup complete!${NC}"
echo "=============================================="
echo ""
echo "  Backend API:       http://localhost:18234"
echo "  API Docs:          http://localhost:18234/api/v1/openapi.json"
echo "  Frontend:          http://localhost:5173"
echo ""
echo "  Press Ctrl+C to stop"
echo ""

# ---------------------------------------------------------------------------
# Wait for processes
# ---------------------------------------------------------------------------
wait
