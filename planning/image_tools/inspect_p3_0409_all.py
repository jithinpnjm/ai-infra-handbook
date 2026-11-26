#!/usr/bin/env python3
import json
data = json.load(open('specs/p3_04_09.json'))
for item in data:
    print(item['name'])
    print("  Title:", item['title'])
    print("  Spec:", item['spec'])
