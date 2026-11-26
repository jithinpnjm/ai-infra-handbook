# Tune all box heights and y-coordinates so ALL paddings >= 16.5px and all inter-box gaps >= 40px:

# Available vertical height:
# Canvas: 1600 x 1200
# Outside margins: 40px top, 40px bottom
# Title: baseline 1 at 86, baseline 2 at 138 (top is 45.2, bottom is 150)
# Gap to Top Strip: 38px -> Top Strip y=188

# Strip: y=188, h=78 (ends at 266)
# Gap to Row A: 40px -> Row A y=306

# Row A: y=306, h=232 (ends at 538)
#   Title: y=355
#   Verdict: y=320, h=68, text y=362
#   Math: y=390, h=62, text y=428 (L=20, R=183.5, T=16.8, B=18.8)
#   Boundary: y=460, h=62, text y=498 (L=20, R=58, T=17.6, B=18.0)

# Gap to Row B: 40px -> Row B y=578

# Row B: y=578, h=282 (ends at 860)
#   Title: y=624
#   Verdict: y=590, h=68, text y=632
#   Math: y=654, h=60, text y=691 (L=20, R=432, T=15.8 -> adjust ty=692: T=16.8, B=16.8 for h=60!)
#     Wait: fs=25 -> y_min = ty - 21.25, y_max = ty + 6.25.
#     If box_y=654, h=61:
#       ty=692:
#       y_min = 692 - 21.25 = 670.75 -> top pad = 670.75 - 654 = 16.75px
#       y_max = 692 + 6.25 = 698.25 -> bottom pad = 715 - 698.25 = 16.75px!
#   Boundary: y=722, h=60, text y=760:
#     fs=24 -> y_min = 760 - 20.4 = 739.6 -> top pad = 739.6 - 722 = 17.6px
#     y_max = 760 + 6 = 766 -> bottom pad = 782 - 766 = 16.0px (make h=61 -> 17.0px)
#   Straddle: y=790, h=60, text y=828:
#     fs=24 -> y_min = 828 - 20.4 = 807.6 -> top pad = 807.6 - 790 = 17.6px
#     y_max = 828 + 6 = 834 -> bottom pad = 850 - 834 = 16.0px (make h=61 -> 17.0px)

# Gap to Notes: 40px -> Notes y=900, h=145 (ends at 1045)
# Gap to Bottom Bar: 40px -> Bottom Bar y=1085, h=75 (ends at 1160)
# Margin bottom: 1200 - 1160 = 40px!

def test_box_padding(name, bx, by, bw, bh, lines):
    all_ok = True
    print(f"\nChecking {name} [box: ({bx}, {by}, {bw}, {bh})]:")
    for text, fs, is_mono, tx, ty, anchor in lines:
        char_w = 0.62 * fs if is_mono else 0.6 * fs
        tw = len(text) * char_w
        if anchor == "middle":
            x_min = tx - tw / 2
            x_max = tx + tw / 2
        else:
            x_min = tx
            x_max = tx + tw
        y_min = ty - fs * 0.85
        y_max = ty + fs * 0.25
        
        pad_l = x_min - bx
        pad_r = (bx + bw) - x_max
        pad_t = y_min - by
        pad_b = (by + bh) - y_max
        min_p = min(pad_l, pad_r, pad_t, pad_b)
        ok = min_p >= 16.0
        if not ok:
            all_ok = False
        print(f"  [{'PASS' if ok else 'FAIL'}] '{text[:32]}...' min={min_p:4.1f}px (L={pad_l:4.1f}, R={pad_r:4.1f}, T={pad_t:4.1f}, B={pad_b:4.1f})")
    return all_ok

checks = [
    ("Row A Container", 40, 306, 1520, 232, [("Start sector 2048 (1 MiB)", 30, False, 140, 355, "left")]),
    ("Row A Verdict", 1340, 320, 200, 68, [("aligned", 30, False, 1440, 362, "middle")]),
    ("Row A Math", 65, 388, 870, 62, [("2048 / 8 = 256, a whole number, remainder 0", 25, True, 85, 426, "left")]),
    ("Row A Boundary", 65, 458, 870, 62, [("the partition boundary line sits exactly on a page edge", 24, False, 85, 496, "left")]),
    ("Row B Container", 40, 578, 1520, 282, [("cat /sys/block/sdf/sdf2/start prints 1953126", 28, True, 140, 624, "left")]),
    ("Row B Verdict", 1290, 590, 250, 68, [("NOT aligned", 30, False, 1415, 632, "middle")]),
    ("Row B Math", 65, 654, 1010, 61, [("1953126 / 8 = 244140.75, remainder 6", 25, True, 85, 692, "left")]),
    ("Row B Boundary", 65, 722, 1010, 61, [("the partition boundary line falls inside a page, six sectors in", 24, False, 85, 760, "left")]),
    ("Row B Straddle", 65, 790, 1010, 61, [("a single 4 KiB read straddles two physical pages", 24, False, 85, 828, "left")]),
    ("Left Note", 40, 900, 730, 145, [
        ("Why 8: eight 512-byte sectors", 24, False, 140, 955, "left"),
        ("make one 4,096-byte page", 24, False, 140, 995, "left")
    ]),
    ("Right Note", 800, 900, 760, 145, [
        ("Check with a tool:", 24, True, 900, 942, "left"),
        ("parted /dev/sdb align-check", 24, True, 900, 976, "left"),
        ("optimal 1 prints 1 aligned", 24, True, 900, 1010, "left")
    ]),
    ("Bottom Bar", 40, 1085, 1520, 75, [("Existing partitions are not realigned by the tools, so check them yourself", 26, False, 800, 1132, "middle")])
]

all_pass = True
for name, bx, by, bw, bh, lines in checks:
    if not test_box_padding(name, bx, by, bw, bh, lines):
        all_pass = False

print("\n=== OVERALL RESULT ===")
print("ALL PASS:", all_pass)
