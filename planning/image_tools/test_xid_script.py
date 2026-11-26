import re

text_items = [
    ("Title", ["The Xid gauge stays high after the repair"], 48, False),
    ("Timeline Header", ["Timeline with a line plot of DCGM_FI_DEV_XID_ERROR for one GPU"], 30, False),
    ("Step 1", ["Xid 79 appears, gauge jumps to 79"], 24, False),
    ("Step 2", [
        "node repaired, but gauge stays at 79",
        "until another Xid replaces it or the",
        "exporter restarts"
    ], 24, False),
    ("Step 3", [
        "alert on equals 79 keeps firing",
        "after the repair"
    ], 24, False),
    ("Wrong Alert", ["DCGM_FI_DEV_XID_ERROR == 79"], 26, True),
    ("Right Alert", [
        "value plus recency: check when the",
        "value last changed, not only what",
        "it is"
    ], 24, False),
    ("Side Note", [
        "a bad exporter restart can also",
        "re-emit a stuck gauge, so confirm",
        "a real Xid with dmesg on one node"
    ], 24, False),
    ("Footer", [
        "verify each metric name against /metrics on your exporter version; throttle, double-bit ECC and NVLink CRC counters",
        "are not enabled by default in DCGM exporter 4.9.0, enable them"
    ], 24, False)
]

for name, lines, fs, is_mono in text_items:
    rate = 0.62 if is_mono else 0.60
    print(f"=== {name} (fs={fs}) ===")
    for l in lines:
        w = len(l) * rate * fs
        print(f"  [{len(l):2d} chars, {w:6.1f}px] '{l}'")
