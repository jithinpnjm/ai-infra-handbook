#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def build_svg():
    # Dimensions
    w = 1600
    h = 1200
    
    # Text line breaks planning
    # Let's inspect every label and its wrapped lines
    lines_map = {
        # Title (48px bold)
        "title": [
            "What the client sees when a connection fails,",
            "and where to look"
        ],
        # Col 1 Header (28px bold)
        "col1_hdr": [
            "Error the client sees"
        ],
        # Col 2 Header (28px bold)
        "col2_hdr": [
            "What actually happened",
            "on the wire"
        ],
        # Col 3 Header (28px bold)
        "col3_hdr": [
            "Where to look"
        ],
        # Row 1 Col 1 (24px bold)
        "r1_c1": [
            "Connection refused",
            "(ECONNREFUSED)"
        ],
        # Row 1 Col 2 (24px)
        "r1_c2": [
            "a RST came back: host reachable,",
            "nobody listening on that port, or a",
            "firewall using reject --tcp-reset"
        ],
        # Row 1 Col 3 (24px)
        "r1_c3": [
            "the listener: somebody",
            "was home and said no"
        ],
        # Row 2 Col 1 (24px bold)
        "r2_c1": [
            "Connection timed out",
            "(ETIMEDOUT)"
        ],
        # Row 2 Col 2 (24px)
        "r2_c2": [
            "no reply to the SYNs, retried with",
            "exponential backoff 1, 2, 4 seconds",
            "and so on; tcp_syn_retries=6",
            "gives about 127 seconds"
        ],
        # Row 2 Col 3 (24px, orange box)
        "r2_c3": [
            "route and firewall or security",
            "group, host down: nobody",
            "answered the door at all"
        ],
        # Row 3 Col 1 (24px bold)
        "r3_c1": [
            "No route to host or",
            "Network is unreachable"
        ],
        # Row 3 Col 2 (24px)
        "r3_c2": [
            "ICMP unreachable from a",
            "router, or no local route"
        ],
        # Row 3 Col 3 (24px)
        "r3_c3": [
            "the routing table",
            "(chapter 2.5)"
        ],
        # Row 4 Col 1 (24px bold)
        "r4_c1": [
            "Connection reset by peer"
        ],
        # Row 4 Col 2 (24px)
        "r4_c2": [
            "a RST during an established",
            "connection"
        ],
        # Row 4 Col 3 (24px)
        "r4_c3": [
            "peer crashed, app closed with",
            "unread data, firewall or NAT",
            "state expired, load balancer",
            "idle timeout"
        ],
        # Left Panel (24px bold)
        "lp_refused": [
            "SYN then RST"
        ],
        "lp_timeout": [
            "SYN retried"
        ],
        # Takeaway (24px bold)
        "takeaway": [
            "A refusal means the host answered, so look at the listener;",
            "a timeout means the SYNs never got a reply, so look at the route and firewall"
        ]
    }
    
    # Check max character width for each box
    # Col 1: w = 360 (printable >= 328)
    # Col 2: w = 460 (printable >= 428)
    # Col 3: w = 380 (printable >= 348)
    
    for key, lns in lines_map.items():
        full = " ".join(lns)
        for ln in lns:
            # 24px: 0.6 * 24 = 14.4
            # 28px: 0.6 * 28 = 16.8
            # 48px: 0.6 * 48 = 28.8
            fs = 48 if "title" in key else (28 if "hdr" in key else 24)
            w_est = len(ln) * 0.6 * fs
            print(f"[{key:10s}|{fs:2d}px] len={len(ln):2d} w={w_est:5.1f}px: '{ln}'")

build_svg()
