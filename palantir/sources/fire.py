"""
Active fire / hotspot detections from NASA FIRMS (Fire Information for
Resource Management System).

• Free with a NASA Earthdata account → MAP_KEY
• Register at: https://www.earthdata.nasa.gov/
• Then visit: https://firms.modaps.eosdis.nasa.gov/api/map_key/
• Set FIRMS_MAP_KEY environment variable

Instruments: VIIRS (375m resolution) from Suomi-NPP and NOAA-20,
             MODIS (1km) from Aqua/Terra.

Docs: https://firms.modaps.eosdis.nasa.gov/api/area/
"""

from __future__ import annotations

import csv
import io
import os
import sys
from datetime import datetime, timezone

import requests

from palantir.models import GeoRecord, Layer, SourceResult

_BASE  = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
_TIMEOUT = 30

# FIRMS instrument sources (higher resolution first)
_SOURCES = [
    ("VIIRS_SNPP_NRT",  "VIIRS/SNPP"),
    ("VIIRS_NOAA20_NRT","VIIRS/NOAA-20"),
    ("MODIS_NRT",       "MODIS"),
]


def fetch(
    world_bbox: str = "-180,-90,180,90",
    day_range: int = 1,
) -> SourceResult:
    """
    Fetch active fire detections for the last `day_range` days.

    world_bbox: "lon_min,lat_min,lon_max,lat_max"
    """
    fetched_at = datetime.now(timezone.utc)
    map_key = os.getenv("FIRMS_MAP_KEY", "")

    if not map_key:
        print("  ! NASA FIRMS: FIRMS_MAP_KEY not set — skipping "
              "(free key at firms.modaps.eosdis.nasa.gov/api/map_key/)", file=sys.stderr)
        return SourceResult(layer=Layer.FIRE, source_name="firms",
                            fetched_at=fetched_at, records=[],
                            errors=["FIRMS_MAP_KEY not set"])

    records: list[GeoRecord] = []

    for src_code, src_label in _SOURCES:
        url = f"{_BASE}/{map_key}/{src_code}/{world_bbox}/{day_range}"
        try:
            resp = requests.get(url, timeout=_TIMEOUT)
            if resp.status_code == 400:
                continue  # source not available
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  ✗ FIRMS ({src_label}): {e}", file=sys.stderr)
            continue

        reader = csv.DictReader(io.StringIO(resp.text))
        for row in reader:
            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
            except (KeyError, ValueError):
                continue

            acq_date = row.get("acq_date", "")
            acq_time = row.get("acq_time", "0000").zfill(4)
            try:
                obs = datetime.strptime(f"{acq_date} {acq_time}", "%Y-%m-%d %H%M").replace(tzinfo=timezone.utc)
            except ValueError:
                obs = fetched_at

            frp  = row.get("frp", "0")     # Fire Radiative Power (MW)
            conf = row.get("confidence", "")
            uid  = f"{src_code}_{lat:.4f}_{lon:.4f}_{acq_date}_{acq_time}"

            records.append(GeoRecord(
                layer=Layer.FIRE, source_name="firms",
                observed_at=obs,
                uid=uid,
                label=f"🔥 {src_label} FRP={frp}MW",
                lat=lat, lon=lon,
                extras={
                    "instrument":  src_label,
                    "frp_mw":      frp,
                    "confidence":  conf,
                    "bright_t31":  row.get("bright_t31") or row.get("brightness", ""),
                    "satellite":   row.get("satellite", ""),
                    "daynight":    row.get("daynight", ""),
                },
            ))

        # Limit per instrument to avoid overwhelming the map
        if len(records) > 5000:
            break

    return SourceResult(layer=Layer.FIRE, source_name="firms",
                        fetched_at=fetched_at, records=records)
