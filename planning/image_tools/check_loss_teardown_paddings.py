#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_loss_teardown_candidate.svg")
root = tree.getroot()

lines_check = [
    # Title
    ("Title line 1", 1600, 0, "Transfer, loss recovery and teardown:", 48, False, 800, "middle"),
    ("Title line 2", 1600, 0, "why TIME_WAIT fills up", 48, False, 800, "middle"),

    # Left panel header
    ("Left header", 480, 40, "Receiving the body", 30, False, 136, "start"),

    # Left Card 1
    ("Left Card 1", 440, 60, "segments arrive shuffled", 25, False, 280, "middle"),

    # Left Card 2
    ("Left Card 2", 440, 60, "socket receive buffer", 26, False, 280, "middle"),

    # Left Card 3
    ("Left Card 3 line 1", 440, 60, "sends ACKs, often one", 24, False, 118, "start"),
    ("Left Card 3 line 2", 440, 60, "for every second segment,", 24, False, 76, "start"),
    ("Left Card 3 line 3", 440, 60, "with delayed ACK timers", 24, False, 76, "start"),

    # Left Card 4
    ("Left Card 4 line 1", 440, 60, "advertises its window:", 24, False, 118, "start"),
    ("Left Card 4 line 2", 440, 60, "the amount of data it is", 24, False, 76, "start"),
    ("Left Card 4 line 3", 440, 60, "ready to accept right now", 24, False, 76, "start"),

    # Left Card 5
    ("Left Card 5", 440, 60, "curl reads with recv", 25, True, 290, "middle"),

    # Middle panel header
    ("Middle header", 480, 560, "Loss", 32, False, 652, "start"),

    # Middle Route 1
    ("Middle Route 1 line 1", 405, 580, "fast retransmit", 24, False, 638, "start"),
    ("Middle Route 1 line 2", 405, 580, "after three duplicate", 24, False, 596, "start"),
    ("Middle Route 1 line 3", 405, 580, "ACKs, or through", 24, False, 596, "start"),
    ("Middle Route 1 line 4", 405, 580, "SACK", 24, False, 596, "start"),

    # Middle Route 2
    ("Middle Route 2 line 1", 405, 580, "retransmission timeout", 24, False, 638, "start"),
    ("Middle Route 2 line 2", 405, 580, "fires", 24, False, 596, "start"),

    # Middle Card 3
    ("Middle Card 3 line 1", 440, 580, "congestion window", 26, False, 800, "middle"),
    ("Middle Card 3 line 2", 440, 580, "collapses, then regrows", 26, False, 800, "middle"),

    # Right panel header
    ("Right header", 480, 1080, "Closing", 32, False, 1172, "start"),

    # Right Card 1
    ("Right Card 1 line 1", 440, 1100, "FIN, ACK exchange", 25, False, 1160, "start"),
    ("Right Card 1 line 2", 440, 1100, "(or RST on abort)", 25, False, 1118, "start"),

    # Right Card 2
    ("Right Card 2 line 1", 440, 1100, "the side that closes", 24, False, 1158, "start"),
    ("Right Card 2 line 2", 440, 1100, "first holds the connection", 24, False, 1118, "start"),
    ("Right Card 2 line 3", 440, 1100, "in TIME_WAIT for about", 24, False, 1118, "start"),
    ("Right Card 2 line 4", 440, 1100, "60 seconds on Linux", 24, False, 1118, "start"),

    # Right Card 3
    ("Right Card 3 line 1", 440, 1100, "stops late packets from", 24, False, 1158, "start"),
    ("Right Card 3 line 2", 440, 1100, "corrupting a new", 24, False, 1118, "start"),
    ("Right Card 3 line 3", 440, 1100, "connection that reuses", 24, False, 1118, "start"),
    ("Right Card 3 line 4", 440, 1100, "the same 5-tuple", 24, False, 1118, "start"),

    # Warning Card
    ("Warning line 1", 1520, 40, "Thousands of short connections can exhaust ephemeral ports (32768 to 60999)", 26, False, 140, "start"),
    ("Warning line 2", 1520, 40, "or fill the table with TIME_WAIT entries", 26, False, 140, "start"),

    # Command strip
    ("Command ss -s", 200, 40, "ss -s", 25, True, 110, "start"),
    ("Command ss -tni", 1340, 220, "ss -tni dst 93.184.216.34 (rtt, cwnd, mss, retrans, bytes)", 24, True, 260, "start"),

    # Bottom bar
    ("Bottom bar line 1", 1520, 40, "If your service opens thousands of short connections,", 24, False, 800, "middle"),
    ("Bottom bar line 2", 1520, 40, "watch the TIME_WAIT count before you scale it up", 24, False, 800, "middle")
]

print("=== CHECKING PADDINGS AND BOX CONFINEMENT (rule: >= 16px padding) ===")
all_pass = True
for name, box_w, box_x, text, fs, is_mono, text_x, anchor in lines_check:
    c = 0.62 if is_mono else 0.6
    w = len(text) * fs * c
    if anchor == "middle":
        left = text_x - w / 2
        right = text_x + w / 2
    else:
        left = text_x
        right = text_x + w
    
    pad_left = left - box_x
    pad_right = (box_x + box_w) - right
    
    ok = (pad_left >= 16 and pad_right >= 16)
    if not ok:
        all_pass = False
    print(f"[{'PASS' if ok else 'FAIL'}] {name:25s} | pad_left={pad_left:5.1f}px, pad_right={pad_right:5.1f}px (min 16) | text='{text[:35]}...'")

assert all_pass, "Some text lines violated the 16px padding rule!"
print("\nALL PADDING CHECKS PASSED: Every text line has >= 16px clearance from its box boundaries!")
