"""Unit tests for BLE advertisement classifier — no hardware required."""
from unittest.mock import MagicMock

import pytest

from blewatch.scanner import classify_advertisement


def _make_adv(company_id=None, service_uuids=None, tx_power=-60, rssi=-70, mfr_payload=b"\x01" * 8):
    adv = MagicMock()
    adv.manufacturer_data = {company_id: mfr_payload} if company_id is not None else {}
    adv.service_uuids = list(service_uuids) if service_uuids else []
    adv.tx_power = tx_power
    adv.rssi = rssi
    return adv


def _make_device(address="AA:BB:CC:DD:EE:FF"):
    d = MagicMock()
    d.address = address
    return d


def test_airtag_detected():
    adv = _make_adv(
        company_id=0x004C,
        service_uuids=["0000fd6f-0000-1000-8000-00805f9b34fb"],
    )
    assert classify_advertisement(_make_device(), adv) == "AirTag"


def test_tile_detected():
    adv = _make_adv(
        company_id=0x000D,
        service_uuids=["0000feed-0000-1000-8000-00805f9b34fb"],
    )
    assert classify_advertisement(_make_device(), adv) == "Tile"


def test_smarttag_detected():
    adv = _make_adv(
        company_id=0x0075,
        service_uuids=["0000fd5a-0000-1000-8000-00805f9b34fb"],
    )
    assert classify_advertisement(_make_device(), adv) == "SmartTag"


def test_audio_device_ignored():
    # Tile headphones: audio UUID present → should NOT be flagged as Tile tracker
    adv = _make_adv(
        company_id=0x000D,
        service_uuids=["0000110b-0000-1000-8000-00805f9b34fb"],  # A2DP Sink
    )
    assert classify_advertisement(_make_device(), adv) is None


def test_unknown_tracker_detected():
    adv = _make_adv(
        company_id=0x9999,
        service_uuids=["0000abcd-0000-1000-8000-00805f9b34fb"],
        mfr_payload=b"\x02\x03\x04",  # short payload < 32 bytes
    )
    result = classify_advertisement(_make_device(), adv)
    assert result == "unknown"


def test_no_match_returns_none():
    adv = _make_adv()
    adv.service_uuids = []
    adv.manufacturer_data = {}
    adv.tx_power = None
    assert classify_advertisement(_make_device(), adv) is None
