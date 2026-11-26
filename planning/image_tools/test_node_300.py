nodes = [
    ("IDLE", 230, 215, 300, 90, "IDLE", "sans", 32, 415, 271),
    ("ALLOCATED", 1070, 215, 300, 90, "ALLOCATED", "sans", 32, 1255, 271),
    ("DRAINED", 230, 515, 300, 90, "DRAINED", "sans", 32, 415, 571),
    ("DRAINING", 1070, 515, 300, 90, "DRAINING", "sans", 32, 1255, 571),
    ("DOWN", 750, 900, 300, 90, "DOWN", "sans", 32, 935, 956),
]

all_ok = True
for desc, bx, by, bw, bh, text, ftype, fs, tx, ty in nodes:
    rate = 0.60
    tw = len(text) * rate * fs
    icon_end = bx + 18 + 48
    gap_icon = (tx - tw / 2) - icon_end
    pad_R = (bx + bw) - (tx + tw / 2)
    pad_T = (ty - fs * 0.75) - by
    pad_B = (by + bh) - ty
    min_pad = min(gap_icon, pad_R, pad_T, pad_B)
    ok = min_pad >= 16.0
    if not ok: all_ok = False
    print(f"[{'PASS' if ok else 'FAIL'}] {desc:12s}: gap_icon={gap_icon:4.1f}, pad_R={pad_R:4.1f}, pad_T={pad_T:4.1f}, pad_B={pad_B:4.1f} (min={min_pad:4.1f})")

assert all_ok, "Node check failed!"
print("\nALL STATE NODES PASSED min_pad >= 16.0px!")
