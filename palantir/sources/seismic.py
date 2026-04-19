"""
Real-time seismic data from the USGS Earthquake Hazards Program.

• Completely free, no auth required
• GeoJSON feed updated every minute
• Docs: https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

import requests

from palantir.models import GeoRecord, Layer, SourceResult

# Feed options by recency + magnitude
_FEEDS = {
    "all_hour":      "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson",
    "all_day":       "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
    "significant_week": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson",
}
_TIMEOUT = 20


def fetch(feed: str = "all_day") -> SourceResult:
    """Fetch earthquake events. feed = 'all_hour' | 'all_day' | 'significant_week'."""
    fetched_at = datetime.now(timezone.utc)
    url = _FEEDS.get(feed, _FEEDS["all_day"])

    try:
        resp = requests.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        msg = f"USGS: {e}"
        print(f"  ✗ {msg}", file=sys.stderr)
        return SourceResult(layer=Layer.SEISMIC, source_name="usgs",
                            fetched_at=fetched_at, records=[], errors=[msg])

    records: list[GeoRecord] = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        geom  = feat.get("geometry", {})
        coords = geom.get("coordinates", [None, None, None])
        lon, lat, depth_km = coords[0], coords[1], coords[2]
        if lat is None or lon is None:
            continue

        mag   = props.get("mag") or 0.0
        place = props.get("place") or "Unknown"
        ts_ms = props.get("time") or 0
        uid   = feat.get("id") or f"{lat},{lon}"

        records.append(GeoRecord(
            layer=Layer.SEISMIC, source_name="usgs",
            observed_at=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
            uid=uid,
            label=f"M{mag:.1f} — {place}",
            lat=lat, lon=lon,
            extras={
                "magnitude":  mag,
                "depth_km":   depth_km,
                "place":      place,
                "type":       props.get("type", "earthquake"),
                "alert":      props.get("alert") or "none",
                "tsunami":    bool(props.get("tsunami")),
                "usgs_url":   props.get("url") or "",
                "felt":       props.get("felt") or 0,
            },
        ))

    return SourceResult(layer=Layer.SEISMIC, source_name="usgs",
                        fetched_at=fetched_at, records=records)
