import re

# Steps content:
steps = [
    {
        "num": "1",
        "full": "Quantify: throughput, latency percentiles, retransmit rate, against baseline and line rate or BDP",
        "lines": [
            ("Quantify: throughput, latency percentiles,", 30, "bold"),
            ("retransmit rate, against baseline and line rate or BDP", 24, "normal")
        ]
    },
    {
        "num": "2",
        "full": "Find the limit: ss -ti limiter flags, CPU and softirq, NIC drops, PFC, ECN, MTU",
        "lines": [
            ("Find the limit: ss -ti limiter flags,", 30, "bold"),
            ("CPU and softirq, NIC drops, PFC, ECN, MTU", 24, "normal")
        ]
    },
    {
        "num": "3",
        "full": "Find the segment: iperf3 or ib_write_bw between pairs, halving the path",
        "lines": [
            ("Find the segment: iperf3 or ib_write_bw", 30, "bold"),
            ("between pairs, halving the path", 24, "normal")
        ]
    },
    {
        "num": "4",
        "full": "Loss or latency: nstat and tcpretrans for loss, ss -ti and ping for RTT",
        "lines": [
            ("Loss or latency: nstat and tcpretrans for loss,", 30, "bold"),
            ("ss -ti and ping for RTT", 24, "normal")
        ]
    },
    {
        "num": "5",
        "full": "One flow or all flows: ECMP hash collisions, elephant flows, single-core limits",
        "lines": [
            ("One flow or all flows: ECMP hash collisions,", 30, "bold"),
            ("elephant flows, single-core limits", 24, "normal")
        ]
    }
]

side_box = {
    "full": "Step 6: compare with a healthy node",
    "lines": [
        ("Step 6:", 30, "bold"),
        ("compare with", 24, "normal"),
        ("a healthy node", 24, "normal")
    ]
}

caption = "Each step removes part of the search space before the next one starts."

print("All step labels defined.")

