import xml.etree.ElementTree as ET

tree = ET.parse("final_svg.svg")
root = tree.getroot()

# 1. Labels check
required_labels = [
    "Three habits that waste time, and the method that replaces them",
    "Streetlight: use the tools you know or that are easy, where the light is good (running top because you know it)",
    "finds an issue, not the issue",
    "Random change: change tunables until it improves and keep what looks better",
    "unexplained, fragile, may encode workarounds, risk at peak",
    "Blame-someone-else: hypothesise a component you do not own and hand it over without data",
    "wastes other teams; a ticket bounces for a week; demand screenshots of tools run",
    "Problem statement (always first)",
    "Scientific method: question, hypothesis, prediction, test, analysis",
    "Diagnosis cycle: hypothesis, instrumentation, data, hypothesis, quickly so bad theories die early",
    "Observational: watch the system while it runs",
    "Experimental: change one thing; if it does nothing, revert it before the next hypothesis",
    "Negative: deliberately worsen something to confirm a cause",
    "A method fixes the order of the questions, so your favourite tool comes after the evidence",
]

def get_element_text(elem):
    parts = []
    if elem.text:
        parts.append(elem.text.strip())
    for child in elem:
        parts.append(get_element_text(child))
        if child.tail:
            parts.append(child.tail.strip())
    return " ".join([p for p in parts if p])

full_text = " ".join([get_element_text(el) for el in root.iter('{http://www.w3.org/2000/svg}text')])
clean_full = " ".join(full_text.split())

# Check each required label in text
print("=== REQUIRED LABELS CHECK ===")
for lab in required_labels:
    # clean spaces in lab
    clean_lab = " ".join(lab.split())
    # remove step numbers 1, 2, 3 if comparing
    if clean_lab in clean_full:
        print(f"FOUND: {lab[:40]}...")
    else:
        print(f"NOT DIRECTLY FOUND: {lab}")

# Check arrows
arrows = [el for el in root.iter() if el.attrib.get('marker-end')]
print(f"\nArrow count: {len(arrows)} (expected: 2)")

# Check font sizes
small_fonts = []
for el in root.iter():
    if 'font-size' in el.attrib:
        fs = float(el.attrib['font-size'])
        if fs < 24:
            small_fonts.append((el.tag, el.text, fs))
print(f"Small fonts (<24px): {small_fonts}")

# Check boxes and gaps
boxes = [
    ('card1', 40, 140, 600, 265),
    ('card2', 40, 445, 600, 265),
    ('card3', 40, 750, 600, 310),
    ('node1', 680, 140, 880, 135),
    ('node2', 680, 315, 420, 575),
    ('test1', 1140, 315, 420, 135),
    ('test2', 1140, 490, 420, 195),
    ('test3', 1140, 725, 420, 165),
    ('node3', 680, 930, 880, 130),
    ('bottom', 40, 1100, 1520, 60),
]

print("\n=== GAP CHECKS ===")
print("Card 1 -> Card 2 gap:", 445 - (140 + 265))
print("Card 2 -> Card 3 gap:", 750 - (445 + 265))
print("Card 3 -> Bottom gap:", 1100 - (750 + 310))
print("Node 1 -> Node 2 gap:", 315 - (140 + 135))
print("Node 2 -> Node 3 gap:", 930 - (315 + 575))
print("Node 3 -> Bottom gap:", 1100 - (930 + 130))
print("Test 1 -> Test 2 gap:", 490 - (315 + 135))
print("Test 2 -> Test 3 gap:", 725 - (490 + 195))
print("Left col -> Right col gap:", 680 - (40 + 600))
print("Right col 1 -> Right col 2 gap:", 1140 - (680 + 420))
print("Bottom margin:", 1200 - (1100 + 60))
print("Left margin:", 40)
print("Right margin:", 1600 - (1140 + 420))
