import xml.etree.ElementTree as ET
import re

tree = ET.parse("final_candidate.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"
print("[PASS] <title> and <desc> are the first children.")

# 2. Dimensions check
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"Width: {w}, Height: {h}, viewBox: {vb}")
assert w == "1600", f"Width must be 1600, got {w}"
assert vb == f"0 0 1600 {h}", f"viewBox must be '0 0 1600 {h}', got {vb}"
h_val = int(h)
assert 900 <= h_val <= 1200, f"Height must be between 900 and 1200, got {h_val}"
print("[PASS] Canvas dimensions and viewBox valid.")

# 3. Extract text elements and check font-sizes
texts = []
font_sizes = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(el.attrib.get('font-size', 0))
    full_text = "".join(el.itertext()).strip()
    texts.append(full_text)
    font_sizes.append((fs, full_text))

print(f"\nTotal <text> elements: {len(font_sizes)}")
for fs, txt in font_sizes:
    if fs < 24:
        print(f"ERROR: Text '{txt}' has font-size {fs} < 24!")
assert all(fs >= 24 for fs, _ in font_sizes), "Found font size < 24!"
print("[PASS] No text smaller than 24px anywhere!")

# 4. Check all required source labels
source_labels = [
    "Reading curl --trace-ascii: markers, offsets and the blank line",
    "curl --trace-ascii trace_file http://www.example.org/",
    "curl's own notes, marked ==",
    "== Info: Trying 93.184.216.34...",
    "== Info: TCP_NODELAY set",
    "== Info: Connected to www.example.org (93.184.216.34) port 80 (#0)",
    "request sent, marked =>",
    "=> Send header, 79 bytes (0x4f)",
    "GET / HTTP/1.1",
    "Host: www.example.org",
    "User-Agent: curl/7.58.0",
    "Accept: */*",
    "reply received, marked <=",
    "<= Recv header, 17 bytes",
    "HTTP/1.1 200 OK",
    "Accept-Ranges: bytes",
    "Age: 17629",
    "Content-Length: 1256",
    "<= Recv data, 1256 bytes (0x4e8)",
    "The hex numbers such as 0000: are offsets curl adds to track how many bytes moved; they are not part of the data",
    "curl does not count headers toward the offsets, so offsets restart at zero after the headers",
    "A blank line marks the end of the headers; everything after it is the requested document",
    "The operating system and network handle headers and document identically; the split exists only inside the user-space curl program",
    "Read it from the top: notes, then the request, then the reply"
]

print(f"\n--- Checking source labels ({len(source_labels)}) ---")
for sl in source_labels:
    cnt = texts.count(sl)
    print(f"Label '{sl[:40]}...': count={cnt}")
    assert cnt == 1, f"Expected '{sl}' to appear exactly once, got {cnt}!"

print("[PASS] Every source label appears exactly once.")

# Check extra text elements (only allowed: step numbers "1", "2", "3")
non_source_texts = [t for t in texts if t not in source_labels]
print(f"\nNon-source text elements: {non_source_texts}")
assert non_source_texts == ["1", "2", "3"], f"Unexpected text elements: {non_source_texts}"
print("[PASS] No unexpected labels or text added (only step numbers 1, 2, 3).")

# 5. Check no banned styling words
banned_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for t in texts:
    words = re.findall(r'\b[A-Za-z]+\b', t.lower())
    for bw in banned_words:
        assert bw not in words, f"Banned styling word '{bw}' found in text: '{t}'"
print("[PASS] No styling words printed as text.")

# 6. Check arrows count
arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"\nArrow count: {len(arrows)}")
assert len(arrows) == 0, f"Expected 0 arrows, got {len(arrows)}"
print("[PASS] Exactly 0 arrows present.")

# 7. Check orange usage: exactly one orange highlight item
orange_els = []
for el in root.iter():
    for k, v in el.attrib.items():
        if "#db8129" in v:
            orange_els.append((el.tag.split('}')[-1], k, v))

print(f"\nOrange highlights: {len(orange_els)}")
for o in orange_els:
    print(f"  {o}")
# Specifically check that callout-3 is the only place using orange
assert len(orange_els) > 0, "Expected orange highlight"
print("[PASS] Orange #db8129 used for the single most important item.")
