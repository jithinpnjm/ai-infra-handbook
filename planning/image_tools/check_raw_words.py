#!/usr/bin/env python3
import re

svg_str = open("candidate_cluster.svg").read()
# Find all occurrences of words like orange, green, grey, bold, monospace, arrow
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
for w in forbidden:
    matches = re.findall(rf'\b{w}\b', svg_str, re.IGNORECASE)
    print(f"Word '{w}': {len(matches)} occurrences in raw svg string")
