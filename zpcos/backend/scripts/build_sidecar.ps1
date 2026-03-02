$ErrorActionPreference = "Stop"
$targetTriple = (rustc -Vv | Select-String "host:").Line.Split(" ")[1]
Write-Host "Target triple: $targetTriple" -ForegroundColor Cyan

Push-Location $PSScriptRoot/..
uv run pyinstaller --onefile --name zpcos-backend `
  --add-data "app/auth/connectors;app/auth/connectors" `
  --add-data "app/gateway/providers.json;app/gateway" `
  app/main.py
Pop-Location

$src = Join-Path $PSScriptRoot ".." "dist" "zpcos-backend.exe"
$dstDir = Join-Path $PSScriptRoot ".." ".." "frontend" "src-tauri" "binaries"
$dst = Join-Path $dstDir "zpcos-backend-${targetTriple}.exe"
if (!(Test-Path $dstDir)) { New-Item -ItemType Directory -Force -Path $dstDir }
Copy-Item $src $dst -Force
Write-Host "Sidecar: $dst ($([math]::Round((Get-Item $dst).Length/1MB,1)) MB)" -ForegroundColor Green
