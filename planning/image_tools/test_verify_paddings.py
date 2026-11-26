import re
import xml.etree.ElementTree as ET

tree = ET.parse("test_output.svg")
root = tree.getroot()

def est_width(text, fs, mono=False):
    factor = 0.62 if mono else 0.60
    return len(text) * fs * factor

print("=== CHECKING ALL TEXT PADDINGS ===")

# 1. Title
tw = est_width("awk group-by: an associative array counts as the lines pass", 48, False)
print(f"Title: len={len('awk group-by: an associative array counts as the lines pass')}, width={tw:.1f}px")

# 2. Left panel headers
c1 = est_width("column 1", 24, False)
c2 = est_width("column 2", 24, False)
print(f"column 1: {c1:.1f}px in 117px cell -> padding {(117-c1)/2:.1f}px")
print(f"column 2: {c2:.1f}px in 117px cell -> padding {(117-c2)/2:.1f}px")

# 3. Snapshots
for s in ["after line 1", "after line 3", "after line 5"]:
    sw = est_width(s, 30, False)
    print(f"Step '{s}': {sw:.1f}px")

for val in ["alice = 1", "alice = 2, bob = 1", "alice = 3, bob = 2"]:
    vw = est_width(val, 26, True)
    print(f"Val '{val}': {vw:.1f}px in 474px box -> padding {474-vw:.1f}px")

# 4. END text
end_title = est_width("END { for (k in c) print c[k], k }", 24, True)
print(f"END title: {end_title:.1f}px in (1560-1095)={465}px -> padding {465-end_title:.1f}px")
runs = est_width("runs once after the last line", 24, False)
print(f"runs once: {runs:.1f}px in 560px box -> padding {(560-runs)/2:.1f}px")

# 5. Output cards in comparison panel
for o in ["1 alice", "1 bob", "2 alice", "1 bob"]:
    ow = est_width(o, 26, True)
    print(f"A card '{o}': {ow:.1f}px in 140px box -> padding {(140-ow)/2:.1f}px")

for o in ["3 alice", "2 bob"]:
    ow = est_width(o, 30, True)
    print(f"B card '{o}': {ow:.1f}px in 260px box -> padding {(260-ow)/2:.1f}px")

# 6. Bottom bar
bw = est_width("An associative array is a lookup table keyed by text, so no sort | uniq -c is needed", 26, False)
print(f"Bottom bar: {bw:.1f}px in 1520px box -> padding {(1520-bw)/2:.1f}px")

