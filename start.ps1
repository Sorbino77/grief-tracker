# =====================================================================
#  Grief Tracker - one-click launcher (PowerShell)
#  Right-click "Run with PowerShell" or:  pwsh -ExecutionPolicy Bypass -File .\start.ps1
#  Does:  uv sync -> migrate -> superuser if missing -> import_excel if empty -> runserver -> browse
# =====================================================================

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

function Step([string]$n, [string]$msg) {
    Write-Host "[${n}] " -NoNewline -ForegroundColor Cyan
    Write-Host $msg
}
function Info([string]$msg) { Write-Host "      $msg" -ForegroundColor DarkGray }
function Ok([string]$msg)   { Write-Host "      $msg" -ForegroundColor Green }
function Warn([string]$msg) { Write-Host "      $msg" -ForegroundColor Yellow }
function Fail([string]$msg) {
    Write-Host ""
    Write-Host "[ERROR] $msg" -ForegroundColor Red
    Write-Host "Press Enter to close..." -ForegroundColor DarkGray
    Read-Host | Out-Null
    exit 1
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Magenta
Write-Host "  Grief Tracker - launcher" -ForegroundColor Magenta
Write-Host "====================================================================" -ForegroundColor Magenta
Write-Host ""

# ---- 1. uv check ----------------------------------------------------
Step "1/6" "Checking for uv..."
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "uv is not installed or not on PATH." -ForegroundColor Yellow
    Write-Host "Install with this PowerShell one-liner, then re-run:" -ForegroundColor Yellow
    Write-Host '  irm https://astral.sh/uv/install.ps1 | iex' -ForegroundColor Cyan
    Fail "uv missing"
}
Ok "uv found ($(uv --version))"

# ---- 2. .env --------------------------------------------------------
Step "2/6" "Checking .env..."
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Warn ".env was missing - copied from .env.example"
    } else {
        Fail "Neither .env nor .env.example found."
    }
} else {
    Ok ".env present."
}

# ---- 3. uv sync -----------------------------------------------------
Step "3/6" "Syncing dependencies (uv sync)..."
& uv sync
if ($LASTEXITCODE -ne 0) { Fail "uv sync failed (exit $LASTEXITCODE)" }
Ok "Dependencies in sync."

# ---- 4. migrate -----------------------------------------------------
Step "4/6" "Applying database migrations..."
& uv run python manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { Fail "migrate failed (exit $LASTEXITCODE)" }
Ok "Migrations applied."

# ---- 5a. superuser --------------------------------------------------
Step "5/6" "Bootstrapping admin user and seed data..."

$probe = @"
import django, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
from django.contrib.auth import get_user_model
sys.exit(0 if get_user_model().objects.filter(is_superuser=True).exists() else 1)
"@
& uv run python -c $probe 2>$null
if ($LASTEXITCODE -eq 0) {
    Ok "Superuser already exists - skipping."
} else {
    Warn "No superuser found. Launching createsuperuser (answer the prompts)..."
    Write-Host ""
    & uv run python manage.py createsuperuser
    if ($LASTEXITCODE -ne 0) {
        Warn "createsuperuser was cancelled or failed - continuing anyway."
    } else {
        Ok "Superuser created."
    }
}

# ---- 5b. excel import ----------------------------------------------
$emptyProbe = @"
import django, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
from apps.grief.models import GriefIssue
sys.exit(0 if GriefIssue.objects.exists() else 1)
"@
& uv run python -c $emptyProbe 2>$null
if ($LASTEXITCODE -eq 0) {
    Ok "DB already has issues - skipping import."
} else {
    $excel = "data\Grief_003.xlsm"
    if (Test-Path $excel) {
        Warn "DB has no issues yet. Importing $excel..."
        & uv run python manage.py import_excel $excel
        if ($LASTEXITCODE -ne 0) { Warn "import_excel returned $LASTEXITCODE - continuing." } else { Ok "Excel data imported." }
    } else {
        Warn "$excel not found. Place your Grief workbook there to seed the DB."
    }
}

# ---- 6. runserver + browser ----------------------------------------
Step "6/6" "Starting dev server at http://localhost:8000/ ..."
Info "Press Ctrl+C in this window to stop the server."
Write-Host ""

# kick the browser open after a short delay so it doesn't beat the server
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8000/"
} | Out-Null

& uv run python manage.py runserver
