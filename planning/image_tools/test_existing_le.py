import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate_le.svg")
root = tree.getroot()

# Check text elements
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = elem.attrib.get('font-size')
    tsp_sizes = [tsp.attrib.get('font-size') for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan')]
    text_elements.append((full_text, fs, tsp_sizes))

print(f"Total text elements: {len(text_elements)}")
for i, (t, fs, tsps) in enumerate(text_elements, 1):
    print(f"{i:2d}. text fs={fs}, tspans={tsps} -> '{t}'")

expected_labels = [
    "Histogram buckets: keep le, then take the quantile once",
    "Each box counts every request at or under its bound: cumulative",
    "histogram_quantile interpolates inside the bucket that holds the quantile",
    "Trap: sum by (model) drops le",
    "Breaks histogram_quantile",
    "Right: sum by (le, model)",
    "Keep le in the by clause, then take the quantile once",
    "Pod A buckets",
    "Pod B buckets",
    "rate per series",
    "sum by (le, model)",
    "histogram_quantile(0.99)",
    "le stands for less than or equal to."
]

found_texts = [t for t, fs, tsps in text_elements]
print("\n--- Expected labels check ---")
for exp in expected_labels:
    cnt = found_texts.count(exp)
    print(f"[{'OK' if cnt==1 else 'FAIL'}] count={cnt}: '{exp}'")

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtras: {extras}")
