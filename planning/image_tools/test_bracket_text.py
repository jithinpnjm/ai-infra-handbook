#!/usr/bin/env python3
import re

text = "each layer fails in its own way"
lines = ["each layer", "fails in", "its own", "way"]
fs = 24
rate = 0.60
for l in lines:
    tw = len(l) * rate * fs
    print(f"Line '{l:12s}': len={len(l):2d}, tw={tw:5.1f}px")
