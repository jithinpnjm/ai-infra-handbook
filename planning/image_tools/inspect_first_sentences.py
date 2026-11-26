#!/usr/bin/env python3
import json, glob

for p in sorted(glob.glob("specs/p3_*.json")):
    data = json.load(open(p))
    for item in data:
        spec = item.get('spec', '')
        first_sentence = spec.split('.')[0]
        name = item.get('name', '')
        print(f"{name:30s} | {first_sentence}")
