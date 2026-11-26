#!/usr/bin/env python3
import glob
import re

for f in glob.glob("planning/image_tools/audit_*.py") + glob.glob("planning/image_tools/planning/image_tools/audit_*.py"):
    content = open(f).read()
    m = re.search(r'expected_labels\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if m:
        labels_str = m.group(1)
        print(f"=== {f} ===")
        labels = [l.strip().strip('"').strip("'") for l in labels_str.strip().split('\n') if l.strip()]
        for l in labels:
            print("  ", l)
