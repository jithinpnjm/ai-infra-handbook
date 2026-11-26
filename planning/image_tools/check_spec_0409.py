#!/usr/bin/env python3
import json, re

data = json.load(open('specs/p3_04_09.json'))
item = [x for x in data if x.get('name') == 'p4-0409-app-play-stages'][0]
print("Title:", item['title'])
print("Spec:", item['spec'])
quotes = re.findall(r"'([^']*)'", item['spec'])
print("Single quotes:", quotes)
