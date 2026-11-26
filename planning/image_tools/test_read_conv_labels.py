#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

spec_labels = [
    "Reading the sample trace line by line as a conversation",
    "duplex.example.com (client)",
    "mikado.example.com (server)",
    "arp who-has mikado tell duplex",
    "arp reply mikado is-at 0:2:2d:b:ee:4e",
    "S 3200063165 win 5840 mss 1460 sackOK (DF)",
    "S ack 3200063166 win 5792",
    ". ack 1",
    "P 1:427(426)",
    ". ack 427",
    "P 1:773(772)",
    ". ack 773",
    "lines 1-2: finding the link address because the client needs the server's MAC before it can send a frame",
    "lines 3-5: three-way handshake",
    "lines 6-9: data",
    "summary: 9 packets received by filter, 0 packets dropped by kernel",
    "S SYN, S. SYN-ACK, . ACK, P. PSH-ACK, F. FIN-ACK, R or R. RST",
    "Read the flags in order; a SYN with no reply stops the story at the first line, and the next question is who stayed silent"
]

print(f"Total labels: {len(spec_labels)}")
for i, l in enumerate(spec_labels, 1):
    print(f"{i:2d}. len={len(l):2d}: '{l}'")
