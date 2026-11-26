import re
import json

spec = json.load(open('specs/p3_01_19.json'))[0]
title = spec['title']
raw_labels = [title] + re.findall(r"'([^']*)'", spec['spec'])

print(f"Total labels: {len(raw_labels)}")
for i, l in enumerate(raw_labels, 1):
    print(f"{i:2d}. len={len(l):3d}: {l}")
