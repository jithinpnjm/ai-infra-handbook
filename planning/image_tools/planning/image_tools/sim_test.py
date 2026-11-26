#!/usr/bin/env python3
import re

# Font metrics:
# sans: 0.60 * fs
# mono: 0.62 * fs

def text_width(text, fs, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * factor * fs

counters = [
    "rising carrier_changes",
    "non-zero rx_crc_errors or uncorrected FEC",
    "rx_discards and rx_out_of_buffer",
    "rx_pause and tx_pause",
    "NIC at the wrong speed, a 400G NIC at 100G"
]

suspects = [
    "link flapping: cable, optic, transceiver seating, switch port, power",
    "marginal signal: dirty or failing optic, bad DAC, bent fibre",
    "host cannot drain traffic fast enough, or switch or NIC buffers overflow",
    "flow control is active",
    "cable, optic, lane problem, or switch configuration"
]

commands = [
    "ip -s link show eth0; cat /sys/class/net/eth0/carrier_changes",
    "ethtool -S eth0 | egrep crc|fcs|err|drop|pause|pfc",
    "ethtool --show-fec eth0",
    "ethtool -m eth0 (DOM: temperature, Tx/Rx optical power)",
    "dmesg -T | egrep -i link",
    "lldpcli show neighbors (which switch and port is at the far end)"
]

print("=== MONO COMMANDS (fs=24) ===")
for cmd in commands:
    print(f"'{cmd}' -> len={len(cmd)}, width={text_width(cmd, 24, True):.1f}px")

print("\n=== COUNTERS (fs=30) ===")
for c in counters:
    print(f"'{c}' -> len={len(c)}, width={text_width(c, 30, False):.1f}px")

print("\n=== SUSPECTS (fs=24) ===")
for s in suspects:
    print(f"'{s}' -> len={len(s)}, width={text_width(s, 24, False):.1f}px")
