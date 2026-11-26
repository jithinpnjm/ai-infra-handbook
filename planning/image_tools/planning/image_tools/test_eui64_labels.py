#!/usr/bin/env python3
import json, re, pathlib

spec_item = [x for x in json.load(open('specs/p3_02_03.json')) if x['name'] == 'p3-0203-eui64'][0]
expected_labels = [spec_item['title']] + re.findall(r"'([^']*)'", spec_item['spec'])

print("Expected labels count:", len(expected_labels))
for i, l in enumerate(expected_labels):
    print(f"[{i:2d}] len={len(l):3d} : '{l}'")
