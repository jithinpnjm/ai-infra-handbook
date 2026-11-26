#!/usr/bin/env python3
import glob
import re

for f in sorted(glob.glob("planning/image_tools/*.py")):
    content = open(f).read()
    if "expected_labels =" in content:
        # extract expected_labels list
        match = re.search(r'expected_labels\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if match:
            items_str = match.group(1)
            # find all string literals
            items = re.findall(r'["\'](.*?)["\']', items_str)
            for item in items:
                if any(w in item.lower() for w in ["strip", "test", "reviewer", "habits", "table"]):
                    print(f"{f}: found suspicious item: '{item}'")
