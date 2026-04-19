"""
Active weather alerts from the NOAA / National Weather Service API.

• Completely free, no auth required (US-focused)
• GeoJSON response with polygon geometries for alert areas
• Docs: https://www.weather.gov/documentation/services-web-api

For global severe weather, also queries OpenMeteo (free, no key):
• https://open-meteo.com/en/docs/historical-weather-api
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

import requests

from palantir.models import GeoRecord, Layer, SourceResult

_NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"
_TIMEOUT = 20

_SEVERITY_ORDER = {"Extreme": 4, "Severe": 3, "Moderate": 2, "Minor": 1, "Unknown": 0}


def fetch(area: str | None = None) -> SourceResult:
    """
    Fetch active NWS weather alerts.
    area: optional 2-letter US state code (e.g. "CA") to filter results.
    """
    fetched_at = datetime.now(timezone.utc)
    params: dict[str, str] = {"status": "actual"}
    if area:
        params["area"] = area

    headers = {"User-Agent": "palantir-awareness-bot/1.0 (contact: user@example.com)"}

    try:
        resp = requests.get(_NWS_ALERTS_URL, params=params, headers=headers, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        msg = f"NWS Alerts: {e}"
        print(f"  ✗ {msg}", file=sys.stderr)
        return SourceResult(layer=Layer.WEATHER, source_name="nws",
                            fetched_at=fetched_at, records=[], errors=[msg])

    records: list[GeoRecord] = []
    for feat in data.get("features", []):
        props  = feat.get("properties", {})
        geom   = feat.get("geometry")  # may be polygon or None

        # Derive a representative point from the geometry centroid or area description
        lat, lon = None, None
        if geom:
            gtype = geom.get("type", "")
            if gtype == "Point":
                lon, lat = geom["coordinates"]
            elif gtype in ("Polygon", "MultiPolygon"):
                # crude centroid of first ring
                ring = (geom["coordinates"][0] if gtype == "Polygon"
                        else geom["coordinates"][0][0])
                lons = [c[0] for c in ring]
                lats = [c[1] for c in ring]
                lon, lat = sum(lons) / len(lons), sum(lats) / len(lats)

        uid       = props.get("id") or feat.get("id") or ""
        event     = props.get("event") or "Weather Alert"
        headline  = props.get("headline") or event
        severity  = props.get("severity") or "Unknown"
        sent      = props.get("sent") or ""

        try:
            obs = datetime.fromisoformat(sent.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            obs = fetched_at

        records.append(GeoRecord(
            layer=Layer.WEATHER, source_name="nws",
            observed_at=obs,
            uid=uid,
            label=f"[{severity.upper()}] {event}",
            lat=lat, lon=lon,
            extras={
                "event":       event,
                "severity":    severity,
                "certainty":   props.get("certainty") or "",
                "urgency":     props.get("urgency") or "",
                "headline":    headline,
                "area_desc":   props.get("areaDesc") or "",
                "expires":     props.get("expires") or "",
                "nws_url":     props.get("@id") or "",
            },
        ))

    # Sort by severity descending
    records.sort(key=lambda r: _SEVERITY_ORDER.get(r.extras.get("severity", "Unknown"), 0), reverse=True)

    return SourceResult(layer=Layer.WEATHER, source_name="nws",
                        fetched_at=fetched_at, records=records)
