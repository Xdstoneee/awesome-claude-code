#!/usr/bin/env bash
# PALANTIR — one-shot setup script
# Works on: Kali/Debian/Ubuntu (native + WSL), macOS
# On Windows (no WSL): use setup.bat instead

PYTHON=${PYTHON:-python3}
PALANTIR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$PALANTIR_DIR")"
VENV_DIR="$REPO_DIR/venv"
RUN_SCRIPT="$REPO_DIR/run.sh"

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

# ── Detect environment ───────────────────────────────────────────────────────
IS_WSL=false
IS_WSLG=false
if grep -qi microsoft /proc/version 2>/dev/null; then
    IS_WSL=true
    [ -d /mnt/wslg ] && IS_WSLG=true
fi

# ── 1. System dependencies ───────────────────────────────────────────────────
if [[ "$OSTYPE" == "linux"* ]]; then
    echo "[1/5] Installing system libraries..."

    # Let apt resolve ALL Qt deps by installing the system Qt packages.
    # We don't use them directly (we use the venv's PyQt6) but this pulls
    # every required .so onto the system with correct symlinks — no guessing.
    sudo apt-get install -y --no-install-recommends \
        python3-pyqt6 \
        python3-pyqt6.qtwebengine \
        2>&1 | grep -E "(Setting up|already the newest|error)" || true

    # Refresh linker cache
    sudo ldconfig 2>/dev/null || true
    echo "  ✓ System libraries ready"
else
    echo "[1/5] macOS — skipping apt installs"
fi

# ── 2. Python version check ──────────────────────────────────────────────────
echo "[2/5] Checking Python..."
PY_VER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo $PY_VER | cut -d. -f1)
PY_MINOR=$(echo $PY_VER | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || [ "$PY_MINOR" -lt 10 ]; then
    echo "  ✗ Python 3.10+ required, found $PY_VER"
    echo "    Hint: PYTHON=python3.11 bash palantir/setup.sh"
    exit 1
fi
echo "  ✓ Python $PY_VER"

# ── 3. Virtual environment ───────────────────────────────────────────────────
echo "[3/5] Setting up virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON -m venv "$VENV_DIR"
    echo "  ✓ Created $VENV_DIR"
else
    echo "  ✓ venv already exists"
fi
PIP="$VENV_DIR/bin/pip"
PYTHON_VENV="$VENV_DIR/bin/python"
$PIP install --upgrade pip --quiet

# ── 4. Python packages ───────────────────────────────────────────────────────
echo "[4/5] Installing Python packages..."
$PIP install -r "$PALANTIR_DIR/requirements.txt" --quiet
echo "  ✓ Packages installed"

# ── 5. Verify imports ────────────────────────────────────────────────────────
echo "[5/5] Verifying install..."
VERIFY_OK=true
$PYTHON_VENV -c "
import sys
ok = True
for mod in ['PyQt6.QtWidgets', 'PyQt6.QtWebEngineWidgets', 'requests', 'websocket']:
    try:
        __import__(mod)
        print(f'  ✓ {mod}')
    except ImportError as e:
        print(f'  ✗ {mod}: {e}')
        ok = False
sys.exit(0 if ok else 1)
" || VERIFY_OK=false

# ── .env file ────────────────────────────────────────────────────────────────
if [ ! -f "$REPO_DIR/.env" ]; then
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
    echo "  ✓ Created .env — add API keys there to unlock more sources"
fi

# ── Write run.sh — always, even if verify had warnings ───────────────────────
echo ""
echo "Configuring display..."

if [ "$IS_WSL" = true ]; then
    if [ "$IS_WSLG" = true ]; then
        echo "  ✓ WSLg (Windows 11) detected"
        QT_ENV='export DISPLAY=${DISPLAY:-:0}
export WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-0}
export QT_QPA_PLATFORM=xcb
export LIBGL_ALWAYS_SOFTWARE=1
export QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox --disable-gpu"'
    else
        WIN_IP=$(grep nameserver /etc/resolv.conf | awk '{print $2}' | head -1)
        echo "  ! WSL without WSLg — needs VcXsrv on Windows (sourceforge.net/projects/vcxsrv)"
        QT_ENV="export DISPLAY=${WIN_IP}:0.0
export QT_QPA_PLATFORM=xcb
export LIBGL_ALWAYS_SOFTWARE=1
export QTWEBENGINE_CHROMIUM_FLAGS=\"--no-sandbox --disable-gpu\""
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  ✓ macOS"
    QT_ENV='export QT_QPA_PLATFORM=cocoa'
else
    echo "  ✓ Native Linux"
    QT_ENV='export DISPLAY=${DISPLAY:-:0}
export QT_QPA_PLATFORM=xcb
export QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox"'
fi

cat > "$RUN_SCRIPT" << LAUNCHER
#!/usr/bin/env bash
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
cd "\$SCRIPT_DIR"
${QT_ENV}
exec "\$SCRIPT_DIR/venv/bin/python" -m palantir "\$@"
LAUNCHER
chmod +x "$RUN_SCRIPT"
echo "  ✓ run.sh created"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
if [ "$VERIFY_OK" = true ]; then
    echo "  ╔══════════════════════════════════════╗"
    echo "  ║  Setup complete. Launch with:        ║"
    echo "  ║                                      ║"
    echo "  ║    bash run.sh                       ║"
    echo "  ╚══════════════════════════════════════╝"
else
    echo "  ╔══════════════════════════════════════════════════════╗"
    echo "  ║  WARNING: some imports failed (see above)            ║"
    echo "  ║  Try launching anyway — bash run.sh                  ║"
    echo "  ║  If it crashes, run: bash palantir/setup.sh again    ║"
    echo "  ╚══════════════════════════════════════════════════════╝"
fi
echo ""
