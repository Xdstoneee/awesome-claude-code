"""
Interactive Leaflet.js map embedded in a QWebEngineView.
Python pushes GeoJSON updates via runJavaScript().
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView


class MapWidget(QWebEngineView):
    """Dark Leaflet map that receives GeoJSON feature collections from Python."""

    _MAP_HTML = Path(__file__).parent / "map.html"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self._tmp_html: Path | None = None
        self._loaded = False
        self._pending_geojson: dict[str, Any] | None = None

        self.loadFinished.connect(self._on_loaded)
        self._load_map()

    # ── Internal ────────────────────────────────────────────────

    def _load_map(self) -> None:
        html_src = self._MAP_HTML.read_text(encoding="utf-8")
        # Write to a temp file so the page has a proper file:// base URL
        # (needed for Leaflet CDN scripts to load correctly in WebEngine)
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False,
            encoding="utf-8", prefix="palantir_map_",
        )
        tmp.write(html_src)
        tmp.flush()
        self._tmp_html = Path(tmp.name)
        tmp.close()
        self.load(QUrl.fromLocalFile(str(self._tmp_html)))

    def _on_loaded(self, ok: bool) -> None:
        # Mark loaded regardless of ok — WebEngine fires ok=False when any
        # sub-resource (CDN script, favicon) fails even if the page itself ran.
        self._loaded = True
        if self._pending_geojson is not None:
            # Small delay lets the JS engine finish initialising after load
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, lambda: self._push_pending())

    def _push_pending(self) -> None:
        if self._pending_geojson is not None:
            self._push(self._pending_geojson)
            self._pending_geojson = None

    def _push(self, geojson: dict[str, Any]) -> None:
        js_payload = json.dumps(geojson, allow_nan=False)
        self.page().runJavaScript(f"updateMarkers({js_payload}); flashHUD();")

    # ── Public API ──────────────────────────────────────────────

    def update_data(self, geojson: dict[str, Any]) -> None:
        """Push a new GeoJSON FeatureCollection to the map."""
        if self._loaded:
            self._push(geojson)
        else:
            self._pending_geojson = geojson

    def toggle_layer(self, layer_name: str, visible: bool) -> None:
        """Show or hide a named layer."""
        self.page().runJavaScript(
            f"toggleLayer({json.dumps(layer_name)}, {json.dumps(visible)});"
        )

    def cleanup(self) -> None:
        """Delete the temp HTML file on exit."""
        if self._tmp_html and self._tmp_html.exists():
            self._tmp_html.unlink(missing_ok=True)
