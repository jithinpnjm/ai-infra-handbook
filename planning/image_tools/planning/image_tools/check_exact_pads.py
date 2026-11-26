#!/usr/bin/env python3

# Option 1: RSS (x=40, w=480, h=260) -> box interior: x 40..520, y 620..880
# Text lines:
# Line 1: "RSS: hardware, " -> 15 chars sans 30px = 15 * 0.6 * 30 = 270px. Start x=64, end=334 < 504px (pass, pad 186px)
# Line 2: "NIC hashes to N receive " -> 24 chars sans 24px = 24 * 0.6 * 24 = 345.6px. Start x=64, end=409.6 < 504px (pass, pad 110px)
# Line 3: "queues " (7 chars) + "(ethtool -l eth0)" (17 chars mono)
# Width = 7 * 0.6 * 24 + 17 * 0.62 * 24 = 100.8 + 252.96 = 353.76px. Start x=64, end=417.8 < 504px (pass, pad 102px)

# Option 2: RPS (x=560, w=480, h=260) -> box interior: x 560..1040, y 620..880
# Line 1: "RPS: software, " -> 15 * 0.6 * 30 = 270px. Start 584, end 854 < 1024 (pass)
# Line 2: "steers to other CPUs " -> 21 * 0.6 * 24 = 302.4px. Start 584, end 886.4 < 1024 (pass)
# Line 3: "after the interrupt" -> 19 * 0.6 * 24 = 273.6px. Start 584, end 857.6 < 1024 (pass)

# Option 3: XPS (x=1080, w=480, h=260) -> box interior: x 1080..1560, y 620..880
# Line 1: "XPS: maps CPUs to " -> 18 * 0.6 * 30 = 324px. Start 1104, end 1428 < 1544 (pass, pad 132px)
# Line 2: "TX queues, avoids lock " -> 23 * 0.6 * 24 = 331.2px. Start 1104, end 1435.2 < 1544 (pass)
# Line 3: "contention and " -> 15 * 0.6 * 24 = 216px. Start 1104, end 1320 < 1544 (pass)
# Line 4: "cross-NUMA transmit" -> 19 * 0.6 * 24 = 273.6px. Start 1104, end 1377.6 < 1544 (pass)

# Orange note: (x=40, w=1520, h=80) -> box interior: x 40..1560, y 920..1000
# Text: "One core cannot process 100 Gb/s on its own" -> 43 chars sans 28px = 43 * 0.6 * 28 = 722.4px.
# Start x=145, end=867.4 < 1544 (pass, pad 692px)

# Footer: (x=40, w=1520, h=70) -> box interior: x 40..1560, y 1040..1110
# "mpstat -P ALL 1: " (17 chars mono 26px) + "is one core at 100%?" (20 chars sans 26px)
# Width = 17 * 0.62 * 26 + 20 * 0.6 * 26 = 274.04 + 312 = 586.04px.
# Start x=135, end=721.04 < 1544 (pass, pad 839px)

print("All card widths verified against conservative font estimation rules.")
