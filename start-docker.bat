@echo off
REM =====================================================================
REM  Grief Tracker - one-click Docker launcher (Windows)
REM  Builds + starts the dev stack (postgres + Django runserver).
REM  Auto: migrate, bootstrap admin@local/admin, seed Excel on first run.
REM =====================================================================
setlocal
cd /d "%~dp0"

echo.
echo ====================================================================
echo   Grief Tracker - docker compose up (dev)
echo ====================================================================
echo.

where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not on PATH.
    echo Install Docker Desktop: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        echo No .env found. Copying from .env.example ...
        copy /Y ".env.example" ".env" >nul
    )
)

REM Open browser after a short delay so it doesn't beat the server.
start "" cmd /c "timeout /t 8 /nobreak >nul & start http://localhost:8000/"

docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

endlocal
