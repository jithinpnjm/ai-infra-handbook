#!/usr/bin/env python3
import glob, re

for f in sorted(glob.glob("*.py")):
    content = open(f).read()
    if "p4-04" in content or "p3_04" in content:
        print(f"File: {f}")
        for line in content.splitlines():
            if "expected_labels" in line or "spec_item" in line or "p4-04" in line:
                print("  ", line.strip())
