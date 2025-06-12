@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "REQ_FILE=%SCRIPT_DIR%requirements.uv.in"

python -c "import sys; sys.exit(0 if sys.prefix != getattr(sys,'base_prefix', sys.prefix) else 1)" >nul
if "%ERRORLEVEL%"=="0" (
    set "PYTHON=python"
) else (
    set "VENV_DIR=%USERPROFILE%\.hybrid_tts\venv"
    if not exist "%VENV_DIR%" (
        python -m venv "%VENV_DIR%"
    )
    "%VENV_DIR%\Scripts\pip.exe" install -U pip uv >nul
    "%VENV_DIR%\Scripts\uv.exe" pip install -r "%REQ_FILE%"
    set "PYTHON=%VENV_DIR%\Scripts\python.exe"
)

cmd.exe /c start "" %PYTHON% -m gui_pyside6.main %*
