# Changelog

## [Unreleased] — v1.0.0

### Added
- BLE live scanner with AirTag, Tile, SmartTag, and unknown tracker detection
- Persistence heuristic engine (N sightings / T minutes / D meters thresholds)
- JSON structured alert output (SIEM-compatible) to stdout
- Human-readable summary to stderr
- Offline btsnoop/pcap analysis mode
- MAC rotation grouping fallback by (tracker_type, time_window)
- CLI entry point: `blewatch scan` and `blewatch analyze <file>`
