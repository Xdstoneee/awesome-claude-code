# blewatch

A CLI daemon for detecting BLE (Bluetooth Low Energy) stalker trackers in real time and from captured traffic files. Built for pentesters and privacy researchers.

## Why blewatch?

| Tool | Platform | Output | Offline pcap | Persistence heuristic | MAC rotation handling |
|------|----------|--------|--------------|----------------------|-----------------------|
| AirGuard | Mobile only | UI | No | Identifier-based | Defeated by fast rotation |
| DULT (Apple/Google) | Mobile only | No API | No | 30 min+ latency | No |
| **blewatch** | Linux/macOS CLI | JSON + human | Yes | N/T/D thresholds | Time-window grouping |

## Supported Trackers

- **Apple AirTag** — Company ID `0x004C`, service UUID `0xFD6F` (Find My)
- **Tile** — Company ID `0x000D`, service UUID `0xFEED`
- **Samsung SmartTag** — Company ID `0x0075`, service UUID `0xFD5A`
- **Unknown/generic** — any persistent BLE device matching tracker advertisement patterns

## Install

```bash
pip install -e .
# For offline pcap analysis:
pip install -e ".[pcap]"
```

Requires Python 3.10+. BLE scanning requires root/admin privileges or CAP_NET_RAW on Linux.

## Usage

### Live scan

```bash
# Scan indefinitely, alert to stdout as JSON
sudo blewatch scan

# Custom thresholds: 5 sightings in 15 min window
sudo blewatch scan --min-sightings 5 --window-minutes 15

# Human-readable output to stderr, JSON alerts to stdout
sudo blewatch scan --human
```

### Offline analysis

```bash
# Analyze a btsnoop capture
blewatch analyze capture.btsnoop

# Analyze a pcap file
blewatch analyze capture.pcap

# Pipe JSON alerts to jq
blewatch analyze capture.pcap | jq 'select(.tracker_type == "AirTag")'
```

## Alert Event Format

```json
{
  "event": "tracker_alert",
  "ts": "2026-06-29T14:32:00Z",
  "tracker_type": "AirTag",
  "mac": "AA:BB:CC:DD:EE:FF",
  "first_seen": "2026-06-29T14:20:00Z",
  "last_seen": "2026-06-29T14:32:00Z",
  "observation_count": 5,
  "confidence": "high"
}
```

## Physical Testing

Hardware used in development:
- Generic BLE tracker (unknown brand) — validates unknown-tracker detection path
- Tile Mate (needed for Tile UUID path validation — Tile headphones use audio BT, not Tile network protocol)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). To add a new tracker type, see [docs/adding-tracker-types.md](docs/adding-tracker-types.md).

## Roadmap

- v1.0 (July 31): Live scan + offline pcap + JSON output + persistence heuristic
- v1.1: CFO (Carrier Frequency Offset) fingerprinting for evasion-resistant detection
