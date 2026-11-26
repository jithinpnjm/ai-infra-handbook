import json
import re

data = json.load(open('specs/p3_04_07.json'))
item = [x for x in data if x.get('name') == 'p4-0407-local-facts'][0]
title = item['title']
spec = item['spec']

expected = [title] + re.findall(r"'([^']*)'", spec)
print(f"Total expected labels: {len(expected)}")
for i, exp in enumerate(expected):
    print(f"{i:2d}: [{len(exp)} chars] '{exp}'")
