<#
.SYNOPSIS
  Starts Vigilo on this computer: the API and the web interface, then opens the browser.

.DESCRIPTION
  Used by "Start Vigilo.cmd" and "Start Vigilo (active scan).cmd" at the root of the
  repository, so Vigilo starts with a double-click. Each part runs in its own window;
  close both windows to stop Vigilo.

  -Active also enables the verified active scan. It needs Docker Desktop to be running.
#>
param(
    [switch]$Active,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Stop-WithMessage([string]$message) {
    Write-Host ""
    Write-Host $message -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to close this window"
    exit 1
}

function Test-Port([int]$port) {
    $listening = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $listening
}

Write-Host "Vigilo" -ForegroundColor Cyan
Write-Host "------"

# 1. Python environment
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Stop-WithMessage ("The Python environment is missing. In a terminal in this folder, run:`n" +
        "  python -m venv .venv`n  .venv\Scripts\python -m pip install -e "".[dev]""`n" +
        "then start Vigilo again.")
}

# 2. Web interface dependencies (first start only)
if (-not (Test-Path (Join-Path $root "web\node_modules"))) {
    Write-Host "First start: installing the web interface (a few minutes)..."
    Push-Location (Join-Path $root "web")
    npm install
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) { Stop-WithMessage "npm install failed. Is Node.js installed?" }
}

# 3. Active scan: Docker must be running, and the scanner templates installed once
$envLines = @()
if ($Active) {
    $docker = (Get-Command docker -ErrorAction SilentlyContinue).Source
    if (-not $docker) {
        $docker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    }
    if (-not (Test-Path $docker)) {
        Stop-WithMessage "Docker Desktop is not installed. Install it, or use 'Start Vigilo.cmd' without the active scan."
    }
    & $docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage ("Docker is not running. Open Docker Desktop, wait until it says " +
            "'Engine running', then start Vigilo again.")
    }
    & $docker volume inspect vigilo-nuclei-templates *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "First active start: installing the scanner templates (about a minute)..."
        $env:VIGILO_DOCKER = $docker
        & (Join-Path $root ".venv\Scripts\vigilo.exe") prepare-active
        if ($LASTEXITCODE -ne 0) { Stop-WithMessage "The scanner templates could not be installed." }
    }
    New-Item -ItemType Directory -Force (Join-Path $root ".vigilo") | Out-Null
    $envLines = @(
        "`$env:VIGILO_ACTIVE_SCAN = '1'",
        "`$env:VIGILO_DOCKER = '$docker'",
        "`$env:VIGILO_CONSENT_LOG = '$(Join-Path $root ".vigilo\consent.jsonl")'"
    )
}

# 4. Already running?
if ((Test-Port 3000) -or (Test-Port 8000)) {
    Write-Host "Vigilo seems to be running already (port 3000 or 8000 is in use)."
    Write-Host "Close its two windows first to restart it, or open http://localhost:3000"
    if (-not $NoBrowser) { Start-Process "http://localhost:3000" }
    Start-Sleep -Seconds 5
    exit 0
}

# 5. API window
$mode = if ($Active) { " (active scan on)" } else { "" }
$apiCommand = ($envLines + @(
    "`$Host.UI.RawUI.WindowTitle = 'Vigilo API$mode - close to stop'",
    "Set-Location '$root'",
    "& '.venv\Scripts\uvicorn.exe' vigilo.api:app --port 8000 --no-server-header --no-proxy-headers"
)) -join "; "
Start-Process powershell -ArgumentList "-NoExit", "-NoProfile", "-Command", $apiCommand

# 6. Web interface window
$webEnv = if ($Active) { "`$env:NEXT_PUBLIC_VIGILO_ACTIVE_SCAN = '1'; " } else { "" }
$webCommand = $webEnv + (@(
    "`$Host.UI.RawUI.WindowTitle = 'Vigilo website$mode - close to stop'",
    "Set-Location '$(Join-Path $root "web")'",
    "npm run dev"
) -join "; ")
Start-Process powershell -ArgumentList "-NoExit", "-NoProfile", "-Command", $webCommand

# 7. Wait until the website answers, then open it
Write-Host "Starting... (the first time can take up to a minute)"
$ready = $false
for ($i = 0; $i -lt 90; $i++) {
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000/en" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
}
if (-not $ready) {
    Stop-WithMessage "The website did not start. Look at the two Vigilo windows for an error message."
}

Write-Host ""
Write-Host "Vigilo is ready: http://localhost:3000" -ForegroundColor Green
Write-Host "To stop Vigilo, close its two windows."
if (-not $NoBrowser) { Start-Process "http://localhost:3000" }
Start-Sleep -Seconds 4
