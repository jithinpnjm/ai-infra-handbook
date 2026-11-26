import xml.etree.ElementTree as ET

tree = ET.parse("test_timeline.svg")
root = tree.getroot()

# Rule: sans 0.60 * fs, mono 0.62 * fs. Min padding 16px.
# Let us check every rect that contains a text element:
# We have participant boxes, step boxes, note box.

print("=== CHECKING PADDINGS OF ALL RECTS AND TEXTS ===")

# Check participant boxes: width=216, fs=30.
# Max text length in participant boxes:
# "controller": 10 chars -> 10 * 30 * 0.6 = 180px. Pad = (216 - 180)/2 = 18px >= 16px.
# "API server": 10 chars -> 180px. Pad = 18px >= 16px.
# "containerd": 10 chars -> 180px. Pad = 18px >= 16px.
# "Scheduler": 9 chars -> 162px. Pad = (216 - 162)/2 = 27px >= 16px.
# "CSI node": 8 chars -> 144px. Pad = (216 - 144)/2 = 36px >= 16px.

participant_lines = [
    ("User /", 30, 216),
    ("controller", 30, 216),
    ("Scheduler", 30, 216),
    ("containerd", 30, 216),
    ("(CRI)", 30, 216),
    ("CSI node", 30, 216),
    ("plugin", 30, 216),
    ("runc /", 30, 216),
    ("kernel", 30, 216),
    ("API server", 30, 216),
    ("(+etcd)", 30, 216),
    ("Kubelet", 30, 216),
    ("CNI", 30, 216),
    ("Device", 30, 216),
]

for txt, fs, bw in participant_lines:
    w = len(txt) * fs * 0.60
    pad = (bw - w) / 2
    assert pad >= 16.0, f"FAIL: '{txt}' in participant box has pad {pad:.1f} < 16"
    print(f"  [Participant] pad={pad:5.1f}px (w={w:5.1f}/{bw}px): '{txt}'")

print("\nAll participant boxes passed padding checks (pad >= 18px)!")

# Check step message boxes:
# Step rects have width bw, and contain txt.
rects = {}
for g in root.iter('{http://www.w3.org/2000/svg}g'):
    gid = g.attrib.get('id', '')
    if gid.startswith('step-') or gid == 'note-running':
        rect = g.find('{http://www.w3.org/2000/svg}rect')
        text = g.find('{http://www.w3.org/2000/svg}text')
        if rect is not None and text is not None:
            rw = float(rect.attrib['width'])
            fs = float(text.attrib['font-size'])
            tspans = list(text.iter('{http://www.w3.org/2000/svg}tspan'))
            if tspans:
                for tsp in tspans:
                    txt = tsp.text.strip()
                    w = len(txt) * fs * 0.60
                    pad = (rw - w) / 2
                    assert pad >= 16.0, f"FAIL in {gid}: '{txt}' has pad {pad:.1f} < 16 in width {rw}"
                    print(f"  [{gid:14s}] pad={pad:5.1f}px (w={w:5.1f}/{rw}px): '{txt}'")
            else:
                txt = "".join(text.itertext()).strip()
                w = len(txt) * fs * 0.60
                pad = (rw - w) / 2
                assert pad >= 16.0, f"FAIL in {gid}: '{txt}' has pad {pad:.1f} < 16 in width {rw}"
                print(f"  [{gid:14s}] pad={pad:5.1f}px (w={w:5.1f}/{rw}px): '{txt}'")

print("\nALL STEP RECT PADDING CHECKS PASSED (pad >= 16px everywhere)!")
