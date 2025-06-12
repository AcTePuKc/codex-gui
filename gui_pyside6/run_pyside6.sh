#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REQ_FILE="$SCRIPT_DIR/requirements.uv.in"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Verify Node.js availability
if ! command -v node >/dev/null 2>&1; then
    echo "Node.js is required but was not found in PATH." >&2
    exit 1
fi

# Determine package manager (pnpm preferred)
if command -v pnpm >/dev/null 2>&1; then
    PKG_MGR="pnpm"
else
    PKG_MGR="npm"
fi

# Ensure the Codex CLI is installed
if ! codex --help >/dev/null 2>&1; then
    echo "Installing @openai/codex globally using $PKG_MGR..."
    $PKG_MGR install -g @openai/codex
fi

# Detect if an active virtual environment is in use
if python3 - <<'EOF'
import sys
sys.exit(0 if sys.prefix != getattr(sys, 'base_prefix', sys.prefix) else 1)
EOF
then
    PYTHON_CMD="python3"
else
    VENV_DIR="$HOME/.hybrid_tts/venv"
    echo "Using virtual environment at: $VENV_DIR"
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
    fi
    "$VENV_DIR/bin/python3" -m ensurepip --upgrade >/dev/null
    "$VENV_DIR/bin/pip" install -U pip uv >/dev/null
    "$VENV_DIR/bin/uv" pip install -r "$REQ_FILE"
    PYTHON_CMD="$VENV_DIR/bin/python3"
fi

CMD="cd \"$REPO_ROOT\" && $PYTHON_CMD -m gui_pyside6.main $*"

# Launch the app in a new terminal window when available
if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal -- bash -c "$CMD; exec bash"
elif command -v x-terminal-emulator >/dev/null 2>&1; then
    x-terminal-emulator -e bash -c "$CMD; exec bash"
else
    eval "$CMD"
fi
