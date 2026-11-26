import xml.etree.ElementTree as ET

# Conservative width check:
# sans: 0.6 * font_size * len
# mono: 0.62 * font_size * len

checks = [
    # (Label, text_line, font_size, is_mono, box_x, box_width, text_anchor, text_x)
    ("Title", "Summing counters before rate hides the restart", 48, False, 0, 1600, "middle", 800),
    ("Left Header", "Wrong: sum first, then rate", 32, False, 50, 720, "start", 145),
    ("Flat line label line 1", "Sum stays flat:", 28, False, 75, 670, "middle", 410),
    ("Flat line label line 2", "the reset is invisible", 28, False, 75, 670, "middle", 410),
    ("Note line 1", "The work pod A did before", 24, False, 75, 670, "middle", 410),
    ("Note line 2", "the restart is lost", 24, False, 75, 670, "middle", 410),
    ("Right Header line 1", "Right: rate per series, then", 30, False, 830, 720, "start", 925),
    ("Right Header line 2", "sum by the labels you keep", 30, False, 830, 720, "start", 925),
    ("Sum box label", "sum by the labels you keep", 28, False, 910, 560, "middle", 1190),
    ("Fleet rate label", "Fleet rate, reset handled per pod", 26, False, 855, 670, "middle", 1190),
    ("Formula mono", "sum by (labels you keep) (rate(counter))", 26, True, 80, 790, "middle", 475),
    ("Bottom note line 1", "Rate per series, sum by the labels", 24, False, 80, 790, "middle", 475),
    ("Bottom note line 2", "you want to keep, then divide.", 24, False, 80, 790, "middle", 475),
    ("Ratio line 1", "Numerator and denominator summed", 24, False, 935, 585, "middle", 1227),
    ("Ratio line 2", "separately, then divided.", 24, False, 935, 585, "middle", 1227),
    ("Ratio line 3", "Never average ratios.", 24, False, 935, 585, "middle", 1227)
]

print("=== CHECKING TEXT PADDING INSIDE BOXES ===")
all_pass = True
for name, line, fs, is_mono, bx, bw, anchor, tx in checks:
    mult = 0.62 if is_mono else 0.6
    est_w = len(line) * mult * fs
    if anchor == "middle":
        t_left = tx - est_w / 2
        t_right = tx + est_w / 2
    elif anchor == "start":
        t_left = tx
        t_right = tx + est_w
    else:
        t_left = tx - est_w
        t_right = tx
    
    pad_left = t_left - bx
    pad_right = (bx + bw) - t_right
    min_pad = min(pad_left, pad_right)
    ok = min_pad >= 16
    if not ok:
        all_pass = False
    print(f"[{'PASS' if ok else 'FAIL'}] {name:20s}: pad_l={pad_left:5.1f}px, pad_r={pad_right:5.1f}px (min={min_pad:5.1f}px, est_w={est_w:5.1f}px, box_w={bw}px) | '{line}'")

assert all_pass, "Some padding checks failed!"
print("\nALL TEXT PADDING CHECKS PASSED WITH >= 16px!")
