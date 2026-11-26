# Let's test revised card bounding boxes and paddings:

cards = [
    {
        "name": "Row A Container",
        "box": (40, 270, 1520, 260),
        "lines": [("Start sector 2048 (1 MiB)", 30, False, 140, 328, "left")]
    },
    {
        "name": "Row A Verdict",
        "box": (1340, 285, 200, 74),
        "lines": [("aligned", 30, False, 1440, 332, "middle")]
    },
    {
        "name": "Row A Math Card",
        "box": (65, 365, 870, 66),
        "lines": [("2048 / 8 = 256, a whole number, remainder 0", 25, True, 85, 407, "left")]
    },
    {
        "name": "Row A Boundary Card",
        "box": (65, 445, 870, 66),
        "lines": [("the partition boundary line sits exactly on a page edge", 24, False, 85, 487, "left")]
    },
    {
        "name": "Row B Container",
        "box": (40, 550, 1520, 320),
        "lines": [("cat /sys/block/sdf/sdf2/start prints 1953126", 28, True, 140, 608, "left")]
    },
    {
        "name": "Row B Verdict",
        "box": (1290, 565, 250, 74),
        "lines": [("NOT aligned", 30, False, 1415, 612, "middle")]
    },
    {
        "name": "Row B Math Card",
        "box": (65, 642, 1010, 66),
        "lines": [("1953126 / 8 = 244140.75, remainder 6", 25, True, 85, 684, "left")]
    },
    {
        "name": "Row B Boundary Card",
        "box": (65, 720, 1010, 66),
        "lines": [("the partition boundary line falls inside a page, six sectors in", 24, False, 85, 762, "left")]
    },
    {
        "name": "Row B Straddle Card",
        "box": (65, 796, 1010, 66),
        "lines": [("a single 4 KiB read straddles two physical pages", 24, False, 85, 838, "left")]
    },
    {
        "name": "Left Note Box",
        "box": (40, 890, 730, 165),
        "lines": [
            ("Why 8: eight 512-byte sectors", 24, False, 140, 960, "left"),
            ("make one 4,096-byte page", 24, False, 140, 996, "left")
        ]
    },
    {
        "name": "Right Box Tool",
        "box": (800, 890, 760, 165),
        "lines": [
            ("Check with a tool:", 24, True, 900, 945, "left"),
            ("parted /dev/sdb align-check", 24, True, 900, 979, "left"),
            ("optimal 1 prints 1 aligned", 24, True, 900, 1013, "left")
        ]
    },
    {
        "name": "Bottom Bar",
        "box": (40, 1085, 1520, 75),
        "lines": [("Existing partitions are not realigned by the tools, so check them yourself", 26, False, 800, 1132, "middle")]
    }
]

all_pass = True
for c in cards:
    bx, by, bw, bh = c["box"]
    for text, fs, is_mono, tx, ty, anchor in c["lines"]:
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
        
        pad_left = x_min - bx
        pad_right = (bx + bw) - x_max
        pad_top = y_min - by
        pad_bottom = (by + bh) - y_max
        
        min_pad = min(pad_left, pad_right, pad_top, pad_bottom)
        ok = min_pad >= 16.0
        if not ok:
            all_pass = False
        print(f"[{'PASS' if ok else 'FAIL'}] {c['name']} ('{text[:30]}...'): min={min_pad:5.1f}px (L={pad_left:5.1f}, R={pad_right:5.1f}, T={pad_top:5.1f}, B={pad_bottom:5.1f})")

assert all_pass
print("\nALL REVISED PADDINGS PASSED STRICTLY >= 16px!")
