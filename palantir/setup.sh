#!/usr/bin/env bash
# PALANTIR — one-shot setup script
# Works on: Kali/Debian/Ubuntu (native + WSL), macOS
# On Windows (no WSL): use setup.bat instead
set -e

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
    if [ -d /mnt/wslg ]; then
        IS_WSLG=true
    fi
fi

# ── 1. System dependencies ───────────────────────────────────────────────────
if [[ "$OSTYPE" == "linux"* ]]; then
    echo "[1/5] Installing system libraries..."
    PKGS=(
        # Qt core
        libgl1 libegl1 libglib2.0-0 libdbus-1-3 libxkbcommon0
        # XCB / X11
        libxcb-cursor0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0
        libxcb-keysyms1 libxcb-randr0 libxcb-render-util0
        libxcb-shape0 libxcb-xfixes0 libxcb-util1
        # Qt WebEngine (Chromium) — extensive deps
        libxcomposite1 libxdamage1 libxrandr2 libxtst6
        libnss3 libnspr4 libasound2
        # Font rendering (prevents blank text in WebEngine)
        libfontconfig1 libfreetype6
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
" || { echo "  Import verification failed — check errors above"; exit 1; }

# ── .env file ────────────────────────────────────────────────────────────────
if [ ! -f "$REPO_DIR/.env" ]; then
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
    echo "  ✓ Created .env — add API keys there to unlock more sources"
fi

# ── Detect display / WSL config and write run.sh ─────────────────────────────
echo ""
echo "Configuring display for your environment..."

QT_VARS=""

if [ "$IS_WSL" = true ]; then
    if [ "$IS_WSLG" = true ]; then
        # Windows 11 WSLg — Wayland/X11 forwarding built in
        echo "  ✓ Detected WSLg (Windows 11) — using built-in display forwarding"
        QT_VARS='export DISPLAY=${DISPLAY:-:0}
export WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-0}
export QT_QPA_PLATFORM=xcb
export LIBGL_ALWAYS_SOFTWARE=1
export QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox --disable-gpu"'
    else
        # Windows 10 WSL — needs X server on Windows side
        WIN_IP=$(grep nameserver /etc/resolv.conf | awk '{print $2}' | head -1)
        echo "  ! Detected WSL without WSLg (Windows 10)"
        echo "    You need VcXsrv running on Windows with 'Disable access control' checked"
        echo "    Download: https://sourceforge.net/projects/vcxsrv/"
        QT_VARS="export DISPLAY=${WIN_IP}:0.0
export QT_QPA_PLATFORM=xcb
export LIBGL_ALWAYS_SOFTWARE=1
export QTWEBENGINE_CHROMIUM_FLAGS=\"--no-sandbox --disable-gpu\""
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  ✓ macOS detected"
    QT_VARS='export QT_QPA_PLATFORM=cocoa'
else
    # Native Linux
    echo "  ✓ Native Linux — using system display"
    QT_VARS='export DISPLAY=${DISPLAY:-:0}
export QT_QPA_PLATFORM=xcb
export QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox"'
fi

# Write the launcher script
cat > "$RUN_SCRIPT" << LAUNCHER
#!/usr/bin/env bash
# Auto-generated by palantir/setup.sh — re-run setup.sh to regenerate
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
cd "\$SCRIPT_DIR"
${QT_VARS}
exec "\$SCRIPT_DIR/venv/bin/python" -m palantir "\$@"
LAUNCHER
chmod +x "$RUN_SCRIPT"
echo "  ✓ Created run.sh launcher"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║  Setup complete. Launch with:        ║"
echo "  ║                                      ║"
echo "  ║    bash run.sh                       ║"
echo "  ╚══════════════════════════════════════╝"
echo ""
