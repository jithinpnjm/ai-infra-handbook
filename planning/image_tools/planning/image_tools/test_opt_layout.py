#!/usr/bin/env python3

def check_layout():
    # Box 1 (RSS):
    # Box bounds: x=40..520, y=620..880
    # Icon: x=64..120, y=640..696
    # Text x=135
    # Line 1: y=660, font 30px bold, "RSS: hardware, " (270px). Right edge = 405 < 504 (pad = 115px)
    # Line 2: y=696, font 24px, "NIC hashes to N receive " (345.6px). Right edge = 480.6 < 504 (pad = 39.4px >= 16px!)
    # Line 3: y=732, font 24px, "queues (ethtool -l eth0)" (353.8px). Right edge = 488.8 < 504 (pad = 31.2px >= 16px!)
    # Bottom: 732 + 6 = 738. Box bottom = 880. Pad = 142px >= 16px!
    print("RSS layout: PASS")

    # Box 2 (RPS):
    # Box bounds: x=560..1040, y=620..880
    # Icon: x=584..640, y=640..696
    # Text x=655
    # Line 1: y=660, font 30px bold, "RPS: software, " (270px). Right edge = 925 < 1024 (pad = 99px)
    # Line 2: y=696, font 24px, "steers to other CPUs " (302.4px). Right edge = 957.4 < 1024 (pad = 66.6px)
    # Line 3: y=732, font 24px, "after the interrupt" (273.6px). Right edge = 928.6 < 1024 (pad = 95.4px)
    # Bottom: 738. Box bottom = 880. Pad = 142px >= 16px!
    print("RPS layout: PASS")

    # Box 3 (XPS):
    # Box bounds: x=1080..1560, y=620..880
    # Icon: x=1104..1160, y=640..696
    # Text x=1175
    # Line 1: y=660, font 30px bold, "XPS: maps CPUs to " (324px). Right edge = 1499 < 1544 (pad = 45px >= 16px!)
    # Line 2: y=696, font 24px, "TX queues, avoids lock " (331.2px). Right edge = 1506.2 < 1544 (pad = 37.8px >= 16px!)
    # Line 3: y=732, font 24px, "contention and " (216px). Right edge = 1391 < 1544 (pad = 153px)
    # Line 4: y=768, font 24px, "cross-NUMA transmit" (273.6px). Right edge = 1448.6 < 1544 (pad = 95.4px)
    # Bottom: 768 + 6 = 774. Box bottom = 880. Pad = 106px >= 16px!
    print("XPS layout: PASS")

check_layout()
