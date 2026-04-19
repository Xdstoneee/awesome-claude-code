"""
GDELT Project — Global Database of Events, Language, and Tone.

Monitors the world's broadcast, print, and web news media to identify
events, people, locations, organisations, themes, and emotions.

• Completely free, no auth required
• Updated every 15 minutes
• Docs: https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/

We query the GKG (Global Knowledge Graph) and Events API via BigQuery-compatible
CSV exports for recent events with geographic coordinates.
"""

from __future__ import annotations

import csv
import io
import sys
from datetime import datetime, timezone

import requests

from palantir.models import GeoRecord, Layer, SourceResult

# GDELT GKG 15-minute rolling update file list
_LASTUPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
_EVENTS_LASTUPDATE = "http://data.gdeltproject.org/events/lastupdate.txt"
_TIMEOUT = 30

# CAMEO action codes for filtering by event type
_ACTION_LABELS: dict[str, str] = {
    "14": "PROTEST",  "15": "EXHIBIT FORCE",
    "18": "ASSAULT",  "19": "FIGHT",
    "20": "MASS VIOLENCE", "13": "THREATEN",
}


def _latest_events_csv_url() -> str | None:
    try:
        resp = requests.get(_EVENTS_LASTUPDATE, timeout=_TIMEOUT)
        resp.raise_for_status()
        for line in resp.text.splitlines():
            parts = line.strip().split()
            if len(parts) >= 3 and parts[2].endswith(".export.CSV.zip"):
                return parts[2]
    except requests.RequestException:
        pass
    return None


def fetch(max_records: int = 500) -> SourceResult:
    """Fetch the latest GDELT event batch and return geolocated events."""
    fetched_at = datetime.now(timezone.utc)

    # Try the streaming zip export first
    url = _latest_events_csv_url()
    if not url:
        msg = "GDELT: could not determine latest export URL"
        print(f"  ✗ {msg}", file=sys.stderr)
        return SourceResult(layer=Layer.EVENTS, source_name="gdelt",
                            fetched_at=fetched_at, records=[], errors=[msg])

    try:
        import zipfile

        resp = requests.get(url, timeout=_TIMEOUT, stream=True)
        resp.raise_for_status()

        content = b""
        for chunk in resp.iter_content(chunk_size=65536):
            content += chunk
            if len(content) > 20 * 1024 * 1024:  # 20 MB cap
                break

        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            csv_name = zf.namelist()[0]
            csv_bytes = zf.read(csv_name)

    except Exception as e:
        msg = f"GDELT download/unzip: {e}"
        print(f"  ✗ {msg}", file=sys.stderr)
        return SourceResult(layer=Layer.EVENTS, source_name="gdelt",
                            fetched_at=fetched_at, records=[], errors=[msg])

    # GDELT 1.0 event CSV columns (tab-separated, no header)
    # Col 53 = ActionGeo_Lat, 54 = ActionGeo_Long, 1 = GlobalEventID,
    # 26-27 = EventCode/RootCode, 33 = GoldsteinScale, 57 = SOURCEURL
    records: list[GeoRecord] = []
    reader = csv.reader(io.StringIO(csv_bytes.decode("utf-8", errors="ignore")), delimiter="\t")

    for i, row in enumerate(reader):
        if i >= max_records:
            break
        if len(row) < 58:
            continue
        try:
            lat = float(row[53]) if row[53] else None
            lon = float(row[54]) if row[54] else None
        except ValueError:
            continue
        if lat is None or lon is None or (lat == 0 and lon == 0):
            continue

        event_id  = row[0]
        date_str  = row[1]        # YYYYMMDD
        root_code = row[27] or row[26] or "?"
        goldstein = row[33] or "0"
        source_url = row[57] if len(row) > 57 else ""
        action_label = _ACTION_LABELS.get(root_code[:2], f"EVENT-{root_code}")

        try:
            obs = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
        except ValueError:
            obs = fetched_at

        records.append(GeoRecord(
            layer=Layer.EVENTS, source_name="gdelt",
            observed_at=obs,
            uid=event_id,
            label=action_label,
            lat=lat, lon=lon,
            extras={
                "event_code":    root_code,
                "goldstein":     goldstein,
                "actor1":        row[6] if len(row) > 6 else "",
                "actor2":        row[16] if len(row) > 16 else "",
                "action_geo":    row[51] if len(row) > 51 else "",
                "source_url":    source_url,
            },
        ))

    return SourceResult(layer=Layer.EVENTS, source_name="gdelt",
                        fetched_at=fetched_at, records=records)
