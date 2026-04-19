"""
AIS maritime vessel position reports via aisstream.io WebSocket feed.

• Free API key at https://aisstream.io  (generous free tier)
• Set AISSTREAM_API_KEY environment variable
• Without a key this source is gracefully skipped

Protocol: WSS JSON stream — we subscribe, collect for ~10 s, then return.
Docs: https://aisstream.io/documentation
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from datetime import datetime, timezone

from palantir.models import GeoRecord, Layer, SourceResult

_WS_URL  = "wss://stream.aisstream.io/v0/stream"
_COLLECT_SECONDS = 10   # listen for this many seconds per poll cycle


def fetch() -> SourceResult:
    """Subscribe to the global AIS stream and collect positions for 10 s."""
    fetched_at = datetime.now(timezone.utc)
    api_key = os.getenv("AISSTREAM_API_KEY", "")

    if not api_key:
        print("  ! AIS: AISSTREAM_API_KEY not set — skipping "
              "(free key at aisstream.io)", file=sys.stderr)
        return SourceResult(layer=Layer.MARITIME, source_name="aisstream",
                            fetched_at=fetched_at, records=[],
                            errors=["AISSTREAM_API_KEY not set"])

    try:
        import websocket  # websocket-client package
    except ImportError:
        msg = "AIS: install websocket-client  (pip install websocket-client)"
        print(f"  ! {msg}", file=sys.stderr)
        return SourceResult(layer=Layer.MARITIME, source_name="aisstream",
                            fetched_at=fetched_at, records=[], errors=[msg])

    raw_vessels: dict[str, dict] = {}  # mmsi → latest message
    stop_event = threading.Event()

    def on_open(ws):
        ws.send(json.dumps({
            "APIKey": api_key,
            "BoundingBoxes": [[[-90, -180], [90, 180]]],
            "FilterMessageTypes": ["PositionReport", "StandardClassBPositionReport"],
        }))

    def on_message(ws, msg):
        try:
            data = json.loads(msg)
            meta = data.get("MetaData", {})
            mmsi = str(meta.get("MMSI", ""))
            lat  = meta.get("latitude")
            lon  = meta.get("longitude")
            if mmsi and lat is not None and lon is not None:
                raw_vessels[mmsi] = {
                    "mmsi":      mmsi,
                    "name":      meta.get("ShipName", "").strip() or mmsi,
                    "lat":       lat,
                    "lon":       lon,
                    "speed_kn":  data.get("Message", {})
                                     .get("PositionReport", {})
                                     .get("Sog", 0),
                    "heading":   data.get("Message", {})
                                     .get("PositionReport", {})
                                     .get("TrueHeading"),
                    "time_utc":  meta.get("time_utc", ""),
                }
        except (json.JSONDecodeError, KeyError):
            pass
        if stop_event.is_set():
            ws.close()

    def on_error(ws, error):
        print(f"  ✗ AIS WebSocket: {error}", file=sys.stderr)

    ws = websocket.WebSocketApp(_WS_URL,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error)
    t = threading.Thread(target=ws.run_forever, daemon=True)
    t.start()
    time.sleep(_COLLECT_SECONDS)
    stop_event.set()
    ws.close()
    t.join(timeout=3)

    records: list[GeoRecord] = []
    for v in raw_vessels.values():
        speed_kn = v.get("speed_kn") or 0
        records.append(GeoRecord(
            layer=Layer.MARITIME, source_name="aisstream",
            observed_at=fetched_at,
            uid=v["mmsi"], label=v["name"],
            lat=v["lat"], lon=v["lon"],
            speed_ms=speed_kn * 0.5144,
            heading_deg=v.get("heading"),
            extras={"mmsi": v["mmsi"], "speed_knots": speed_kn, "time_utc": v.get("time_utc", "")},
        ))

    return SourceResult(layer=Layer.MARITIME, source_name="aisstream",
                        fetched_at=fetched_at, records=records)
