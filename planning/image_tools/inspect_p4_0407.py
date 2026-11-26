#!/usr/bin/env python3
import json
data = json.load(open('specs/p3_04_07.json'))
item = [x for x in data if x.get('name') == 'p4-0407-local-facts'][0]
print(json.dumps(item, indent=2))
