#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REQ_FILE="$SCRIPT_DIR/requirements.uv.in"
SENTINEL_FILE="$SCRIPT_DIR/.deps_installed"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

INSTALL_DEPS=1
if [ -f "$SENTINEL_FILE" ] && [ "$SENTINEL_FILE" -nt "$REQ_FILE" ]; then
    INSTALL_DEPS=0
fi

# Verify Node.js availability
if ! command -v node >/dev/null 2>&1; then
    echo "Node.js is required but was not found in PATH." >&2
    exit 1
fi

# Determine package manager (pnpm preferred)
if command -v pnpm >/dev/null 2>&1; then
    PKG_MGR="pnpm"
    PNPM_BIN_DIR="$(pnpm bin -g 2>/dev/null || true)"
    if [ -n "$PNPM_BIN_DIR" ] && [ -x "$PNPM_BIN_DIR/codex" ]; then
        export PATH="$PNPM_BIN_DIR:$PATH"
    fi
else
    PKG_MGR="npm"
fi

# Ensure the Codex CLI is installed only if missing
if ! command -v codex >/dev/null 2>&1; then
    echo "Codex CLI not found. Attempting global install using $PKG_MGR..."
    if $PKG_MGR install -g @openai/codex --timeout=15000 >/dev/null 2>&1; then
        echo "Codex CLI successfully installed."
    else
        echo
        echo "[WARN] First install attempt failed. Trying with alternative mirror..."
        if $PKG_MGR install -g @openai/codex --registry=https://registry.npmmirror.com --timeout=15000; then
            echo "Codex CLI installed using mirror registry."
        else
            echo
            echo "Failed to install @openai/codex using mirror."
            echo "You may need to install it manually:"
            echo "    $PKG_MGR install -g @openai/codex --registry=https://registry.npmmirror.com"
        fi
    fi
else
    echo "Codex CLI already installed."
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
    if [ "$INSTALL_DEPS" -eq 1 ]; then
        VIRTUAL_ENV="$VENV_DIR" "$VENV_DIR/bin/uv" pip install -r "$REQ_FILE"
        touch "$SENTINEL_FILE"
    else
        echo "Requirements unchanged; skipping installation."
    fi
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
