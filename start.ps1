# =============================================================================
# Zero-Employee Orchestrator — Startup Script (Windows PowerShell)
# Starts the backend and frontend simultaneously
# =============================================================================

$ErrorActionPreference = "Stop"
$ROOT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

function Info($msg)  { Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Ok($msg)    { Write-Host "[OK]    $msg" -ForegroundColor Green }
function Warn($msg)  { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Err($msg)   { Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }

# ---------------------------------------------------------------------------
# Check if setup is complete — run automatic setup if not
# ---------------------------------------------------------------------------
$NeedSetup = $false

if (-not (Test-Path "$ROOT_DIR\apps\api\.venv")) { $NeedSetup = $true }
if (-not (Test-Path "$ROOT_DIR\apps\desktop\ui\node_modules")) { $NeedSetup = $true }

if ($NeedSetup) {
    Warn "Setup is not complete. Running automatic setup..."

    # Python venv + dependencies
    if (-not (Test-Path "$ROOT_DIR\apps\api\.venv")) {
        Info "Creating Python virtual environment..."
        $PythonCmd = $null
        foreach ($cmd in @("python3", "python")) {
            try {
                $ver = & $cmd -c "import sys; print(sys.version_info.minor)" 2>$null
                if ([int]$ver -ge 12) { $PythonCmd = $cmd; break }
            } catch { }
        }
        if (-not $PythonCmd) { Err "Python 3.12 or higher is required." }

        Push-Location "$ROOT_DIR\apps\api"
        try {
            if (Get-Command uv -ErrorAction SilentlyContinue) {
                & uv venv --python $PythonCmd .venv
                & uv pip install -e "."
            } else {
                & $PythonCmd -m venv .venv
                & .\.venv\Scripts\pip.exe install -e "."
            }
            Ok "Python dependencies installed ($PythonCmd)"
        } finally { Pop-Location }
    }

    # Auto-generate .env file
    if (-not (Test-Path "$ROOT_DIR\apps\api\.env")) {
        Info "Generating .env file..."
        $Secret = & python -c "import secrets; print(secrets.token_urlsafe(32))" 2>$null
        if (-not $Secret) { $Secret = "auto-$(Get-Date -UFormat %s)" }
        @"
DATABASE_URL=sqlite+aiosqlite:///./zero_employee_orchestrator.db
SECRET_KEY=$Secret
DEBUG=true
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","tauri://localhost","https://tauri.localhost"]
DEFAULT_EXECUTION_MODE=subscription
USE_G4F=true
"@ | Set-Content "$ROOT_DIR\apps\api\.env" -Encoding UTF8
        Ok ".env file created"
    }

    # Frontend dependencies
    if (-not (Test-Path "$ROOT_DIR\apps\desktop\ui\node_modules")) {
        Info "Installing frontend dependencies..."
        Push-Location "$ROOT_DIR\apps\desktop\ui"
        try {
            if (Get-Command pnpm -ErrorAction SilentlyContinue) {
                & pnpm install
            } else {
                & npm install
            }
            Ok "Frontend dependencies installed"
        } finally { Pop-Location }
    }

    Ok "Automatic setup completed"
    Write-Host ""
}

# ---------------------------------------------------------------------------
# Start backend
# ---------------------------------------------------------------------------
Info "Starting backend API server (port 18234)..."
$backendJob = Start-Job -ScriptBlock {
    Set-Location "$using:ROOT_DIR\apps\api"
    & .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 18234
}

# Wait for backend to be ready
Info "Waiting for backend to be ready..."
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:18234/healthz" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) { Ok "Backend is ready"; break }
    } catch { }
    if ($backendJob.State -eq "Failed" -or $backendJob.State -eq "Completed") {
        Err "Backend process crashed during startup. Check logs for details."
    }
    if ($i -eq 30) { Warn "Backend not yet ready after 30s, continuing anyway..." }
    Start-Sleep -Seconds 1
}

# ---------------------------------------------------------------------------
# Start frontend
# ---------------------------------------------------------------------------
Info "Starting frontend dev server (port 5173)..."
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:ROOT_DIR\apps\desktop\ui"
    if (Get-Command pnpm -ErrorAction SilentlyContinue) {
        & pnpm dev
    } else {
        & npm run dev
    }
}

Write-Host ""
Write-Host "=============================================="
Write-Host "  Startup complete!" -ForegroundColor Green
Write-Host "=============================================="
Write-Host ""
Write-Host "  Backend API:       http://localhost:18234"
Write-Host "  API Docs:          http://localhost:18234/api/v1/openapi.json"
Write-Host "  Frontend:          http://localhost:5173"
Write-Host ""
Write-Host "  Press Ctrl+C to stop"
Write-Host ""

# ---------------------------------------------------------------------------
# Wait for processes and cleanup on exit
# ---------------------------------------------------------------------------
try {
    while ($true) {
        if ($backendJob.State -ne "Running" -and $frontendJob.State -ne "Running") { break }
        Start-Sleep -Seconds 2
    }
} finally {
    Info "Stopping servers..."
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -Force -ErrorAction SilentlyContinue
    Remove-Job $frontendJob -Force -ErrorAction SilentlyContinue
    Ok "All servers stopped"
}
