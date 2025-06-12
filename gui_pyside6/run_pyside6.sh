#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REQ_FILE="$SCRIPT_DIR/requirements.uv.in"

# Detect if an active virtual environment is in use
if python - <<'EOF'
import sys
sys.exit(0 if sys.prefix != getattr(sys, 'base_prefix', sys.prefix) else 1)
EOF
then
    PYTHON="python"
else
    VENV_DIR="$HOME/.hybrid_tts/venv"
    if [ ! -d "$VENV_DIR" ]; then
        python -m venv "$VENV_DIR"
    fi
    "$VENV_DIR/bin/pip" install -U pip uv >/dev/null
    "$VENV_DIR/bin/uv" pip install -r "$REQ_FILE"
    PYTHON="$VENV_DIR/bin/python"
fi

CMD="$PYTHON -m gui_pyside6.main $*"

# Launch the app in a new terminal window when available
if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal -- bash -c "$CMD; exec bash"
elif command -v x-terminal-emulator >/dev/null 2>&1; then
    x-terminal-emulator -e bash -c "$CMD; exec bash"
else
    eval "$CMD"
fi
