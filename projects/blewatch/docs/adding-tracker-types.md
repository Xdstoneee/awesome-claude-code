# Adding a New Tracker Type

1. **Identify the advertisement signature** using a BLE sniffer or `btmon`:
   - Manufacturer company ID (2-byte little-endian in manufacturer data)
   - Service UUID (listed in service UUIDs field)

2. **Add the signature** to `TRACKER_SIGNATURES` in `src/blewatch/scanner.py`:

```python
"YourTracker": {
    "company_id": 0xXXXX,
    "service_uuids": {"0000xxxx-0000-1000-8000-00805f9b34fb"},
},
```

3. **Add a unit test** in `tests/test_scanner.py`:

```python
def test_yourtracker_detected():
    adv = _make_adv(
        company_id=0xXXXX,
        service_uuids=["0000xxxx-0000-1000-8000-00805f9b34fb"],
    )
    assert classify_advertisement(_make_device(), adv) == "YourTracker"
```

4. **Update README.md** — add a row to the "Supported Trackers" table.

5. Run `pytest tests/` to verify no regressions.

## Advertisement Byte Layout Reference

BLE advertisement packets follow this structure:

```
HCI LE Meta Event (0x3E) → LE Advertising Report (subevent 0x02)
  → per-report: event_type, address_type, address[6], data_length, data[], RSSI
     → data AD structures: length, AD type, AD data
        - AD type 0xFF = Manufacturer Specific: company_id[2] + payload
        - AD type 0x03/0x07 = 16-bit/128-bit Service UUIDs
```

Use `btmon -w capture.btsnoop` to capture and `wireshark` or `tshark` to inspect.
