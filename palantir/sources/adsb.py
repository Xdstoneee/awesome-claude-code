"""
ADS-B aircraft transponder data via the OpenSky Network REST API.

• Free, no auth for basic access (100 API credits/day)
• Free account at opensky-network.org → 4,000 credits/day
• Set OPENSKY_USERNAME + OPENSKY_PASSWORD for higher limits

Docs: https://openskynetwork.github.io/opensky-api/rest.html
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

import requests

from palantir.models import GeoRecord, Layer, SourceResult

_API   = "https://opensky-network.org/api/states/all"
_TIMEOUT = 30

# OpenSky state-vector field indices
_ICAO24, _CALLSIGN, _ORIGIN = 0, 1, 2
_TIME_POS, _LAST_CONTACT    = 3, 4
_LON, _LAT, _BARO_ALT       = 5, 6, 7
_ON_GROUND, _VELOCITY       = 8, 9
_HEADING, _VERT_RATE        = 10, 11
_SQUAWK, _CATEGORY          = 14, 17


def fetch(bbox: tuple[float, float, float, float] | None = None) -> SourceResult:
    """
    Pull live aircraft state vectors from OpenSky Network.
    bbox = (lat_min, lon_min, lat_max, lon_max) to restrict area.
    """
    fetched_at = datetime.now(timezone.utc)
    user = os.getenv("OPENSKY_USERNAME")
    pw   = os.getenv("OPENSKY_PASSWORD")
    auth = (user, pw) if user and pw else None

    params: dict[str, object] = {}
    if bbox:
        lat_min, lon_min, lat_max, lon_max = bbox
        params = {"lamin": lat_min, "lomin": lon_min, "lamax": lat_max, "lomax": lon_max}

    try:
        resp = requests.get(_API, params=params, auth=auth, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        msg = f"OpenSky: {e}"
        print(f"  ✗ {msg}", file=sys.stderr)
        return SourceResult(layer=Layer.AIRCRAFT, source_name="opensky",
                            fetched_at=fetched_at, records=[], errors=[msg])

    base_time = data.get("time", fetched_at.timestamp())
    records: list[GeoRecord] = []

    for sv in (data.get("states") or []):
        lat, lon = sv[_LAT], sv[_LON]
        if lat is None or lon is None:
            continue
        icao24   = sv[_ICAO24] or ""
        callsign = (sv[_CALLSIGN] or "").strip() or icao24
        ts       = sv[_TIME_POS] or base_time
        records.append(GeoRecord(
            layer=Layer.AIRCRAFT, source_name="opensky",
            observed_at=datetime.fromtimestamp(ts, tz=timezone.utc),
            uid=icao24, label=callsign,
            lat=lat, lon=lon,
            altitude_m=sv[_BARO_ALT],
            speed_ms=sv[_VELOCITY],
            heading_deg=sv[_HEADING],
            extras={
                "origin_country": sv[_ORIGIN] or "",
                "on_ground":      bool(sv[_ON_GROUND]),
                "vertical_rate":  sv[_VERT_RATE],
                "squawk":         sv[_SQUAWK] or "",
            },
        ))

    return SourceResult(layer=Layer.AIRCRAFT, source_name="opensky",
                        fetched_at=fetched_at, records=records)
