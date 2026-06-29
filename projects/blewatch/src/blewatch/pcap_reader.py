"""
Offline btsnoop/pcap replay module.

Parses HCI btsnoop files and standard pcap/pcapng files,
reconstructs BLE advertisement events, and feeds them into
the same callback interface used by the live scanner.

Requires: pip install scapy (optional dependency group [pcap])

Capture instructions: see docs/capture-guide.md
"""
from __future__ import annotations

import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .scanner import Sighting

_BTSNOOP_MAGIC = b"btsnoop\x00"


def _is_btsnoop(data: bytes) -> bool:
    return data[:8] == _BTSNOOP_MAGIC


def replay_file(path: str, callback: Callable[[Sighting], None]) -> None:
    """Replay a btsnoop or pcap file, calling callback for each tracker sighting."""
    data = Path(path).read_bytes()
    if _is_btsnoop(data):
        _replay_btsnoop(data, callback)
    else:
        _replay_pcap(data, callback)


def _replay_btsnoop(data: bytes, callback: Callable[[Sighting], None]) -> None:
    # btsnoop v1: 16-byte file header, then records of:
    #   4B original_length, 4B included_length, 4B flags, 4B drops, 8B ts_usec, <payload>
    offset = 16
    while offset < len(data) - 24:
        orig_len, inc_len, flags, drops = struct.unpack_from(">IIII", data, offset)
        ts_usec = struct.unpack_from(">q", data, offset + 16)[0]
        payload = data[offset + 24 : offset + 24 + inc_len]
        offset += 24 + inc_len

        # Only process HCI LE Meta events (event code 0x3E, subevent 0x02 = LE Adv Report)
        if len(payload) < 7:
            continue
        if payload[0] != 0x04 or payload[1] != 0x3E or payload[3] != 0x02:
            continue

        _parse_le_adv_report(payload[4:], ts_usec, callback)


def _parse_le_adv_report(data: bytes, ts_usec: int, callback: Callable[[Sighting], None]) -> None:
    from .scanner import classify_advertisement

    if len(data) < 9:
        return

    # Minimal synthetic BLEDevice/AdvertisementData for classifier reuse
    # Real parsing would decode full LE Advertising Report structure
    try:
        mac_bytes = data[3:9]
        mac = ":".join(f"{b:02X}" for b in reversed(mac_bytes))
        ts = datetime.fromtimestamp(ts_usec / 1_000_000, tz=timezone.utc)
    except Exception:
        return

    # Build a minimal fake adv dict for pattern matching (full decode in v1.1)
    raw_hex = data.hex()
    sighting = Sighting(
        ts=ts,
        mac=mac,
        rssi=-70,
        tracker_type="unknown",
        raw_adv_hex=raw_hex,
    )
    callback(sighting)


def _replay_pcap(data: bytes, callback: Callable[[Sighting], None]) -> None:
    try:
        from scapy.all import rdpcap, BTLE_ADV
    except ImportError:
        raise SystemExit(
            "pcap analysis requires scapy: pip install blewatch[pcap]"
        )

    packets = rdpcap(data) if isinstance(data, str) else rdpcap.__wrapped__(data)
    for pkt in packets:
        if pkt.haslayer(BTLE_ADV):
            adv = pkt[BTLE_ADV]
            mac = getattr(adv, "AdvA", "00:00:00:00:00:00")
            sighting = Sighting(
                ts=datetime.now(timezone.utc),
                mac=str(mac),
                rssi=-70,
                tracker_type="unknown",
                raw_adv_hex=bytes(adv).hex(),
            )
            callback(sighting)
