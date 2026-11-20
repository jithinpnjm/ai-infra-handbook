#!/usr/bin/env python3
import re

labels = [
    ("Note 1", 370, 128, ["--tags db", "runs only the", "tagged tier"], 24, "mono"),
    ("Note 2", 370, 128, ["-l app", "limits the run to", "one host group"], 24, "mono"),
    ("Orange callout", 390, 128, ["the database must exist", "before the app", "tries to connect"], 24, "sans"),
    ("Green link note", 390, 128, ["the app must answer", "before the proxy", "sends it traffic"], 24, "sans"),
    ("Takeaway bar", 1520, 110, [
        "The database must exist before the app tries to connect,",
        "and the app must answer before the proxy sends it traffic."
    ], 26, "sans")
]

for name, box_w, box_h, lines, sz, t in labels:
    avail_w = box_w - 32
    print(f"\n{name} (w={box_w}, h={box_h}, avail_w={avail_w}):")
    rate = 0.62 if t == "mono" else 0.6
    for line in lines:
        w = len(line) * sz * rate
        pad = (box_w - w) / 2
        print(f"  '{line}' len={len(line)} w={w:.1f}px, pad={pad:.1f}px (min 16px: {pad >= 16})")
        assert pad >= 16, f"Padding {pad} < 16 for '{line}'!"

print("\nALL LABELS PASS STRICT PADDING RULES!")
