# =====================================================================
#  Grief Tracker - one-click Docker launcher (PowerShell)
# =====================================================================
$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "===================================================================" -ForegroundColor Magenta
Write-Host "  Grief Tracker - docker compose up (dev)" -ForegroundColor Magenta
Write-Host "===================================================================" -ForegroundColor Magenta
Write-Host ""

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker is not installed or not on PATH." -ForegroundColor Red
    Write-Host "Install Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Read-Host "Press Enter to close" | Out-Null
    exit 1
}

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "      .env was missing - copied from .env.example" -ForegroundColor Yellow
}

Write-Host "      Default dev admin: admin@local / admin (override via DJANGO_ADMIN_* in .env)" -ForegroundColor DarkGray
Write-Host ""

Start-Job -ScriptBlock {
    Start-Sleep -Seconds 8
    Start-Process "http://localhost:8000/"
} | Out-Null

& docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
