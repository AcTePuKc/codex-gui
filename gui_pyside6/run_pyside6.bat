@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "REQ_FILE=%SCRIPT_DIR%requirements.uv.in"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"

rem Verify Node.js availability
where node >nul 2>&1
if errorlevel 1 (
    echo Node.js is required but was not found in PATH.
    exit /b 1
)

rem Determine package manager (pnpm preferred)
where pnpm >nul 2>&1
if %errorlevel%==0 (
    set "PKG_MGR=pnpm"
) else (
    set "PKG_MGR=npm"
)

rem Ensure the Codex CLI is installed
codex --help >nul 2>&1
if errorlevel 1 (
    echo Installing @openai/codex globally using %PKG_MGR%...
    %PKG_MGR% install -g @openai/codex
)

python -c "import sys; sys.exit(0 if sys.prefix != getattr(sys,'base_prefix', sys.prefix) else 1)" >nul
if "%ERRORLEVEL%"=="0" (
    set "PYTHON_CMD=python"
) else (
    set "VENV_DIR=%USERPROFILE%\.hybrid_tts\venv"
    if not exist "%VENV_DIR%" (
        where uv >nul 2>&1
        if %errorlevel%==0 (
            uv venv "%VENV_DIR%" --python python3.11
        ) else (
            py -3.11 -m venv "%VENV_DIR%"
        )
    )
    "%VENV_DIR%\Scripts\pip.exe" install -U pip uv >nul
    "%VENV_DIR%\Scripts\uv.exe" pip install -r "%REQ_FILE%"
    set "PYTHON_CMD=%VENV_DIR%\Scripts\python.exe"
)

pushd "%REPO_ROOT%" >nul
cmd.exe /c start "" %PYTHON_CMD% -m gui_pyside6.main %*
popd >nul
