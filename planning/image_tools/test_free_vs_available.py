#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, subprocess, pathlib

# Let's inspect the exact labels
expected_labels = [
    "Free is small, available is large: the page cache is reclaimable",
    "total 1950 MB",
    "free 163 MB",
    "page cache, buffers and reclaimable",
    "used by applications",
    "available 1187 MB",
    "the kernel gives it back to applications on demand",
    "free, the column that looks scary",
    "163 MB",
    "free looks low, but that is not a problem.",
    "available, the number to read",
    "1187 MB",
    "Read available, not free."
]

print("Expected labels count:", len(expected_labels))
for i, l in enumerate(expected_labels, 1):
    print(f" {i:2d}. {l}")
