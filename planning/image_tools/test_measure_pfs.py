#!/usr/bin/env python3
import sys

def est_width(text, is_mono=False, font_size=24):
    factor = 0.62 if is_mono else 0.6
    return len(text) * factor * font_size

labels = [
    ("Metadata, data and the parallel file system idea", 48, False),
    ("Client 1", 32, False),
    ("Client 2", 32, False),
    ("Client N", 32, False),
    ("Metadata service", 32, False),
    ("names, permissions, layouts", 24, False),
    ("Data server 1", 32, False),
    ("Data server 2", 32, False),
    ("Data server M", 32, False),
]

print("Estimated widths:")
for text, fs, mono in labels:
    w = est_width(text, mono, fs)
    print(f"[{fs}px] '{text}': {w:.1f}px")
