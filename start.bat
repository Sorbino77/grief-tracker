@echo off
REM =====================================================================
REM  Grief Tracker - one-click launcher (Windows)
REM  Double-click to: sync deps -> migrate -> seed -> runserver -> browse
REM =====================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo ====================================================================
echo   Grief Tracker - launcher
echo ====================================================================
echo.

REM ---- 1. uv check ----------------------------------------------------
where uv >nul 2>&1
if errorlevel 1 (
    echo [ERROR] uv is not installed or not on PATH.
    echo.
    echo   Install it from: https://docs.astral.sh/uv/getting-started/installation/
    echo   Quick PowerShell one-liner:
    echo     powershell -c "irm https://astral.sh/uv/install.ps1 ^| iex"
    echo.
    pause
    exit /b 1
)
echo [1/6] uv found.

REM ---- 2. .env exists -------------------------------------------------
if not exist ".env" (
    if exist ".env.example" (
        echo [2/6] No .env found. Copying from .env.example ...
        copy /Y ".env.example" ".env" >nul
    ) else (
        echo [ERROR] No .env and no .env.example to copy from.
        pause
        exit /b 1
    )
) else (
    echo [2/6] .env present.
)

REM ---- 3. Sync dependencies ------------------------------------------
echo [3/6] Syncing dependencies (uv sync) ...
call uv sync
if errorlevel 1 (
    echo [ERROR] uv sync failed.
    pause
    exit /b 1
)

REM ---- 4. Migrate -----------------------------------------------------
echo [4/6] Applying database migrations ...
call uv run python manage.py migrate --noinput
if errorlevel 1 (
    echo [ERROR] migrate failed.
    pause
    exit /b 1
)

REM ---- 5a. Superuser bootstrap (interactive prompt if missing) -------
echo [5/6] Checking for an admin user ...
call uv run python -c "import django,os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development');django.setup();from django.contrib.auth import get_user_model;import sys;sys.exit(0 if get_user_model().objects.filter(is_superuser=True).exists() else 1)" >nul 2>&1
if errorlevel 1 (
    echo       No superuser found. Launching createsuperuser ^(answer the prompts^)...
    echo.
    call uv run python manage.py createsuperuser
    echo.
) else (
    echo       Superuser already exists. Skipping.
)

REM ---- 5b. Excel import bootstrap (only if DB has zero issues) -------
echo       Checking GriefIssue table ...
call uv run python -c "import django,os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development');django.setup();from apps.grief.models import GriefIssue;import sys;sys.exit(0 if GriefIssue.objects.exists() else 1)" >nul 2>&1
if errorlevel 1 (
    if exist "data\Grief_003.xlsm" (
        echo       No issues in DB yet. Importing data\Grief_003.xlsm ...
        call uv run python manage.py import_excel data\Grief_003.xlsm
    ) else (
        echo       No issues in DB. Skipping import - data\Grief_003.xlsm not found.
    )
) else (
    echo       DB already has issues. Skipping import.
)

REM ---- 6. Open browser, then start runserver -------------------------
echo [6/6] Starting development server at http://localhost:8000/ ...
echo       Press Ctrl+C in this window to stop the server.
echo.
start "" "http://localhost:8000/"
call uv run python manage.py runserver

endlocal
