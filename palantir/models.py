"""
Shared data models. Every geographic record serializes to a GeoJSON Feature
so the unified output loads directly into QGIS, Kepler.gl, Mapbox, or the
embedded Leaflet map.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Layer(str, Enum):
    AIRCRAFT  = "aircraft"   # ADS-B transponder broadcasts
    MARITIME  = "maritime"   # AIS vessel position reports
    SEISMIC   = "seismic"    # USGS earthquake events
    WEATHER   = "weather"    # NOAA/NWS active alerts
    FIRE      = "fire"       # NASA FIRMS satellite fire detections
    SATELLITE = "satellite"  # Celestrak orbital objects (TLE-propagated)
    EVENTS    = "events"     # GDELT global news/conflict events
    TRAFFIC   = "traffic"    # Open DOT traffic sensors & cameras


LAYER_COLORS: dict[Layer, str] = {
    Layer.AIRCRAFT:  "#00d4ff",  # cyan
    Layer.MARITIME:  "#00ff41",  # matrix green
    Layer.SEISMIC:   "#ff0040",  # red
    Layer.WEATHER:   "#ffaa00",  # amber
    Layer.FIRE:      "#ff6600",  # orange
    Layer.SATELLITE: "#cc00ff",  # purple
    Layer.EVENTS:    "#ff00cc",  # pink
    Layer.TRAFFIC:   "#ffff00",  # yellow
}


@dataclass
class GeoRecord:
    """
    One observation from any source, normalised to a common schema.
    lon/lat are WGS-84 decimal degrees; None = no point geometry
    (e.g. a weather alert polygon lives in extras["geometry"]).
    """
    layer: Layer
    source_name: str
    observed_at: datetime
    uid: str
    label: str
    lat: float | None
    lon: float | None
    altitude_m: float | None = None
    speed_ms: float | None = None
    heading_deg: float | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_geojson_feature(self) -> dict[str, Any]:
        geometry: dict[str, Any] | None = None
        if self.lat is not None and self.lon is not None:
            geometry = {"type": "Point", "coordinates": [self.lon, self.lat]}

        props: dict[str, Any] = {
            "layer":       self.layer.value,
            "source":      self.source_name,
            "uid":         self.uid,
            "label":       self.label,
            "observed_at": self.observed_at.isoformat(),
        }
        if self.altitude_m  is not None: props["altitude_m"]  = round(self.altitude_m, 1)
        if self.speed_ms    is not None: props["speed_ms"]    = round(self.speed_ms, 2)
        if self.heading_deg is not None: props["heading_deg"] = round(self.heading_deg, 1)
        props.update(self.extras)
        return {"type": "Feature", "geometry": geometry, "properties": props}


@dataclass
class SourceResult:
    layer: Layer
    source_name: str
    fetched_at: datetime
    records: list[GeoRecord]
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.records) or not self.errors

    def to_geojson(self) -> dict[str, Any]:
        return {
            "type": "FeatureCollection",
            "features": [r.to_geojson_feature() for r in self.records],
        }
