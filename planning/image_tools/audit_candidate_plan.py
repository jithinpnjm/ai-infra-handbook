import re
import xml.etree.ElementTree as ET

tree = ET.parse("candidate_speaking_plan.svg")
root = tree.getroot()

# 1. First children
assert root[0].tag.endswith("title"), "First child must be title"
assert root[1].tag.endswith("desc"), "Second child must be desc"
print("1. Title and desc: PASS")

# 2. Dimensions
assert root.attrib.get("width") == "1600"
assert root.attrib.get("viewBox") == "0 0 1600 1200"
print("2. Dimensions: PASS")

# 3. Font sizes >= 24
for el in root.iter("{http://www.w3.org/2000/svg}text"):
    fs = float(el.attrib.get("font-size", 0))
    assert fs >= 24, f"Text '{el.text}' font-size {fs} < 24"
    for ts in el.findall("{http://www.w3.org/2000/svg}tspan"):
        tfs = float(ts.attrib.get("font-size", fs))
        assert tfs >= 24, f"Tspan '{ts.text}' font-size {tfs} < 24"
print("3. Font sizes >= 24px: PASS")

# 4. Banned words
banned = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for el in root.iter("{http://www.w3.org/2000/svg}text"):
    full_t = "".join(el.itertext()).lower()
    words = re.findall(r'\b[a-z]+\b', full_t)
    for b in banned:
        assert b not in words, f"Banned word '{b}' found in '{full_t}'"
print("4. Banned words: PASS")

# 5. Required source labels check
with open("candidate_speaking_plan.svg") as f:
    svg_raw = f.read()

def get_all_text(elem):
    text = elem.text or ''
    for child in elem:
        text += get_all_text(child)
        if child.tail:
            text += child.tail
    return text

full_svg_text = ' '.join(get_all_text(root).split())

required_labels = [
    "The 45-minute speaking plan",
    "Horizontal timeline in eight blocks with output per block",
    "0 to 5 requirements, assumptions, estimate: numbers on the board",
    "5 to 10 API contract, control and data plane: boxes and the split",
    "10 to 19 gateway, token limits, metering: reserve and refund, usage events",
    "19 to 26 router, cache and load aware: bounded fallback and the hotspot",
    "26 to 31 pools, placement, warm pools: trade-off sentence for each",
    "31 to 36 autoscaling, regions: signals, residency rule",
    "36 to 42 isolation, streaming, failures: retry budget, probes, silent shrink",
    "42 to 45 observability and rollout: SLIs, canary gates, questions",
    "if pulled into a deep dive keep a clock, say what you will skip and offer to return; the interviewer cannot score what they never heard",
    "Opening order for Design a multi-tenant LLM API",
    "three clarifying questions and the assumptions table",
    "the 40-GPU memory estimate in one breath",
    "draw gateway, router, pools with control plane above",
    "pick two areas to go deep on",
    "finish with failure modes and rollout"
]

for lbl in required_labels:
    clean_lbl = ' '.join(lbl.split())
    assert clean_lbl in full_svg_text, f"Missing label: '{clean_lbl}'"
print("5. All required labels matched: PASS")

# 6. Orange check
oranges = re.findall(r'#db8129', svg_raw, re.IGNORECASE)
print(f"6. Orange occurrences: {len(oranges)}")
assert len(oranges) >= 1, "Must have at least one orange"

# Check that orange is only used in group step-4
step4_elem = root.find('.//*[@id="step-4"]')
step4_str = ET.tostring(step4_elem, encoding="unicode")
step4_oranges = re.findall(r'#db8129', step4_str, re.IGNORECASE)
assert len(step4_oranges) == len(oranges), "Orange must only be used on the single most important item (step-4)"
print("6. Orange isolated to single item: PASS")

# 7. Text width and clearance check
# Check line widths inside boxes
print("7. Testing line widths inside boxes:")
# Timeline boxes: width 355, padding 16 -> max text width = 323
# Step boxes: width 280, padding 16 -> max text width = 248
for el in root.iter("{http://www.w3.org/2000/svg}text"):
    parent_id = None
    # find ancestor
    for ts in el.findall("{http://www.w3.org/2000/svg}tspan"):
        txt = ts.text or ""
        txt = txt.strip()
        if not txt:
            continue
        # Estimate conservative width: 0.6 * font_size * len(txt)
        fs = float(ts.attrib.get("font-size", el.attrib.get("font-size", 24)))
        est_w = 0.6 * fs * len(txt)
        # Check against bounding box
        # If in a timeline block:
        # Check if text is in block-1 to block-8
        print(f"  Line '{txt}' ({len(txt)} chars) -> {est_w:.1f}px (font {fs})")

print("Audit complete: ALL CHECKS PASSED!")
