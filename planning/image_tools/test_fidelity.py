import xml.etree.ElementTree as ET
import re

tree = ET.parse("output.svg")
root = tree.getroot()

# Function to extract all visible text strings from SVG
def get_texts(elem):
    texts = []
    # If element is text or tspan
    tag = elem.tag.split('}')[-1]
    if tag == 'text':
        # Check if it has tspans
        tspans = [c for c in elem if c.tag.split('}')[-1] == 'tspan']
        if tspans:
            full = " ".join([re.sub(r'\s+', ' ', "".join(t.itertext())).strip() for t in tspans])
            texts.append(full)
        else:
            full = re.sub(r'\s+', ' ', "".join(elem.itertext())).strip()
            texts.append(full)
    else:
        for child in elem:
            texts.extend(get_texts(child))
    return texts

found_texts = get_texts(root)
print(f"Total <text> elements found: {len(found_texts)}")
for i, t in enumerate(found_texts, 1):
    print(f"{i:2d}: {t}")

expected = [
    "Tracing one host through the /etc/hosts template",
    "# {{ ansible_managed }}",
    "first line marks the file as generated so nobody edits it by hand",
    "127.0.0.1 localhost",
    "second line keeps the loopback address",
    "for h in groups[cluster] | sort",
    "the loop writes one line per host in sorted order: the sort keeps the output the same on every render",
    "{{ hostvars[h][ansible_host] }} {{ h }}.{{ cluster_domain }} {{ h }}",
    "each line uses the host's ansible_host and its name, so the file follows the inventory: add a host to the inventory, run the playbook, and the new line appears without anyone touching the file",
    "endfor",
    "inventory entry gpu001 with its ansible_host value, and the cluster_domain variable",
    "the ansible_host value, then gpu001 followed by the cluster_domain value, then gpu001",
    "cross-host data needs facts for those hosts: see the --limit trap",
    "Trace one value from the data to the output line"
]

print("\n--- Matching Check ---")
all_matched = True
for exp in expected:
    match = False
    for f in found_texts:
        if f == exp:
            match = True
            break
    if match:
        print(f"MATCH: {exp[:50]}...")
    else:
        print(f"MISSING: {exp}")
        all_matched = False

print(f"\nAll matched? {all_matched}")
print(f"Counts equal? {len(found_texts) == len(expected)}")
