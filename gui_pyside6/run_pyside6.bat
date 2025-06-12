@echo off
setlocal enabledelayedexpansion

:: Paths
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"
set "REQ_FILE=%SCRIPT_DIR%requirements.uv.in"

echo ======================================================
echo  Codex GUI Launcher - Environment Setup Assistant
echo ======================================================

:: STEP 1: Node.js Check
echo.
echo [Step 1] Checking for Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo Node.js not found. Please install it from https://nodejs.org/
    echo Script will exit now.
    pause
    exit /b 1
)
echo Node.js found.

:: STEP 2: Package Manager Check
echo.
echo [Step 2] Checking for package manager (pnpm preferred)...
where pnpm >nul 2>&1
if %errorlevel%==0 (
    set "PKG_MGR=pnpm"
    echo pnpm found.
) else (
    echo pnpm not found. Checking for npm fallback...
    where npm >nul 2>&1
    if %errorlevel%==0 (
        set "PKG_MGR=npm"
        echo npm found.
        echo   Tip: pnpm is faster. You can install it via: npm install -g pnpm
    ) else (
        echo npm was not found either. Cannot continue without a package manager.
        pause
        exit /b 1
    )
)

:STEP_3
:: STEP 3: Python Environment Setup
echo.
echo [Step 3] Setting up Python environment...

python -c "import sys; sys.exit(0 if hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix else 1)" >nul 2>&1
if %ERRORLEVEL%==0 (
    set "PYTHON_CMD=python"
    echo Running inside an active virtual environment.
    goto AFTER_VENV
)

set "VENV_DIR=%USERPROFILE%\.hybrid_tts\venv"
set "UV_BIN=%~dp0tools\uv.exe"
echo Using virtual environment at: %VENV_DIR%

:: Fallback: Check in ~/.local/bin
if not exist "%UV_BIN%" (
    if exist "%USERPROFILE%\.local\bin\uv.exe" (
        set "UV_BIN=%USERPROFILE%\.local\bin\uv.exe"
    )
)

:: Check PATH
if not exist "%UV_BIN%" (
    where uv >nul 2>&1
    if %ERRORLEVEL%==0 (
        for /f "delims=" %%I in ('where uv') do set "UV_BIN=%%I"
    )
)

:: Prompt install if still not found
if not exist "%UV_BIN%" (
    echo UV not found in tools, PATH, or .local\bin
    set /p USERCHOICE="Install UV using pip now? (Y/N): "
    if /I "%USERCHOICE%"=="Y" (
        pip install uv
        echo UV installed via pip. Restarting this step...
        goto STEP_3
    ) else (
        echo Continuing without UV.
        set "UV_BIN="
    )
)

:: Create venv
if not exist "%VENV_DIR%" (
    echo Virtual environment not found. Creating one...
    if defined UV_BIN (
        echo Using UV: %UV_BIN%
        "%UV_BIN%" venv "%VENV_DIR%" --python python3.11
    ) else (
        py -3.11 -m venv "%VENV_DIR%"
    )
)

"%VENV_DIR%\Scripts\python.exe" -m ensurepip --upgrade >nul 2>&1

:: Update pip and install requirements
echo Updating pip...
"%VENV_DIR%\Scripts\python.exe" -m pip install -U pip >nul

echo Installing requirements...
if defined UV_BIN (
    "%UV_BIN%" pip install -r "%REQ_FILE%"
) else (
    "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%REQ_FILE%"
)

set "PYTHON_CMD=%VENV_DIR%\Scripts\python.exe"

:AFTER_VENV

:: STEP 4: Codex CLI Check & Install
echo.
echo [Step 4] Checking for Codex CLI...
where codex >nul 2>&1
if errorlevel 1 (
    echo Codex CLI not found. Attempting global install using %PKG_MGR%...

    %PKG_MGR% install -g @openai/codex --timeout=15000 >nul 2>&1
    if errorlevel 1 (
        echo.
        echo [WARN] First install attempt failed. Trying with alternative mirror...
        %PKG_MGR% install -g @openai/codex --registry=https://registry.npmmirror.com --timeout=15000
        if errorlevel 1 (
            echo.
            echo Failed to install @openai/codex using mirror.
            echo You may need to install it manually:
            echo     %PKG_MGR% install -g @openai/codex --registry=https://registry.npmmirror.com
        ) else (
            echo Codex CLI installed using mirror registry.
        )
    ) else (
        echo Codex CLI successfully installed.
    )
) else (
    echo Codex CLI already installed.
)

echo.
echo [Step 5] Launching Codex GUI...
rem === Launch GUI ===
pushd "%REPO_ROOT%" >nul
echo [INFO] Launching Codex GUI...
"%PYTHON_CMD%" -m gui_pyside6.main %*
popd >nul
