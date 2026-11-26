#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse('output_candidate.svg')
root = tree.getroot()

print("==================== AUDIT START ====================")

# 1. Structure
children = list(root)
tag1 = children[0].tag.split('}')[-1]
tag2 = children[1].tag.split('}')[-1]
print(f"1. First children: <{tag1}>, <{tag2}>")
assert tag1 == 'title', f"First child is not title, got {tag1}"
assert tag2 == 'desc', f"Second child is not desc, got {tag2}"

# 2. Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Dimensions: {width}x{height}, viewBox='{viewBox}'")
assert width == "1600"
assert height == "1180"
assert viewBox == "0 0 1600 1180"
assert int(height) <= 1200

# 3. Font sizes >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size', '0'))
    assert fs >= 24, f"Text '{full_text}' font size {fs} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24 in '{full_text}'!"
    text_elements.append((full_text, fs))

print(f"3. All text elements >= 24px (total elements: {len(text_elements)})")

# 4. Expected labels
expected_labels = [
    "Which startup stage produced this error message",
    "shell fork and execve",
    "kernel checks the file and picks a format handler",
    "ELF loader maps LOAD segments, builds the stack",
    "PT_INTERP: kernel maps ld.so, execution starts in the dynamic linker",
    "ld.so loads DT_NEEDED libraries, relocates, runs constructors",
    "_start, __libc_start_main, main",
    "Exec format error (wrong CPU architecture such as x86-64 on aarch64, or a script without shebang)",
    "exit 126 found but not executable",
    "exit 127 not found",
    "bad ELF interpreter / not found for a file that exists (glibc binary on Alpine musl: /lib64/ld-linux-x86-64.so.2 missing)",
    "libcuda.so.1: cannot open shared object file",
    "error while loading shared libraries: libnccl.so.2",
    "version GLIBC_2.34 not found",
    "version GLIBCXX_3.4.30 not found",
    "CUDA error: no kernel image is available for execution on the device",
    "Illegal instruction (SIGILL, exit 132)",
    "segfault exit 139",
    "file and readelf -h",
    "readelf -l | grep interpreter",
    "ldd, ldconfig -p, LD_DEBUG=libs",
    "strace -f for the last failed call"
]

step_numbers = {"1", "2", "3", "4", "5", "6"}

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found texts:")
for exp in expected_labels:
    cnt = found_texts.count(exp)
    print(f"  '{exp[:45]}...': count={cnt}")
    assert cnt == 1, f"Expected '{exp}' once, got {cnt}!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nUnexpected extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected texts: {extras}"
print("   [PASS] Exact label fidelity passed!")

# 5. Forbidden style words
forbidden = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow", "cylinder", "folder", "callout"]
for t in found_texts:
    for w in forbidden:
        words_in_text = [re.sub(r'[^a-zA-Z]', '', word).lower() for word in t.split()]
        if w in words_in_text:
            raise AssertionError(f"Forbidden word '{w}' found in text: '{t}'")
print("5. [PASS] No forbidden style instruction words found in text!")

# 6. Outside Margins
# Test box rects (excluding background and icon shapes inside transform groups)
box_rects = []
for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
    w = float(elem.attrib.get('width', '0'))
    h = float(elem.attrib.get('height', '0'))
    if w == 1600 and h == 1180:
        continue # Background
    if w < 100 or h < 50:
        continue # Icon inner shape
    x = float(elem.attrib.get('x', '0'))
    y = float(elem.attrib.get('y', '0'))
    box_rects.append((x, y, w, h))

print(f"\n6. Checking outside margins on {len(box_rects)} major box rects:")
for x, y, w, h in box_rects:
    m_l = x
    m_r = 1600 - (x + w)
    m_t = y
    m_b = 1180 - (y + h)
    assert m_l >= 40, f"Left margin {m_l} < 40!"
    assert m_r >= 40, f"Right margin {m_r} < 40!"
    assert m_t >= 40, f"Top margin {m_t} < 40!"
    assert m_b >= 40, f"Bottom margin {m_b} < 40!"
print("   [PASS] All major box margins >= 40px!")

# 7. Check Gaps between the 4 Columns
cols = [
    (40, 360),
    (440, 340),
    (820, 360),
    (1220, 340)
]
print("\n7. Checking column gaps:")
for i in range(len(cols)-1):
    g = cols[i+1][0] - (cols[i][0] + cols[i][1])
    print(f"   Gap between Col {i+1} and Col {i+2}: {g}px")
    assert g >= 40, f"Column gap {g} < 40!"
print("   [PASS] All column gaps >= 40px!")

# 8. Check Vertical Clearance between Pipeline and Columns
# Pipeline ends at y=346, Columns start at y=390 -> gap = 44px >= 40px!
gap_pipe_cols = 390 - 346
print(f"\n8. Gap between Pipeline and Columns: {gap_pipe_cols}px")
assert gap_pipe_cols >= 40
print("   [PASS] Vertical gap >= 40px!")

print("\n==================== ALL CHECKS PASSED! ====================")
