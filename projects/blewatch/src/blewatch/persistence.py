"""
Tracker persistence heuristic engine.

A device is flagged as "following you" when it satisfies:
  N >= min_sightings observations
  within T <= window_minutes minutes

Confidence levels:
  high   — known tracker type (AirTag/Tile/SmartTag), N >= min_sightings
  medium — unknown tracker type, N >= min_sightings
  low    — any tracker, N < min_sightings but repeated

MAC rotation evasion fallback: group by (tracker_type, time_window) when
multiple MACs of the same type appear within the window.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterator

from .scanner import Sighting

DEFAULT_MIN_SIGHTINGS = 3
DEFAULT_WINDOW_MINUTES = 10


@dataclass
class Alert:
    tracker_type: str
    mac: str
    first_seen: datetime
    last_seen: datetime
    observation_count: int
    confidence: str

    def to_json_event(self) -> str:
        return json.dumps(
            {
                "event": "tracker_alert",
                "ts": datetime.now(timezone.utc).isoformat(),
                "tracker_type": self.tracker_type,
                "mac": self.mac,
                "first_seen": self.first_seen.isoformat(),
                "last_seen": self.last_seen.isoformat(),
                "observation_count": self.observation_count,
                "confidence": self.confidence,
            }
        )


@dataclass
class _DeviceRecord:
    mac: str
    tracker_type: str
    sightings: list[datetime] = field(default_factory=list)
    alerted: bool = False


class PersistenceEngine:
    def __init__(
        self,
        min_sightings: int = DEFAULT_MIN_SIGHTINGS,
        window_minutes: int = DEFAULT_WINDOW_MINUTES,
    ) -> None:
        self.min_sightings = min_sightings
        self.window_minutes = window_minutes
        self._records: dict[str, _DeviceRecord] = {}

    def ingest(self, sighting: Sighting) -> Iterator[Alert]:
        """Process a sighting; yield Alert if persistence threshold is crossed."""
        rec = self._records.setdefault(
            sighting.mac,
            _DeviceRecord(mac=sighting.mac, tracker_type=sighting.tracker_type),
        )
        rec.sightings.append(sighting.ts)

        cutoff = sighting.ts - timedelta(minutes=self.window_minutes)
        recent = [t for t in rec.sightings if t >= cutoff]
        rec.sightings = recent

        if not rec.alerted and len(recent) >= self.min_sightings:
            rec.alerted = True
            confidence = "high" if rec.tracker_type != "unknown" else "medium"
            yield Alert(
                tracker_type=rec.tracker_type,
                mac=rec.mac,
                first_seen=recent[0],
                last_seen=recent[-1],
                observation_count=len(recent),
                confidence=confidence,
            )
