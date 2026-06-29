# Capture Guide

## Linux (btmon)

```bash
# Capture to btsnoop file
sudo btmon -w capture.btsnoop

# In another terminal, start blewatch analysis
blewatch analyze capture.btsnoop
```

## macOS (PacketLogger)

1. Install Xcode or Additional Tools for Xcode
2. Open PacketLogger from `/Applications/Xcode.app/.../PacketLogger`
3. Start capture, File → Save As → `.btsnoop`
4. `blewatch analyze capture.btsnoop`

## Standard pcap (with Scapy or Wireshark)

```bash
# Requires blewatch[pcap]
pip install "blewatch[pcap]"
blewatch analyze capture.pcap
```

## Tips

- Carry the device you're testing (generic tracker) in a bag for 10+ minutes
- Walk a varied route — straight lines give fewer time-window crossings
- Capture at least 15 minutes of traffic for persistence testing
- Redact real MAC addresses before sharing captures (replace with `AA:BB:CC:DD:EE:XX`)
