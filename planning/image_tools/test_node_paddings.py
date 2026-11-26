# Node boxes: width 280, height 90
# Inside each node box:
# Icon: width 54px, placed at bx + 20
# Text: node title at tx, ty
# Let's test padding:
nodes = [
    ("IDLE", 240, 215, 280, 90, "IDLE", "sans", 32, 415, 271),
    ("ALLOCATED", 1080, 215, 280, 90, "ALLOCATED", "sans", 32, 1250, 271),
    ("DRAINED", 240, 515, 280, 90, "DRAINED", "sans", 32, 415, 571),
    ("DRAINING", 1080, 515, 280, 90, "DRAINING", "sans", 32, 1250, 571),
    ("DOWN", 760, 900, 280, 90, "DOWN", "sans", 32, 925, 956),
]

for desc, bx, by, bw, bh, text, ftype, fs, tx, ty in nodes:
    rate = 0.60
    tw = len(text) * rate * fs
    # Icon ends at bx + 20 + 54 = bx + 74
    # Gap from icon to text:
    gap_icon = (tx - tw / 2) - (bx + 74)
    pad_R = (bx + bw) - (tx + tw / 2)
    pad_T = (ty - fs * 0.75) - by
    pad_B = (by + bh) - ty
    min_pad = min(gap_icon, pad_R, pad_T, pad_B)
    ok = min_pad >= 16.0
    print(f"[{'PASS' if ok else 'FAIL'}] {desc:12s}: gap_icon={gap_icon:4.1f}, pad_R={pad_R:4.1f}, pad_T={pad_T:4.1f}, pad_B={pad_B:4.1f} (min={min_pad:4.1f})")

