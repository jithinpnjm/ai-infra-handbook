import xml.etree.ElementTree as ET
import re, json, pathlib

# Let's write a generator script and verify everything against audit_v2 standards
svg_file = "candidate_prefill_decode.svg"

# Let's inspect the spec from specs/p2_20_13.json
spec = json.load(open('specs/p2_20_13.json'))
spec_item = [x for x in spec if x.get('name') == 'p2-2013-prefill-decode-pools'][0]

print("Title:", spec_item['title'])
print("Spec:", spec_item['spec'])

expected_labels = [spec_item['title']] + re.findall(r"'([^']*)'", spec_item['spec'])
print("\nExpected Labels count:", len(expected_labels))
for i, l in enumerate(expected_labels, 1):
    print(f"  {i}. {l}")
