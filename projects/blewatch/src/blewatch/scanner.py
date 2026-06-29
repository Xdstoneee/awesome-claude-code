"""
BLE advertisement scanner and tracker type classifier.

Advertisement byte layout reference (for contributor extensions):
  AirTag:     manufacturer_data company_id=0x004C, service_uuid=0xFD6F (Find My network)
  Tile:       manufacturer_data company_id=0x000D, service_uuid=0xFEED
  SmartTag:   manufacturer_data company_id=0x0075, service_uuid=0xFD5A
  Unknown:    persistent device, no audio profile (A2DP/HFP), short payload

Hardware note: Tile *headphones* advertise audio profiles (A2DP/HFP) — NOT service UUID 0xFEED.
A physical Tile Mate/Slim/Sticker is required to validate the Tile detection path.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

TRACKER_SIGNATURES: dict[str, dict[str, Any]] = {
    "AirTag": {
        "company_id": 0x004C,
        "service_uuids": {"0000fd6f-0000-1000-8000-00805f9b34fb"},
    },
    "Tile": {
        "company_id": 0x000D,
        "service_uuids": {"0000feed-0000-1000-8000-00805f9b34fb"},
    },
    "SmartTag": {
        "company_id": 0x0075,
        "service_uuids": {"0000fd5a-0000-1000-8000-00805f9b34fb"},
    },
}

# Audio profiles that indicate headphones/speakers, not trackers
_AUDIO_UUIDS = {
    "0000110b-0000-1000-8000-00805f9b34fb",  # A2DP Sink
    "0000110a-0000-1000-8000-00805f9b34fb",  # A2DP Source
    "0000111e-0000-1000-8000-00805f9b34fb",  # HFP
}


@dataclass
class Sighting:
    ts: datetime
    mac: str
    rssi: int
    tracker_type: str
    raw_adv_hex: str


def classify_advertisement(device: BLEDevice, adv: AdvertisementData) -> str | None:
    """Return tracker type string or None if device is not a known/suspected tracker."""
    uuids = {u.lower() for u in (adv.service_uuids or [])}
    mfr = adv.manufacturer_data or {}

    for tracker_type, sig in TRACKER_SIGNATURES.items():
        if sig["company_id"] in mfr and sig["service_uuids"].intersection(uuids):
            return tracker_type

    # Generic unknown tracker heuristic: persistent BLE, no audio, short payload
    if uuids and not uuids.intersection(_AUDIO_UUIDS):
        total_payload = sum(len(v) for v in mfr.values())
        if total_payload < 32 and adv.tx_power is not None:
            return "unknown"

    return None


def make_sighting(device: BLEDevice, adv: AdvertisementData, tracker_type: str) -> Sighting:
    raw = "".join(
        v.hex() for v in (adv.manufacturer_data or {}).values()
    )
    return Sighting(
        ts=datetime.now(timezone.utc),
        mac=device.address,
        rssi=adv.rssi if adv.rssi is not None else -999,
        tracker_type=tracker_type,
        raw_adv_hex=raw,
    )


async def scan_forever(callback: Callable[[Sighting], None]) -> None:
    """Scan BLE indefinitely, calling callback for each tracker sighting."""

    def _detection_callback(device: BLEDevice, adv: AdvertisementData) -> None:
        tracker_type = classify_advertisement(device, adv)
        if tracker_type:
            callback(make_sighting(device, adv, tracker_type))

    async with BleakScanner(detection_callback=_detection_callback):
        await asyncio.Event().wait()
