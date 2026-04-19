"""
Main application window — the God's Eye situational awareness dashboard.

Layout
──────
┌─────────────────────────────────────────────────────────────────────┐
│  PALANTIR // GLOBAL SITUATIONAL AWARENESS  ──  [REFRESH] [PAUSE]   │
├──────────┬──────────────────────────────────────────┬──────────────-┤
│ SOURCE   │                                          │  LIVE FEED   │
│ PANEL    │         DARK LEAFLET MAP                 │  (scroll log)│
│          │         (CartoDB Dark Matter)             │              │
│ ● ADS-B  │                                          │              │
│ ● AIS    │                                          │              │
│ ● SEISMC │                                          │              │
│ ● WEATHR │                                          │              │
│ ● FIRE   │                                          │              │
│ ● SAT    │                                          │              │
│ ● GDELT  │                                          │              │
│ ● TRAFFC │                                          │              │
├──────────┴──────────────────────────────────────────┴──────────────-┤
│ STATUS: LIVE │ AIRCRAFT:1247 │ SHIPS:892 │ QUAKES:12 │ NEXT: 58s   │
└─────────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from palantir.gui.feed_panel import FeedPanel
from palantir.gui.map_widget import MapWidget
from palantir.gui.source_panel import SourcePanel
from palantir.gui import theme
from palantir.models import GeoRecord, Layer, SourceResult
from palantir.worker import FetchWorker

# Source (layer_name, display_label, fetch_fn, kwargs)
from palantir.sources import adsb, ais, seismic, weather, fire, satellites, gdelt, traffic

_SOURCE_DEFS: list[tuple[str, str, Any, dict]] = [
    ("aircraft",  "ADS-B",    adsb.fetch,        {}),
    ("maritime",  "AIS",      ais.fetch,         {}),
    ("seismic",   "SEISMIC",  seismic.fetch,     {"feed": "all_day"}),
    ("weather",   "WEATHER",  weather.fetch,     {}),
    ("fire",      "FIRE",     fire.fetch,        {}),
    ("satellite", "SAT-TLE",  satellites.fetch,  {}),
    ("events",    "GDELT",    gdelt.fetch,       {"max_records": 300}),
    ("traffic",   "TRAFFIC",  traffic.fetch,     {}),
]

_DEFAULT_REFRESH_SECS = 60
_OUTPUT_DIR = Path(__file__).parent.parent / "output"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PALANTIR // GLOBAL SITUATIONAL AWARENESS")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        self._all_records: dict[str, list[GeoRecord]] = {}
        self._workers: list[FetchWorker] = []
        self._paused = False
        self._countdown = _DEFAULT_REFRESH_SECS
        self._pending_fetches = 0

        self._build_ui()
        self._start_refresh_cycle()

    # ── UI Construction ─────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(6, 6, 6, 6)
        root_layout.setSpacing(4)

        # ── Top header bar ──
        header_bar = QHBoxLayout()
        header_bar.setSpacing(12)

        title = QLabel("⬡ PALANTIR // GLOBAL SITUATIONAL AWARENESS ⬡")
        title.setObjectName("header")
        title.setStyleSheet(
            f"color: {theme.GREEN}; font-size: 14px; font-weight: bold; letter-spacing: 3px;"
        )
        header_bar.addWidget(title)
        header_bar.addStretch()

        self._lbl_last_update = QLabel("LAST UPDATE: --")
        self._lbl_last_update.setStyleSheet(f"color: {theme.DIM}; font-size: 10px;")
        header_bar.addWidget(self._lbl_last_update)

        self._btn_refresh = QPushButton("⟳ REFRESH NOW")
        self._btn_refresh.setFixedWidth(130)
        self._btn_refresh.clicked.connect(self._on_refresh_now)
        header_bar.addWidget(self._btn_refresh)

        self._btn_pause = QPushButton("⏸ PAUSE")
        self._btn_pause.setFixedWidth(90)
        self._btn_pause.setCheckable(True)
        self._btn_pause.toggled.connect(self._on_pause_toggled)
        header_bar.addWidget(self._btn_pause)

        root_layout.addLayout(header_bar)

        # ── Main content: source panel | map | feed ──
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._source_panel = SourcePanel()
        self._source_panel.layer_toggled.connect(self._on_layer_toggled)
        splitter.addWidget(self._source_panel)

        self._map = MapWidget()
        splitter.addWidget(self._map)

        self._feed_panel = FeedPanel()
        splitter.addWidget(self._feed_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([200, 900, 280])

        root_layout.addWidget(splitter, stretch=1)

        # ── Status bar ──
        self._status = QStatusBar()
        self.setStatusBar(self._status)

        self._lbl_status      = QLabel("STATUS: INITIALISING")
        self._lbl_counts      = QLabel("")
        self._lbl_next        = QLabel("")

        for lbl in (self._lbl_status, self._lbl_counts, self._lbl_next):
            lbl.setStyleSheet(f"color: {theme.GREEN}; font-size: 10px; padding: 0 8px;")
            self._status.addWidget(lbl)

        self._status.addPermanentWidget(QLabel("PALANTIR v1.0 │ open-source feeds"))

    # ── Timer / refresh cycle ───────────────────────────────────

    def _start_refresh_cycle(self) -> None:
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._on_countdown_tick)
        self._countdown_timer.start(1000)

        self._on_refresh_now()  # immediate first fetch

    def _on_countdown_tick(self) -> None:
        if self._paused:
            return
        self._countdown -= 1
        self._lbl_next.setText(f"NEXT REFRESH: {self._countdown}s")
        if self._countdown <= 0:
            self._on_refresh_now()

    def _on_refresh_now(self) -> None:
        self._countdown = _DEFAULT_REFRESH_SECS
        self._lbl_status.setText("STATUS: FETCHING...")
        self._lbl_status.setStyleSheet(f"color: {theme.AMBER}; font-size: 10px; padding: 0 8px;")
        self._btn_refresh.setEnabled(False)
        self._feed_panel.add_message("── REFRESH CYCLE STARTED ──", theme.DIM)
        self._pending_fetches = len(_SOURCE_DEFS)

        for layer_name, display, fn, kwargs in _SOURCE_DEFS:
            self._source_panel.set_fetching(layer_name)
            worker = FetchWorker(layer_name, fn, **kwargs)
            worker.finished.connect(self._on_source_result)
            worker.error.connect(self._on_source_error)
            worker.start()
            self._workers.append(worker)

    # ── Worker callbacks ────────────────────────────────────────

    @pyqtSlot(object)
    def _on_source_result(self, result: SourceResult) -> None:
        layer_name = result.layer.value
        self._all_records[layer_name] = result.records
        self._source_panel.update_source(layer_name, len(result.records), result.ok)
        self._feed_panel.add_records(result.records[:30])  # latest 30 in feed

        if result.errors:
            for err in result.errors:
                self._feed_panel.add_message(f"WARN: {err}", theme.AMBER)

        self._pending_fetches -= 1
        if self._pending_fetches <= 0:
            self._on_all_fetched()

    @pyqtSlot(str, str)
    def _on_source_error(self, source_name: str, error_msg: str) -> None:
        self._source_panel.update_source(source_name, 0, ok=False)
        self._feed_panel.add_message(f"ERR [{source_name}]: {error_msg[:60]}", theme.RED)
        self._pending_fetches -= 1
        if self._pending_fetches <= 0:
            self._on_all_fetched()

    def _on_all_fetched(self) -> None:
        self._lbl_status.setText("STATUS: LIVE")
        self._lbl_status.setStyleSheet(f"color: {theme.GREEN}; font-size: 10px; padding: 0 8px;")
        self._btn_refresh.setEnabled(True)

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        self._lbl_last_update.setText(f"LAST UPDATE: {now_str}")

        # Merge all records into a single GeoJSON FeatureCollection
        all_features: list[dict] = []
        for records in self._all_records.values():
            for rec in records:
                all_features.append(rec.to_geojson_feature())

        geojson: dict[str, Any] = {"type": "FeatureCollection", "features": all_features}
        self._map.update_data(geojson)

        # Write to disk
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = _OUTPUT_DIR / "latest.geojson"
        out_path.write_text(json.dumps(geojson, indent=2), encoding="utf-8")

        # Update count status bar
        counts = {k: len(v) for k, v in self._all_records.items() if v}
        count_str = " │ ".join(f"{k.upper()[:3]}:{v:,}" for k, v in counts.items())
        self._lbl_counts.setText(count_str)

        self._feed_panel.add_message(
            f"── REFRESH COMPLETE — {len(all_features):,} TOTAL RECORDS ──",
            theme.GREEN,
        )

        # Clean up finished workers
        self._workers = [w for w in self._workers if w.isRunning()]

    # ── Controls ────────────────────────────────────────────────

    @pyqtSlot(str, bool)
    def _on_layer_toggled(self, layer_name: str, visible: bool) -> None:
        self._map.toggle_layer(layer_name, visible)

    @pyqtSlot(bool)
    def _on_pause_toggled(self, paused: bool) -> None:
        self._paused = paused
        self._btn_pause.setText("▶ RESUME" if paused else "⏸ PAUSE")
        self._feed_panel.add_message(
            "AUTO-REFRESH PAUSED" if paused else "AUTO-REFRESH RESUMED",
            theme.AMBER,
        )

    # ── Cleanup ──────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        self._countdown_timer.stop()
        for w in self._workers:
            w.quit()
            w.wait(1000)
        self._map.cleanup()
        super().closeEvent(event)
