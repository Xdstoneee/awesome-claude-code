#!/usr/bin/env python3
"""
PALANTIR — Global Situational Awareness Dashboard
Multi-source real-world data aggregation GUI.

Usage:
    python -m palantir          # launch GUI
    python -m palantir --fetch  # headless fetch, write output/latest.geojson

Sources (configure via environment variables — see .env.example):
    OpenSky Network   — ADS-B aircraft positions        (free, optional OPENSKY_USERNAME/PASSWORD)
    AISstream.io      — Maritime AIS vessel positions   (free API key: AISSTREAM_API_KEY)
    USGS              — Real-time earthquake events      (free, no key)
    NOAA / NWS        — Active US weather alerts         (free, no key)
    NASA FIRMS        — Satellite fire/hotspot data      (free key: FIRMS_MAP_KEY)
    Celestrak         — Orbital TLE satellite positions  (free, no key; needs: pip install sgp4)
    GDELT             — Global news/conflict events      (free, no key)
    US 511 APIs       — Open traffic incident feeds      (free, no key)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def launch_gui() -> int:
    try:
        from PyQt6.QtCore import Qt
        from PyQt6.QtWebEngineWidgets import QWebEngineView  # must be before QApplication
        from PyQt6.QtWidgets import QApplication
    except ImportError as e:
        print(
            f"ERROR: PyQt6 import failed — {e}\n\n"
            "  Run the setup script to fix automatically:\n"
            "    bash palantir/setup.sh          (Linux/WSL/macOS)\n"
            "    palantir\\setup.bat              (Windows)\n\n"
            "  Or manually:\n"
            "    sudo apt install libgl1 libegl1 libxcb-cursor0   # Linux/WSL\n"
            "    pip install PyQt6 PyQt6-WebEngine",
            file=sys.stderr,
        )
        return 1

    # Load .env file if present
    _load_dotenv()

    app = QApplication(sys.argv)
    app.setApplicationName("Palantir")
    app.setApplicationDisplayName("PALANTIR // Global Situational Awareness")

    from palantir.gui import theme
    theme.apply(app)

    from palantir.gui.main_window import MainWindow
    win = MainWindow()
    win.show()

    return app.exec()


def headless_fetch(output_path: Path) -> int:
    """Fetch all sources without a GUI and write a GeoJSON file."""
    _load_dotenv()

    from palantir.sources import adsb, ais, seismic, weather, fire, satellites, gdelt, traffic

    fetchers = [
        ("aircraft",  adsb.fetch,       {}),
        ("maritime",  ais.fetch,        {}),
        ("seismic",   seismic.fetch,    {"feed": "all_day"}),
        ("weather",   weather.fetch,    {}),
        ("fire",      fire.fetch,       {}),
        ("satellite", satellites.fetch, {}),
        ("events",    gdelt.fetch,      {"max_records": 300}),
        ("traffic",   traffic.fetch,    {}),
    ]

    all_features = []
    for name, fn, kwargs in fetchers:
        print(f"[{name.upper()}]")
        try:
            result = fn(**kwargs)
            print(f"  → {len(result.records)} records")
            for rec in result.records:
                all_features.append(rec.to_geojson_feature())
        except Exception as exc:
            print(f"  ✗ {exc}", file=sys.stderr)

    geojson = {"type": "FeatureCollection", "features": all_features}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(geojson, indent=2), encoding="utf-8")
    print(f"\n✓ Wrote {len(all_features):,} features → {output_path}")
    return 0


def _load_dotenv() -> None:
    """Load .env file from project root if python-dotenv is installed."""
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"✓ Loaded env from {env_file}")
    except ImportError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="palantir",
        description="Global Situational Awareness Dashboard",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Headless fetch — write output/latest.geojson and exit",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "output" / "latest.geojson",
        help="Output GeoJSON path for --fetch mode",
    )
    args = parser.parse_args()

    if args.fetch:
        return headless_fetch(args.output)
    return launch_gui()


if __name__ == "__main__":
    sys.exit(main())
