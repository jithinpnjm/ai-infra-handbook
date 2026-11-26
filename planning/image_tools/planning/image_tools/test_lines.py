#!/usr/bin/env python3
import re

counters = [
    ("rising carrier_changes", [
        "rising",
        "carrier_changes"
    ]),
    ("non-zero rx_crc_errors or uncorrected FEC", [
        "non-zero rx_crc_errors",
        "or uncorrected FEC"
    ]),
    ("rx_discards and rx_out_of_buffer", [
        "rx_discards and",
        "rx_out_of_buffer"
    ]),
    ("rx_pause and tx_pause", [
        "rx_pause and",
        "tx_pause"
    ]),
    ("NIC at the wrong speed, a 400G NIC at 100G", [
        "NIC at the wrong speed,",
        "a 400G NIC at 100G"
    ])
]

# Let's check widths at 30px bold (0.60 * 30 = 18 px/char)
print("=== COUNTERS AT 30px BOLD (18 px/char) ===")
for full, lines in counters:
    print(f"Full: '{full}'")
    for line in lines:
        w = len(line) * 18
        print(f"   '{line}' -> len={len(line)}, w={w}px")

suspects = [
    ("link flapping: cable, optic, transceiver seating, switch port, power", [
        "link flapping: cable, optic,",
        "transceiver seating,",
        "switch port, power"
    ]),
    ("marginal signal: dirty or failing optic, bad DAC, bent fibre", [
        "marginal signal: dirty or",
        "failing optic, bad DAC,",
        "bent fibre"
    ]),
    ("host cannot drain traffic fast enough, or switch or NIC buffers overflow", [
        "host cannot drain traffic fast",
        "enough, or switch or NIC",
        "buffers overflow"
    ]),
    ("flow control is active", [
        "flow control is active"
    ]),
    ("cable, optic, lane problem, or switch configuration", [
        "cable, optic, lane problem,",
        "or switch configuration"
    ])
]

print("\n=== SUSPECTS AT 24px (14.4 px/char) ===")
for full, lines in suspects:
    print(f"Full: '{full}'")
    for line in lines:
        w = len(line) * 14.4
        print(f"   '{line}' -> len={len(line)}, w={w:.1f}px")
