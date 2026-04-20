"""
Live satellite positions computed from Celestrak TLE data.

• Completely free, no auth required
• TLEs updated several times per day
• Propagation via sgp4 library (pip install sgp4)
• Docs: https://celestrak.org/

Without sgp4 installed, falls back to returning raw TLE metadata only.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

import requests

from palantir.models import GeoRecord, Layer, SourceResult

_TIMEOUT = 30

# Celestrak TLE catalogue groups (JSON format)
_CATALOGUES: dict[str, str] = {
    "stations":   "https://celestrak.org/SOCRATES/query.php?catalog=stations&FORMAT=JSON",
    "visual":     "https://celestrak.org/SOCRATES/query.php?catalog=visual&FORMAT=JSON",
    "active":     "https://celestrak.org/SOCRATES/query.php?catalog=active&FORMAT=JSON",
}

# Simpler TLE text endpoints — one TLE set per 3 lines
_TLE_URLS: dict[str, str] = {
    "stations": "https://celestrak.org/SOCRATES/query.php?catalog=stations&FORMAT=TLE",
    "visual":   "https://celestrak.org/SOCRATES/query.php?catalog=visual&FORMAT=TLE",
}

_CELESTRAK_JSON = "https://celestrak.org/SOCRATES/query.php?catalog={group}&FORMAT=JSON"
_CELESTRAK_TLE  = "https://celestrak.org/pub/TLE/{group}.txt"

# Well-maintained small catalogue lists
_GROUPS = {
    "stations": "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=TLE",
    "visual":   "https://celestrak.org/NORAD/elements/gp.php?GROUP=visual&FORMAT=TLE",
    "weather":  "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=TLE",
}


def _parse_tle_text(text: str) -> list[tuple[str, str, str]]:
    """Parse a TLE text block into (name, line1, line2) tuples."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    tles: list[tuple[str, str, str]] = []
    i = 0
    while i + 2 < len(lines):
        name  = lines[i]
        line1 = lines[i + 1]
        line2 = lines[i + 2]
        if line1.startswith("1 ") and line2.startswith("2 "):
            tles.append((name, line1, line2))
            i += 3
        else:
            i += 1
    return tles


def _propagate(name: str, line1: str, line2: str, when: datetime) -> tuple[float, float, float] | None:
    """Return (lat, lon, alt_km) for a TLE at the given UTC time, or None."""
    try:
        from sgp4.api import Satrec, jday  # type: ignore[import]
        sat = Satrec.twoline2rv(line1, line2)
        jd, fr = jday(when.year, when.month, when.day,
                      when.hour, when.minute, when.second + when.microsecond / 1e6)
        e, r, _ = sat.sgp4(jd, fr)
        if e != 0 or not r:
            return None
        from math import atan2, sqrt, degrees, pi
        x, y, z = r
        lon = degrees(atan2(y, x))
        hyp = sqrt(x * x + y * y)
        lat = degrees(atan2(z, hyp))
        alt_km = sqrt(x * x + y * y + z * z) - 6371.0
        return lat, lon, alt_km
    except ImportError:
        return None
    except Exception:
        return None


def fetch(groups: list[str] | None = None) -> SourceResult:
    """Fetch and propagate satellite positions from Celestrak TLEs."""
    fetched_at = datetime.now(timezone.utc)
    selected = groups or list(_GROUPS.keys())
    records: list[GeoRecord] = []
    has_sgp4 = False

    try:
        import sgp4  # noqa: F401
        has_sgp4 = True
    except ImportError:
        print("  ! Satellites: sgp4 not installed — showing TLE metadata only "
              "(pip install sgp4)", file=sys.stderr)

    for group in selected:
        url = _GROUPS.get(group)
        if not url:
            continue
        try:
            resp = requests.get(url, timeout=_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  ✗ Celestrak ({group}): {e}", file=sys.stderr)
            continue

        tles = _parse_tle_text(resp.text)
        for name, l1, l2 in tles:
            norad_id = l1[2:7].strip()
            uid = f"NORAD-{norad_id}"

            lat, lon, alt_km = None, None, None
            if has_sgp4:
                result = _propagate(name, l1, l2, fetched_at)
                if result:
                    lat, lon, alt_km = result

            records.append(GeoRecord(
                layer=Layer.SATELLITE, source_name="celestrak",
                observed_at=fetched_at,
                uid=uid, label=name.strip(),
                lat=lat, lon=lon,
                altitude_m=alt_km * 1000 if alt_km is not None else None,
                extras={
                    "norad_id":    norad_id,
                    "group":       group,
                    "epoch_line1": l1[18:32].strip(),
                    "has_position": lat is not None,
                },
            ))

    return SourceResult(layer=Layer.SATELLITE, source_name="celestrak",
                        fetched_at=fetched_at, records=records)
