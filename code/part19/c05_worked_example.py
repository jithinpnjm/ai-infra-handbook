#!/usr/bin/env python3
"""Worked arithmetic for chapter 19.5: algbw, busbw and efficiency from size and time.

The times below are constructed to practise the formulas. They were not
measured on any cluster.
"""
from c05_nccl_parse import algbw_gbs, busbw_factor

CASES = [
    # label, collective, ranks, size in bytes, time in microseconds
    ("8 ranks in one node, 64 MiB", "all_reduce", 8, 64 << 20, 1653.1),
    ("16 ranks on two nodes, 1 GiB", "all_reduce", 16, 1 << 30, 44739.2),
    ("64 ranks on eight nodes, 1 GiB", "all_reduce", 64, 1 << 30, 46970.0),
    ("64 ranks on eight nodes, half-rate link", "all_reduce", 64, 1 << 30, 93940.0),
]


def row(collective, ranks, size, time_us, link_gbps=None):
    alg = algbw_gbs(size, time_us)
    f = busbw_factor(collective, ranks)
    out = {"algbw": round(alg, 2), "factor": f, "busbw": round(alg * f, 2)}
    if link_gbps:
        out["efficiency"] = round(alg * f / (link_gbps / 8), 3)
    return out


if __name__ == "__main__":
    for label, coll, n, size, t in CASES:
        print(label, row(coll, n, size, t, link_gbps=400 if 'nodes' in label else None))
