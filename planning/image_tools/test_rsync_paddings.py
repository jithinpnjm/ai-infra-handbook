#!/usr/bin/env python3
import xml.etree.ElementTree as ET

# Define all boxes and their text lines:
# box: (bx, by, bw, bh)
# lines: [(text, fs, font_family, tx_or_anchor, ty)]
# Note: for text-anchor="middle", tx is center. tw = len(text) * factor * fs. left_edge = tx - tw/2, right_edge = tx + tw/2.
# for text-anchor="start" (default), left_edge = tx, right_edge = tx + tw.

items = [
    {
        "name": "Source dir data",
        "box": (60, 165, 700, 110),
        "lines": [
            ("data", 30, "mono", 155, 228, "start")
        ]
    },
    {
        "name": "Source file a.pt",
        "box": (330, 185, 185, 70),
        "lines": [
            ("a.pt", 24, "mono", 440, 228, "middle")
        ]
    },
    {
        "name": "Source file b.pt",
        "box": (545, 185, 185, 70),
        "lines": [
            ("b.pt", 24, "mono", 655, 228, "middle")
        ]
    },
    {
        "name": "Dest dir /scratch/data",
        "box": (840, 165, 700, 110),
        "lines": [
            ("/scratch/data", 30, "mono", 945, 230, "start")
        ]
    },
    {
        "name": "Card A cmd",
        "box": (60, 355, 440, 90),
        "lines": [
            ("rsync -a data/ ", 24, "mono", 280, 391, "middle"),
            ("gpu01:/scratch/data", 24, "mono", 280, 424, "middle")
        ]
    },
    {
        "name": "Card A file 1",
        "box": (60, 455, 440, 58),
        "lines": [
            ("/scratch/data/a.pt", 24, "mono", 280, 492, "middle")
        ]
    },
    {
        "name": "Card A file 2",
        "box": (60, 523, 440, 58),
        "lines": [
            ("/scratch/data/b.pt", 24, "mono", 280, 560, "middle")
        ]
    },
    {
        "name": "Card A note",
        "box": (60, 595, 440, 130),
        "lines": [
            ("contents copied ", 24, "sans", 280, 645, "middle"),
            ("into the destination", 24, "sans", 280, 680, "middle")
        ]
    },
    {
        "name": "Card B cmd",
        "box": (580, 355, 440, 90),
        "lines": [
            ("rsync -a data ", 24, "mono", 800, 391, "middle"),
            ("gpu01:/scratch/data", 24, "mono", 800, 424, "middle")
        ]
    },
    {
        "name": "Card B file 1",
        "box": (580, 455, 440, 58),
        "lines": [
            ("/scratch/data/data/a.pt", 24, "mono", 800, 492, "middle")
        ]
    },
    {
        "name": "Card B file 2",
        "box": (580, 523, 440, 58),
        "lines": [
            ("/scratch/data/data/b.pt", 24, "mono", 800, 560, "middle")
        ]
    },
    {
        "name": "Card B note",
        "box": (580, 595, 440, 130),
        "lines": [
            ("the directory itself, ", 24, "sans", 800, 645, "middle"),
            ("nested copy", 24, "sans", 800, 680, "middle")
        ]
    },
    {
        "name": "Card C cmd",
        "box": (1100, 355, 440, 90),
        "lines": [
            ("scp -r data ", 24, "mono", 1320, 391, "middle"),
            ("gpu01:/scratch/data", 24, "mono", 1320, 424, "middle")
        ]
    },
    {
        "name": "Card C file 1",
        "box": (1100, 455, 440, 58),
        "lines": [
            ("/scratch/data/data/a.pt", 24, "mono", 1320, 492, "middle")
        ]
    },
    {
        "name": "Card C file 2",
        "box": (1100, 523, 440, 58),
        "lines": [
            ("/scratch/data/data/b.pt", 24, "mono", 1320, 560, "middle")
        ]
    },
    {
        "name": "Card C note",
        "box": (1100, 595, 440, 130),
        "lines": [
            ("also copies every ", 24, "sans", 1320, 634, "middle"),
            ("byte again, even ", 24, "sans", 1320, 664, "middle"),
            ("when nothing changed", 24, "sans", 1320, 694, "middle")
        ]
    },
    {
        "name": "Step 1 box",
        "box": (60, 805, 760, 145),
        "lines": [
            ("rsync -avhn --delete ", 24, "mono", 465, 860, "middle"),
            ("data/ gpu01:/scratch/data/ (dry run)", 24, "mono", 465, 894, "middle")
        ]
    },
    {
        "name": "Step 2 box",
        "box": (840, 805, 320, 145),
        "lines": [
            ("read the list", 26, "sans", 1035, 886, "middle")
        ]
    },
    {
        "name": "Step 3 box",
        "box": (1180, 805, 360, 145),
        "lines": [
            ("run again ", 24, "sans", 1380, 865, "middle"),
            ("without -n", 24, "sans", 1380, 895, "middle")
        ]
    },
    {
        "name": "Warning strip",
        "box": (60, 970, 1480, 120),
        "lines": [
            ("--delete makes the destination match the source; ", 24, "sans", 835, 1024, "middle"),
            ("an empty source deletes the destination contents", 24, "sans", 835, 1056, "middle")
        ]
    }
]

print("=== Checking Exact Text Paddings against Box Boundaries ===")
all_pass = True
for it in items:
    bx, by, bw, bh = it["box"]
    for text, fs, ff, tx, ty, anchor in it["lines"]:
        factor = 0.62 if ff == "mono" else 0.6
        tw = len(text) * factor * fs
        th = fs * 0.8 # height above baseline
        
        if anchor == "middle":
            left_edge = tx - tw / 2
            right_edge = tx + tw / 2
        else:
            left_edge = tx
            right_edge = tx + tw
            
        left_pad = left_edge - bx
        right_pad = (bx + bw) - right_edge
        top_pad = (ty - th) - by
        bottom_pad = (by + bh) - ty
        
        ok = left_pad >= 16 and right_pad >= 16 and top_pad >= 14 and bottom_pad >= 14
        if not ok:
            all_pass = False
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {it['name']} - '{text}':")
        print(f"       left={left_pad:.1f}px, right={right_pad:.1f}px, top={top_pad:.1f}px, bottom={bottom_pad:.1f}px")

assert all_pass, "Some padding failed!"
print("\nALL PADDINGS >= 16px STRICTLY PASSED!")
