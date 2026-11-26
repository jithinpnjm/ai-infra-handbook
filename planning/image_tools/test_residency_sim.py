#!/usr/bin/env python3
# Layout simulation script

# Check text wrapping and box dimensions
def text_width(text, size=24, is_mono=False):
    factor = 0.62 if is_mono else 0.6
    return len(text) * size * factor

labels = [
    ("Title", "Route by the endpoint's region, never by nearest", 48),
    ("Control plane", "Control plane: metadata only, global", 30),
    ("EU Region", "EU region (promised region)", 32),
    ("US Region", "US region", 32),
    ("European customer", "European customer", 30),
    ("Green arrow", "Routed by endpoint region", 26),
    ("Red arrow L1", "Nearest region: breaks the promise", 25),
    ("Red arrow L2", "without an error", 25),
    ("Gateway", "Gateway", 30),
    ("Replica group", "Replica group", 30),
    ("Log store", "Log store", 30),
    ("Logs stay L1", "Prompts, completions and", 24),
    ("Logs stay L2", "logs stay in region", 24),
    ("Metering", "Metering", 30),
    ("Metering leave L1", "Metering events leave only", 24),
    ("Metering leave L2", "after content is stripped", 24),
    ("Bottom note", "Cross-region failover is off by default for residency-bound tenants.", 26)
]

print("=== TEXT WIDTH ESTIMATIONS ===")
for name, txt, sz in labels:
    w = text_width(txt, sz)
    print(f"{name:20s} ({sz}px): len={len(txt):2d}, est_width={w:6.1f}px | '{txt}'")
