#!/usr/bin/env python3

# Layout test script for the funnel and side box

steps_data = [
    {
        "step": 1,
        "y": 170,
        "h": 142,
        "poly": [(40, 170), (1140, 170), (1100, 312), (80, 312)],
        "inner_left": 80,
        "inner_right": 1100,
        "lines": [
            ("Quantify: ", 30, "sans", "bold"),
            ("throughput, latency percentiles, ", 24, "sans", "normal"),
            ("retransmit rate, against baseline and line rate or BDP", 24, "sans", "normal")
        ]
    },
    {
        "step": 2,
        "y": 354,
        "h": 142,
        "poly": [(80, 354), (1100, 354), (1060, 496), (120, 496)],
        "inner_left": 120,
        "inner_right": 1060,
        "lines": [
            ("Find the limit: ", 30, "sans", "bold"),
            ("ss -ti", 24, "mono", "normal"),
            (" limiter flags, CPU and softirq, ", 24, "sans", "normal"),
            ("NIC drops, PFC, ECN, MTU", 24, "sans", "normal")
        ]
    },
    {
        "step": 3,
        "y": 538,
        "h": 142,
        "poly": [(120, 538), (1060, 538), (1020, 680), (160, 680)],
        "inner_left": 160,
        "inner_right": 1020,
        "lines": [
            ("Find the segment: ", 30, "sans", "bold"),
            ("iperf3", 24, "mono", "normal"),
            (" or ", 24, "sans", "normal"),
            ("ib_write_bw", 24, "mono", "normal"),
            (" between pairs, ", 24, "sans", "normal"),
            ("halving the path", 24, "sans", "normal")
        ]
    },
    {
        "step": 4,
        "y": 722,
        "h": 142,
        "poly": [(160, 722), (1020, 722), (980, 864), (200, 864)],
        "inner_left": 200,
        "inner_right": 980,
        "lines": [
            ("Loss or latency: ", 30, "sans", "bold"),
            ("nstat", 24, "mono", "normal"),
            (" and ", 24, "sans", "normal"),
            ("tcpretrans", 24, "mono", "normal"),
            (" for loss, ", 24, "sans", "normal"),
            ("ss -ti", 24, "mono", "normal"),
            (" and ", 24, "sans", "normal"),
            ("ping", 24, "mono", "normal"),
            (" for RTT", 24, "sans", "normal")
        ]
    },
    {
        "step": 5,
        "y": 906,
        "h": 142,
        "poly": [(200, 906), (980, 906), (940, 1048), (240, 1048)],
        "inner_left": 240,
        "inner_right": 940,
        "lines": [
            ("One flow or all flows: ", 30, "sans", "bold"),
            ("ECMP hash collisions, ", 24, "sans", "normal"),
            ("elephant flows, single-core limits", 24, "sans", "normal")
        ]
    }
]

print("Steps data loaded.")
