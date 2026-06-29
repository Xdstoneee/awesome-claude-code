# Contributing

This project is co-maintained by a pentest/privacy research group. See [docs/adding-tracker-types.md](docs/adding-tracker-types.md) for the fastest way to contribute.

## Setup

```bash
git clone <repo>
cd projects/blewatch
pip install -e ".[dev,pcap]"
```

## Running Tests

```bash
pytest tests/ -v
```

No hardware required — tests use mocked BLE callbacks and synthetic fixtures.

## Code Style

- No unnecessary comments — code should be self-documenting
- Type hints on all public functions
- New tracker types must have unit tests before merging

## Security

- Never commit BLE captures containing real MAC addresses of private devices
- Redact MACs in test fixtures (use `AA:BB:CC:DD:EE:FF` format)
- Report security issues via GitHub private vulnerability disclosure
