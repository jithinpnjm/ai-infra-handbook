#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Test all expected labels and their character widths
labels = {
    "title": "Reading the sample trace line by line as a conversation",
    "host1": "duplex.example.com (client)",
    "host2": "mikado.example.com (server)",
    "line1": "arp who-has mikado tell duplex",
    "line2": "arp reply mikado is-at 0:2:2d:b:ee:4e",
    "line3": "S 3200063165 win 5840 mss 1460 sackOK (DF)",
    "line4": "S ack 3200063166 win 5792",
    "line5": ". ack 1",
    "line6": "P 1:427(426)",
    "line7": ". ack 427",
    "line8": "P 1:773(772)",
    "line9": ". ack 773",
    "bracket1": "lines 1-2: finding the link address because the client needs the server's MAC before it can send a frame",
    "bracket2": "lines 3-5: three-way handshake",
    "bracket3": "lines 6-9: data",
    "footer": "summary: 9 packets received by filter, 0 packets dropped by kernel",
    "legend": "S SYN, S. SYN-ACK, . ACK, P. PSH-ACK, F. FIN-ACK, R or R. RST",
    "bottom_bar": "Read the flags in order; a SYN with no reply stops the story at the first line, and the next question is who stayed silent"
}

print("Labels count:", len(labels))
for k, v in labels.items():
    print(f"[{k}] len={len(v)}: '{v}'")
