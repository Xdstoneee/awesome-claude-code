# Project Context

## User Environment
- **OS:** Kali Linux running under WSL2 on Windows
- **User:** r3x — home dir is `/home/r3x`, Windows drive at `/mnt/c/Users/r3x`
- **Python:** pyenv, version 3.11.15 at `~/.pyenv/versions/3.11.15/bin/python`
- **Shell:** zsh (Kali default)
- **Repo location:** `~/awesome-claude-code`
- **Active branch:** `claude/multi-source-data-aggregation-9KuKV`

## Rules for This Project

### Always think ahead
- Before writing setup/install steps, simulate the full run on Kali WSL2 and pre-empt every failure
- Never drip-feed one-line fixes — solve the whole problem at once
- On Linux/WSL installs, always check for missing system `.so` libraries, not just Python packages

### WSL2 display requirements
Qt GUI apps on Kali WSL2 need these env vars set before launching:
```bash
export DISPLAY=${DISPLAY:-:0}
export WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-0}
export QT_QPA_PLATFORM=xcb
export LIBGL_ALWAYS_SOFTWARE=1
export QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox --disable-gpu"
```
Always bake these into a `run.sh` launcher — never make the user export them manually.

### Qt/PyQt6 on Kali WSL2 — full system dep list
These must all be installed before PyQt6 will work:
```
libgl1 libegl1 libglib2.0-0 libdbus-1-3 libxkbcommon0
libxcb-cursor0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0
libxcb-keysyms1 libxcb-randr0 libxcb-render-util0
libxcb-shape0 libxcb-xfixes0 libxcb-util1
libxcomposite1 libxdamage1 libxrandr2 libxtst6
libnss3 libnspr4 libasound2 libfontconfig1 libfreetype6
```

### Launchers
- Always provide a `run.sh` (Linux/WSL) and `setup.bat` (Windows)
- `run.sh` must set all display env vars and use `venv/bin/python`
- User launches with `bash run.sh` — nothing else

### Python packaging
- Always use a venv — Kali blocks system-wide pip installs (PEP 668)
- venv lives at `~/awesome-claude-code/venv/`
- Never tell the user to run bare `pip install` without activating the venv first

## Project: Palantir
A real-world multi-source geospatial situational awareness GUI built in PyQt6.
Lives in `palantir/`. Launch with `bash run.sh` from repo root.

### Data sources
| Layer | Source | Key needed |
|---|---|---|
| Aircraft | OpenSky Network (ADS-B) | No (optional for quota) |
| Maritime | aisstream.io (AIS) | Free key: `AISSTREAM_API_KEY` |
| Seismic | USGS earthquake feed | No |
| Weather | NOAA/NWS alerts | No |
| Fire | NASA FIRMS | Free key: `FIRMS_MAP_KEY` |
| Satellites | Celestrak TLEs + sgp4 | No (`pip install sgp4`) |
| Events | GDELT global news | No |
| Traffic | US 511 DOT APIs | No |

### API keys
Stored in `~/.awesome-claude-code/.env` (copied from `.env.example`).

### Key files
- `palantir/app.py` — entry point
- `palantir/gui/main_window.py` — main window
- `palantir/gui/theme.py` — cyberpunk QSS stylesheet
- `palantir/gui/map.html` — Leaflet.js dark map
- `palantir/sources/` — one file per data source
- `palantir/setup.sh` — full setup (run once)
- `run.sh` — generated launcher (run every time)
