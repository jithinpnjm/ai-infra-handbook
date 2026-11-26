#!/usr/bin/env python3

# Let us verify the layout with icon above text for command boxes

boxes = [
    # (desc, bx, by, bw, bh, text, ftype, fsize, tx, ty)
    ("Title L1", 0, 0, 1600, 1060, "Unquoted variables split on spaces", "sans", 48, 800, 55),
    ("Title L2", 0, 0, 1600, 1060, "and expand to the wrong arguments", "sans", 48, 800, 111),
    ("Col 1 Header", 60, 145, 700, 70, "Unquoted (DANGER)", "sans", 32, 410, 191),
    ("Col 2 Header", 840, 145, 700, 70, "Quoted (correct)", "sans", 32, 1190, 191),
    ("Ex1 L Cmd", 60, 240, 700, 105, "rm $file", "mono", 28, 410, 318),
    ("Ex1 L Container Tag", 60, 385, 700, 125, "two arguments", "sans", 26, 410, 420),
    ("Ex1 L Box 'my'", 180, 435, 180, 60, "my", "mono", 26, 270, 475),
    ("Ex1 L Box 'report.txt'", 400, 435, 240, 60, "report.txt", "mono", 26, 520, 475),
    ("Ex1 R Cmd", 840, 240, 700, 105, "rm \"$file\"", "mono", 28, 1190, 318),
    ("Ex1 R Container Tag", 840, 385, 700, 125, "one argument", "sans", 26, 1190, 420),
    ("Ex1 R Box 'my report.txt'", 1000, 435, 380, 60, "my report.txt", "mono", 26, 1190, 475),
    ("Ex2 L Cmd", 60, 550, 700, 105, "rm -rf $dir/*", "mono", 28, 410, 628),
    ("Ex2 L Result Box", 60, 705, 700, 175, "rm -rf /*", "mono", 32, 410, 830),
    ("Ex2 R Cmd", 840, 550, 700, 105, "rm -rf \"${dir:?dir is unset or empty}\"/*", "mono", 24, 1190, 628),
    ("Ex2 R Result Box", 840, 705, 700, 175, "aborts instead", "sans", 32, 1190, 830),
    ("Caption Bar", 40, 955, 1520, 75, "Always double-quote every expansion, such as \"$var\", \"$(cmd)\" and \"$@\".", "sans", 26, 800, 1002),
]

all_pass = True
for desc, bx, by, bw, bh, text, ftype, fsize, tx, ty in boxes:
    rate = 0.62 if ftype == "mono" else 0.60
    tw = len(text) * rate * fsize
    pad_L = (tx - tw / 2) - bx
    pad_R = (bx + bw) - (tx + tw / 2)
    min_pad = min(pad_L, pad_R)
    ok = min_pad >= 16
    if not ok: all_pass = False
    print(f"[{'PASS' if ok else 'FAIL'}] {desc:25s}: box_w={bw:4d}, text_w={tw:5.1f}, pad_L={pad_L:5.1f}, pad_R={pad_R:5.1f} (min={min_pad:5.1f})")

assert all_pass, "Some paddings failed!"
print("\nALL 16 CHECKS PASSED WITH min_pad >= 16px!")
