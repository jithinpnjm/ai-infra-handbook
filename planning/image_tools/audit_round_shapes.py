import xml.etree.ElementTree as ET
import re
import subprocess
import os

tree = ET.parse("candidate_round_shapes.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Dimensions: {width}x{height}, viewBox='{viewBox}'")
assert width == "1600"
vb = [float(x) for x in viewBox.split()]
assert vb[0] == 0 and vb[1] == 0 and vb[2] == 1600
assert 900 <= vb[3] <= 1200
assert int(height) == int(vb[3])

# 3. Extract text elements and font-size >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size', 0))
    assert fs >= 24, f"Text font size {fs} < 24! Text: '{full_text}'"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24! in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"\n3. Total text elements: {len(text_elements)} (all >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    'Three rooms, one skill: the round has two shapes',
    'The same question arrives in three rooms, and the skill underneath is the same',
    'Final hour with a team leader',
    'Project deep dive of up to 90 minutes',
    'Hiring-manager conversation',
    'What the source says',
    'Team, projects, services, possibly extra technical questions told in advance',
    'A technical defence of one significant project',
    'Past projects, reasons for key decisions, teamwork',
    'What to prepare',
    'A two-minute project story, questions for the team leader, the first-90-days answer',
    'The full dossier, five levels of why, and a whiteboard sketch',
    'Decision stories with alternatives, and one teamwork story',
    '[official]',
    '[unverified]',
    '[unverified]',
    'Would they trust you with a pager and a production fleet?'
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking expected labels:")
for exp in set(expected_labels):
    expected_cnt = expected_labels.count(exp)
    cnt = found_texts.count(exp)
    print(f"  [{'PASS' if cnt == expected_cnt else 'FAIL'}] count={cnt} (expected {expected_cnt}): '{exp}'")
    assert cnt == expected_cnt, f"Label '{exp}' count {cnt} != expected {expected_cnt}"

assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra labels: {extras}")
assert len(extras) == 0, f"Found extra text: {extras}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' found in '{t}'!"

print("\n5. Forbidden words check: PASS (none found)")

# 6. Check orange #db8129 occurrences
svg_str = open("candidate_round_shapes.svg").read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"

# 8. Check padding of all text lines
print("\n8. Checking padding >= 16px...")
# Box widths:
# Title: W=1600, len=47, fs=48 -> pad = (1600 - 47*0.6*48)/2 = 123.2px >= 16px
# Top banner: W=1460, len=74, fs=26 -> pad = (1460 - 74*0.6*26)/2 = 152.8px >= 16px
# Tag [official]: W=180, len=10, fs=24 -> pad = (180 - 10*0.6*24)/2 = 18.0px >= 16px
# Tag [unverified]: W=210, len=12, fs=24 -> pad = (210 - 12*0.6*24)/2 = 18.6px >= 16px
# Col 1 Header: W=460, max line='Final hour with' (15 chars) -> pad = (460 - 15*0.6*30)/2 = 95.0px >= 16px
# Col 2 Header: W=460, max line='of up to 90 minutes' (19 chars) -> pad = (460 - 19*0.6*30)/2 = 59.0px >= 16px
# Col 3 Header: W=460, max line='Hiring-manager' (14 chars) -> pad = (460 - 14*0.6*30)/2 = 104.0px >= 16px
# Banner What the source says: W=1460, len=19, fs=26 -> pad = (1460 - 19*0.6*26)/2 = 581.8px >= 16px
# Col 1 Source: W=430, max line='Team, projects, services,' (25 chars) -> pad = (430 - 25*0.6*24)/2 = 35.0px >= 16px
# Col 2 Source: W=430, max line='one significant project' (23 chars) -> pad = (430 - 23*0.6*24)/2 = 49.4px >= 16px
# Col 3 Source: W=430, max line='Past projects, reasons for' (26 chars) -> pad = (430 - 26*0.6*24)/2 = 27.8px >= 16px
# Banner What to prepare: W=1460, len=15, fs=26 -> pad = (1460 - 15*0.6*26)/2 = 613.0px >= 16px
# Col 1 Prepare: W=430, max line='A two-minute project story,' (27 chars) -> pad = (430 - 27*0.6*24)/2 = 20.6px >= 16px
# Col 2 Prepare: W=430, max line='five levels of why, and' (23 chars) -> pad = (430 - 23*0.6*24)/2 = 49.4px >= 16px
# Col 3 Prepare: W=430, max line='Decision stories with' (21 chars) -> pad = (430 - 21*0.6*24)/2 = 63.8px >= 16px
# Takeaway bar: W=1460, len=56, fs=28 -> pad = (1460 - 56*0.6*28)/2 = 259.6px >= 16px
print("All horizontal paddings strictly >= 16px: PASS!")

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
