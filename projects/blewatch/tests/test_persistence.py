"""Unit tests for persistence heuristic engine."""
from datetime import datetime, timedelta, timezone

import pytest

from blewatch.persistence import PersistenceEngine
from blewatch.scanner import Sighting


def _sighting(mac="AA:BB:CC:DD:EE:FF", tracker_type="AirTag", minutes_ago=0):
    return Sighting(
        ts=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
        mac=mac,
        rssi=-70,
        tracker_type=tracker_type,
        raw_adv_hex="deadbeef",
    )


def test_alert_fires_at_threshold():
    engine = PersistenceEngine(min_sightings=3, window_minutes=10)
    alerts = []
    for i in range(3):
        alerts.extend(engine.ingest(_sighting(minutes_ago=9 - i)))
    assert len(alerts) == 1
    assert alerts[0].tracker_type == "AirTag"
    assert alerts[0].confidence == "high"


def test_alert_not_duplicate():
    engine = PersistenceEngine(min_sightings=3, window_minutes=10)
    alerts = []
    for _ in range(5):
        alerts.extend(engine.ingest(_sighting()))
    assert len(alerts) == 1


def test_sightings_outside_window_ignored():
    engine = PersistenceEngine(min_sightings=3, window_minutes=10)
    alerts = []
    alerts.extend(engine.ingest(_sighting(minutes_ago=30)))
    alerts.extend(engine.ingest(_sighting(minutes_ago=25)))
    alerts.extend(engine.ingest(_sighting(minutes_ago=0)))
    # Only 1 sighting in window — should not alert
    assert len(alerts) == 0


def test_unknown_tracker_medium_confidence():
    engine = PersistenceEngine(min_sightings=3, window_minutes=10)
    alerts = []
    for _ in range(3):
        alerts.extend(engine.ingest(_sighting(tracker_type="unknown")))
    assert alerts[0].confidence == "medium"


def test_different_macs_independent():
    engine = PersistenceEngine(min_sightings=3, window_minutes=10)
    alerts = []
    for _ in range(3):
        alerts.extend(engine.ingest(_sighting(mac="AA:BB:CC:DD:EE:01")))
        alerts.extend(engine.ingest(_sighting(mac="AA:BB:CC:DD:EE:02")))
    assert len(alerts) == 2
