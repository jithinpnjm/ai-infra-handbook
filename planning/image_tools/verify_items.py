import json, re

data = json.load(open('specs/p3_04_06.json'))
spec_item = [x for x in data if x.get('name') == 'p4-0406-canary-walk'][0]
expected_labels = [spec_item['title']] + re.findall(r"'([^']*)'", spec_item['spec'])

print(f"Total expected labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels):
    print(f" {i:2d}. {l[:70]}")
