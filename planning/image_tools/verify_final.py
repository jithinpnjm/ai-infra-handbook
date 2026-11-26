import xml.etree.ElementTree as ET

tree = ET.parse("chainmap_final.svg")
root = tree.getroot()

expected_labels = [
    'ChainMap layering and read-only views for configuration',
    'cli_args',
    'os.environ (MYOPS_ prefixed, lowercased)',
    'file_cfg (/etc/myops.json)',
    'defaults {retries: 3, timeout: 30}',
    'cfg["timeout"]',
    'first mapping wins',
    'ChainMap({retries: 5}, {retries: 3, timeout: 10}): cfg[retries] is 5, cfg[timeout] is 10',
    'a write such as chain[c] = -1 changes only the first mapping',
    'CLI values of None are dropped so they do not hide lower layers: {k: v for k, v in cli.items() if v is not None}',
    'Related views',
    'types.MappingProxyType(d) is a read-only view that still reflects later updates to d, so callers cannot change a hardware pin map while the owner keeps it current',
    'dict.keys() and dict.items() are live views with no copying and support & | - ^',
    'Python scope lookup uses the same idea: ChainMap(locals(), globals(), vars(builtins))',
    'merge: a | b, {**a, **b}, or ChainMap; a deep merge needs recursion',
    'dicts compare equal regardless of key order, lists are order-sensitive',
    'Use ChainMap when the first mapping should win, without copying'
]

text_elements = root.findall(".//{http://www.w3.org/2000/svg}text")
extracted_texts = []
font_sizes = []

for elem in text_elements:
    full_text = "".join(elem.itertext())
    normalized = " ".join(full_text.split())
    extracted_texts.append(normalized)
    fs = elem.get("font-size")
    if fs:
        font_sizes.append(float(fs))
    for tspan in elem.findall(".//{http://www.w3.org/2000/svg}tspan"):
        tfs = tspan.get("font-size")
        if tfs:
            font_sizes.append(float(tfs))

found_counts = {lbl: 0 for lbl in expected_labels}
for text in extracted_texts:
    for lbl in expected_labels:
        if text == " ".join(lbl.split()):
            found_counts[lbl] += 1
            break

all_good = True
for lbl, count in found_counts.items():
    if count != 1:
        print(f"COUNT MISMATCH: '{lbl}' has count {count}")
        all_good = False

print(f"Label count verification: {'PERFECT (all 17 exact)' if all_good else 'FAILED'}")
print(f"Min font size: {min(font_sizes)}px (all >= 24px: {min(font_sizes) >= 24.0})")

