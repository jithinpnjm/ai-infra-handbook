import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_service_python.svg")
root = tree.getroot()

print("==================== AUDIT REPORT ====================")

# 1. First children check: <title> and <desc>
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"1. First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"
print("[PASS] <title> and <desc> are first children")

# 2. Dimensions check
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"2. Width: {w}, Height: {h}, viewBox: {vb}")
assert w == "1600", f"Width must be 1600, got {w}"
assert vb == "0 0 1600 1200", f"viewBox must be '0 0 1600 1200', got {vb}"
print("[PASS] Dimensions and viewBox match 1600x1200")

# 3. Text font-sizes: check every text and tspan is >= 24px
font_sizes = []
for el in root.iter():
    if el.tag.endswith('text'):
        fs = int(el.attrib.get('font-size', '0'))
        tspans = [child for child in el if child.tag.endswith('tspan')]
        if tspans:
            for ts in tspans:
                t_content = (ts.text or "").strip()
                t_fs = int(ts.attrib.get('font-size', fs))
                font_sizes.append((t_content, t_fs))
        else:
            t_content = "".join(el.itertext()).strip()
            font_sizes.append((t_content, fs))

print(f"3. Font sizes check ({len(font_sizes)} items):")
for t, fs in font_sizes:
    assert fs >= 24, f"Text '{t}' has font-size {fs} < 24 px!"
print("[PASS] All text elements >= 24 px")

# 4. Extract full text strings per <text> element
full_texts = []
for el in root.iter():
    if el.tag.endswith('text'):
        combined = " ".join("".join(el.itertext()).split())
        full_texts.append(combined)

expected_title = "Why a script works in the shell but fails under cron or systemd"
assert full_texts[0] == expected_title, f"Expected title '{expected_title}', got '{full_texts[0]}'"

source_labels = [
    "Why a script works in the shell but fails under cron or systemd",
    "Your shell",
    "source .venv/bin/activate puts .venv/bin at the front of PATH and sets VIRTUAL_ENV",
    "python resolves to the venv interpreter",
    "import works",
    "cron, systemd or CI",
    "no activation, a different PATH",
    "bare python3 resolves to the system interpreter",
    "ModuleNotFoundError: No module named x",
    "call the interpreter by absolute path: /path/to/.venv/bin/python -m pip install requests; systemd ExecStart=/opt/myops/.venv/bin/myops with Environment=PYTHONUNBUFFERED=1, a dedicated user and ProtectSystem= hardening from chapter 1.15; log sys.executable",
    "which python",
    "python -m pip show x",
    'python -c "import sys; print(sys.prefix, sys.base_prefix)" (they differ inside a venv)',
    "python -m site shows sys.path, user site and whether a venv is active",
    "python -m pip, not bare pip; one environment per project; recreate rather than repair; rebuild after upgrading the base Python since a venv borrows its interpreter; never sudo pip install: PEP 668 externally-managed-environment, use venv, pipx or distribution packages; --system-site-packages weakens isolation",
    "Activation only changes the shell you are sitting in"
]

print(f"\n4. Checking exact source labels:")
print(f"Total full_texts: {len(full_texts)}")
print(f"Total source_labels: {len(source_labels)}")
assert len(full_texts) == len(source_labels), f"Count mismatch: {len(full_texts)} != {len(source_labels)}"

for sl in source_labels:
    cnt = full_texts.count(sl)
    print(f"   [{cnt}] '{sl[:50]}...'")
    assert cnt == 1, f"Expected '{sl}' to appear exactly once, got {cnt}"

print("[PASS] All 16 source labels match 100% exactly and appear once.")

# 5. Check no banned styling words
banned_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for ft in full_texts:
    words = re.findall(r'\b[A-Za-z]+\b', ft.lower())
    for bw in banned_words:
        assert bw not in words, f"Banned styling word '{bw}' found in text: '{ft}'"

print("[PASS] No banned words found in any text element.")

# 6. Check arrows
arrows = [el for el in root.iter() if 'marker-end' in el.attrib or 'marker-start' in el.attrib]
assert len(arrows) == 0, f"Expected 0 arrows, got {len(arrows)}"
print("[PASS] Arrows count = 0 matches source connections = 0.")

print("\nALL SVG CHECKS PASSED!")
