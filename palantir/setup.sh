#!/usr/bin/env bash
# PALANTIR — one-shot setup script
# Works on: Kali/Debian/Ubuntu WSL, native Linux, macOS
# On Windows: use setup.bat instead
set -e

PYTHON=${PYTHON:-python3}
PALANTIR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$PALANTIR_DIR")"

echo ""
echo "  ██████╗  █████╗ ██╗      █████╗ ███╗   ██╗████████╗██╗██████╗ "
echo "  ██╔══██╗██╔══██╗██║     ██╔══██╗████╗  ██║╚══██╔══╝██║██╔══██╗"
echo "  ██████╔╝███████║██║     ███████║██╔██╗ ██║   ██║   ██║██████╔╝"
echo "  ██╔═══╝ ██╔══██║██║     ██╔══██║██║╚██╗██║   ██║   ██║██╔══██╗"
echo "  ██║     ██║  ██║███████╗██║  ██║██║ ╚████║   ██║   ██║██║  ██║"
echo "  ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═╝"
echo ""
echo "  GLOBAL SITUATIONAL AWARENESS // SETUP"
echo ""

# ── 1. System dependencies (Linux only) ────────────────────────────────────
if [[ "$OSTYPE" == "linux"* ]]; then
    echo "[1/4] Installing system libraries..."
    PKGS=(
        # Qt core
        libgl1 libegl1 libglib2.0-0 libdbus-1-3 libxkbcommon0
        # XCB / X11 — Qt widgets
        libxcb-cursor0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0
        libxcb-keysyms1 libxcb-randr0 libxcb-render-util0
        libxcb-shape0 libxcb-xfixes0 libxcb-util1
        # Qt WebEngine (Chromium-based) — the needy one
        libxcomposite1 libxdamage1 libxrandr2 libxtst6
        libnss3 libnspr4 libasound2
    )
    MISSING=()
    for pkg in "${PKGS[@]}"; do
        dpkg -s "$pkg" &>/dev/null || MISSING+=("$pkg")
    done
    if [ ${#MISSING[@]} -gt 0 ]; then
        echo "  Installing: ${MISSING[*]}"
        sudo apt-get install -y "${MISSING[@]}" 2>&1 | grep -E "(Setting up|already|error)" || true
    else
        echo "  ✓ All system libraries present"
    fi
else
    echo "[1/4] macOS detected — skipping apt installs"
fi

# ── 2. Python version check ─────────────────────────────────────────────────
echo "[2/4] Checking Python..."
PY_VER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo $PY_VER | cut -d. -f1)
PY_MINOR=$(echo $PY_VER | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || [ "$PY_MINOR" -lt 10 ]; then
    echo "  ✗ Python 3.10+ required, found $PY_VER"
    echo "    Use: PYTHON=python3.11 bash palantir/setup.sh"
    exit 1
fi
echo "  ✓ Python $PY_VER"

# ── 3. Virtual environment ───────────────────────────────────────────────────
echo "[3/4] Setting up virtual environment..."
VENV_DIR="$REPO_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON -m venv "$VENV_DIR"
    echo "  ✓ Created venv at $VENV_DIR"
else
    echo "  ✓ venv already exists"
fi

PIP="$VENV_DIR/bin/pip"
PYTHON_VENV="$VENV_DIR/bin/python"

$PIP install --upgrade pip --quiet

# ── 4. Python packages ───────────────────────────────────────────────────────
echo "[4/4] Installing Python packages..."
$PIP install -r "$REPO_DIR/palantir/requirements.txt"

# ── 5. Verify PyQt6 actually imports ────────────────────────────────────────
echo ""
echo "Verifying install..."
$PYTHON_VENV -c "
import sys
failures = []
for mod, pkg in [
    ('PyQt6.QtWidgets',        'PyQt6'),
    ('PyQt6.QtWebEngineWidgets','PyQt6-WebEngine'),
    ('requests',                'requests'),
    ('websocket',               'websocket-client'),
]:
    try:
        __import__(mod)
        print(f'  ✓ {mod}')
    except ImportError as e:
        print(f'  ✗ {mod}: {e}')
        failures.append(pkg)
if failures:
    print(f'\nFailed imports — re-run: bash palantir/setup.sh')
    sys.exit(1)
"

# ── 6. .env file ─────────────────────────────────────────────────────────────
if [ ! -f "$REPO_DIR/.env" ]; then
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
    echo "  ✓ Created .env from .env.example — add your API keys there"
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "  ✓ Setup complete."
echo ""
echo "  Run with:"
echo "    source venv/bin/activate && python -m palantir"
echo ""
echo "  Or (without activating venv):"
echo "    venv/bin/python -m palantir"
echo ""
