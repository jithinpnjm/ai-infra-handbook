import xml.etree.ElementTree as ET
import re

# Canvas: 1600 x 1200
# Margins: left=50, right=1550 (width=1500)
# Top margin: 40

# Let's check text widths using conservative formulas:
# sans: 0.6 * fs * len
# mono: 0.62 * fs * len

labels = [
    # Title
    ("The canary ladder moves traffic up in steps, and each step must pass its gates", 48, "bold"),
    # Gate groups
    ("Latency gates", 32, "bold"),
    ("canary TTFT p99 and ITL p99 against baseline, ratio limit", 24, "normal"),
    ("Quality gates", 32, "bold"),
    ("eval score, finish_reason length share, error rate", 24, "normal"),
    # Step circles
    ("1", 26, "bold"),
    ("2", 26, "bold"),
    ("3", 26, "bold"),
    ("4", 26, "bold"),
    ("5", 26, "bold"),
    ("6", 26, "bold"),
    # Step boxes
    ("Shadow traffic", 28, "bold"),
    ("1 percent", 28, "bold"),
    ("5 percent", 28, "bold"),
    ("25 percent", 28, "bold"),
    ("50 percent", 28, "bold"),
    ("100 percent", 28, "bold"),
    # Gate diamonds
    ("gates pass", 24, "bold"),
    # Outcome boxes
    ("Promote", 32, "bold"),
    ("all gates passed, enough traffic", 24, "normal"),
    ("Hold", 32, "bold"),
    ("marginal results or too few requests", 24, "normal"),
    ("Rollback", 32, "bold"),
    ("hard failure such as quality drop or zero tokens", 24, "normal"),
    # Arrows
    ("hard failure", 24, "bold"),
    ("wait for more evidence", 24, "bold"),
    # Takeaway
    ("Promote only on a clean pass with enough traffic, hold on thin data, roll back on a hard signal.", 25, "bold")
]

print(f"Total labels to place: {len(labels)}")
for text, fs, weight in labels:
    w = len(text) * 0.6 * fs
    print(f"[{fs}px {weight:6s}] w={w:6.1f}px | '{text}'")
