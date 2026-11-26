#!/usr/bin/env python3

boxes = [
    ("Title L1", 0, 0, 1600, 1060, "Unquoted variables split on spaces", "sans", 48, 800, 55),
    ("Title L2", 0, 0, 1600, 1060, "and expand to the wrong arguments", "sans", 48, 800, 111),
    ("Col 1 Header", 60, 145, 700, 70, "Unquoted (DANGER)", "sans", 32, 430, 191),
    ("Col 2 Header", 840, 145, 700, 70, "Quoted (correct)", "sans", 32, 1210, 191),
    ("Ex1 L Cmd", 60, 235, 700, 95, "rm $file", "mono", 28, 410, 294),
    ("Ex1 L Container Tag", 60, 365, 700, 145, "two arguments", "sans", 26, 410, 405),
    ("Ex1 L Box 'my'", 180, 430, 180, 60, "my", "mono", 26, 270, 470),
    ("Ex1 L Box 'report.txt'", 400, 430, 240, 60, "report.txt", "mono", 26, 520, 470),
    ("Ex1 R Cmd", 840, 235, 700, 95, "rm \"$file\"", "mono", 28, 1190, 294),
    ("Ex1 R Container Tag", 840, 365, 700, 145, "one argument", "sans", 26, 1190, 405),
    ("Ex1 R Box 'my report.txt'", 1000, 430, 380, 60, "my report.txt", "mono", 26, 1190, 470),
    ("Ex2 L Cmd", 60, 545, 700, 105, "rm -rf $dir/*", "mono", 28, 410, 610),
    ("Ex2 L Result Box", 60, 695, 700, 205, "rm -rf /*", "mono", 34, 410, 835),
    ("Ex2 R Cmd", 840, 545, 700, 105, "rm -rf \"${dir:?dir is unset or empty}\"/*", "mono", 24, 1190, 626),
    ("Ex2 R Result Box", 840, 695, 700, 205, "aborts instead", "sans", 32, 1190, 835),
    ("Caption Bar", 40, 950, 1520, 75, "Always double-quote every expansion, such as \"$var\", \"$(cmd)\" and \"$@\".", "sans", 26, 800, 997),
]

all_pass = True
for desc, bx, by, bw, bh, text, ftype, fsize, tx, ty in boxes:
    rate = 0.62 if ftype == "mono" else 0.60
    tw = len(text) * rate * fsize
    pad_L = (tx - tw / 2) - bx
    pad_R = (bx + bw) - (tx + tw / 2)
    pad_T = (ty - fsize * 0.75) - by
    pad_B = (by + bh) - ty
    min_pad_h = min(pad_L, pad_R)
    min_pad_v = min(pad_T, pad_B)
    min_pad = min(min_pad_h, min_pad_v)
    ok = min_pad >= 16
    if not ok: all_pass = False
    print(f"[{'PASS' if ok else 'FAIL'}] {desc:25s}: pad_H={min_pad_h:5.1f}, pad_V={min_pad_v:5.1f} (min={min_pad:5.1f})")

assert all_pass, "Some paddings failed!"
print("\nALL 16 CHECKS PASSED HORIZONTALLY AND VERTICALLY (min_pad >= 16px)!")
