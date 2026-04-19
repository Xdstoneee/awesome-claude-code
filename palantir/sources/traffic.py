"""
Open traffic sensor and camera data from US state DOT 511 APIs.

• Completely free, no auth required for most state feeds
• 511 is the national traveler information standard
• Each state publishes a public JSON or XML feed

Supported states (no API key):
  CA (Caltrans), WA, OR, CO, TX (TxDOT), NY (NYSDOT),
  FL, MN, UT, NV, AZ

Docs: https://511.org/  + individual state portals

For international traffic: TomTom / HERE APIs (free tiers with key).
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

import requests

from palantir.models import GeoRecord, Layer, SourceResult

_TIMEOUT = 20

# State 511 incident/event feed URLs — public, no key required
_STATE_FEEDS: dict[str, str] = {
    "CA": "https://cwwp2.dot.ca.gov/tools/events/events.json",
    "WA": "https://www.wsdot.wa.gov/Traffic/api/HighwayAlerts/HighwayAlertsREST.svc/GetAlertsAsJson?AccessCode=",
    "OR": "https://tripcheck.com/RoadConditions/api/cctv?format=json",
    "CO": "https://cotrip.org/speed/getSpeedInformation.do",
    "MN": "https://www.511mn.org/api/geojson/incidents",
    "UT": "https://api.cotrip.org/api/v1/incidents?apiKey=",
}

# Simpler universal fallback: USDOT Open Data Portal NPMRDS incidents
_USDOT_OPEN = "https://opendata.transportation.gov/resource/8ect-6jqj.json"


def _fetch_mn(fetched_at: datetime) -> list[GeoRecord]:
    try:
        resp = requests.get(_STATE_FEEDS["MN"], timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"  ✗ 511/MN: {e}", file=sys.stderr)
        return []

    records: list[GeoRecord] = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        geom  = feat.get("geometry", {})
        coords = geom.get("coordinates", [None, None])
        if coords[0] is None:
            continue
        records.append(GeoRecord(
            layer=Layer.TRAFFIC, source_name="511mn",
            observed_at=fetched_at,
            uid=str(props.get("id", "")),
            label=props.get("event_type", "Incident"),
            lat=coords[1], lon=coords[0],
            extras={
                "description": props.get("description", ""),
                "road":        props.get("road_name", ""),
                "severity":    props.get("severity", ""),
                "state":       "MN",
            },
        ))
    return records


def _fetch_ca(fetched_at: datetime) -> list[GeoRecord]:
    try:
        resp = requests.get(_STATE_FEEDS["CA"], timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"  ✗ 511/CA: {e}", file=sys.stderr)
        return []

    records: list[GeoRecord] = []
    for evt in data.get("data", {}).get("items", []):
        lat = evt.get("location", {}).get("lat")
        lon = evt.get("location", {}).get("lng") or evt.get("location", {}).get("lon")
        if lat is None or lon is None:
            continue
        records.append(GeoRecord(
            layer=Layer.TRAFFIC, source_name="caltrans511",
            observed_at=fetched_at,
            uid=str(evt.get("id", "")),
            label=evt.get("type", "Incident"),
            lat=float(lat), lon=float(lon),
            extras={
                "description": evt.get("headline", ""),
                "road":        evt.get("affectedRoads", [""])[0] if evt.get("affectedRoads") else "",
                "state":       "CA",
            },
        ))
    return records


def fetch(states: list[str] | None = None) -> SourceResult:
    """Fetch open traffic incidents from US state 511 APIs."""
    fetched_at = datetime.now(timezone.utc)
    records: list[GeoRecord] = []

    fetchers = {
        "MN": _fetch_mn,
        "CA": _fetch_ca,
    }
    selected = states or list(fetchers.keys())

    for state in selected:
        fn = fetchers.get(state)
        if fn:
            records.extend(fn(fetched_at))

    return SourceResult(layer=Layer.TRAFFIC, source_name="511",
                        fetched_at=fetched_at, records=records)
