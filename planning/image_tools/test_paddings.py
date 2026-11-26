#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def test_paddings():
    # Boxes:
    # 1. Title: x=800, y=52, fs=48, bold
    # 2. Legend container: x=520, y=82, w=560, h=44
    # 3. Matrix container: x=40, y=166, w=1140, h=650
    #    Col 0 (Action): x=40..340, w=300
    #    Col 1 (mtime): x=340..620, w=280
    #    Col 2 (ctime): x=620..900, w=280
    #    Col 3 (atime): x=900..1180, w=280
    #
    # Rows:
    # Header: y=166..296 (h=130)
    # Row 1: y=296..386 (h=90)
    # Row 2: y=386..476 (h=90)
    # Row 3: y=476..576 (h=100)
    # Row 4: y=576..666 (h=90)
    # Row 5: y=666..816 (h=150)
    #
    # Right box: x=1220..1560 (w=340), y=166..816 (h=650)
    # Bottom bar: x=40..1560 (w=1520), y=856..930 (h=74)

    # Let's verify every line width and horizontal padding >= 16px:
    text_checks = [
        # (name, text, fs, font_type, box_x, box_w, text_anchor, text_x)
        # Legend:
        ("Legend changes", "changes", 25, "sans", 520, 560, "start", 635),
        ("Legend unchanged", "unchanged", 25, "sans", 520, 560, "start", 855),
        
        # Col headers:
        ("Header mtime 1", "mtime ", 26, "sans", 340, 280, "middle", 480),
        ("Header mtime 2", "(contents ", 26, "sans", 340, 280, "middle", 480),
        ("Header mtime 3", "written)", 26, "sans", 340, 280, "middle", 480),
        
        ("Header ctime 1", "ctime ", 26, "sans", 620, 280, "middle", 760),
        ("Header ctime 2", "(inode ", 26, "sans", 620, 280, "middle", 760),
        ("Header ctime 3", "changed)", 26, "sans", 620, 280, "middle", 760),

        ("Header atime 1", "atime ", 26, "sans", 900, 280, "middle", 1040),
        ("Header atime 2", "(file read)", 26, "sans", 900, 280, "middle", 1040),

        # Action commands:
        ("Row 1 cmd", "echo more >> f1", 25, "mono", 40, 300, "start", 65),
        ("Row 2 cmd", "chmod 600 f1", 25, "mono", 40, 300, "start", 65),
        ("Row 3 cmd", "cat f1", 25, "mono", 40, 300, "start", 65),
        ("Row 4 cmd", "ln f1 f2", 25, "mono", 40, 300, "start", 65),
        ("Row 5 cmd 1", "touch -d ", 24, "mono", 40, 300, "start", 65),
        ("Row 5 cmd 2", '"2026-01-01 ', 24, "mono", 40, 300, "start", 65),
        ("Row 5 cmd 3", '12:00" f1', 24, "mono", 40, 300, "start", 65),

        # Row 3 cell text:
        ("Row 3 atime", "rarely: relatime", 24, "sans", 900, 280, "middle", 1040),

        # Row 5 ctime cell text:
        ("Row 5 ctime 1", "ctime still ", 24, "sans", 620, 280, "middle", 760),
        ("Row 5 ctime 2", "moves, ", 24, "sans", 620, 280, "middle", 760),
        ("Row 5 ctime 3", "cannot be set", 24, "sans", 620, 280, "middle", 760),

        # Right box lines:
        ("Right box 1", "stat shows ", 25, "sans", 1220, 340, "middle", 1390),
        ("Right box 2", "all three; ", 25, "sans", 1220, 340, "middle", 1390),
        ("Right box 3", "ls -l shows mtime, ", 25, "sans", 1220, 340, "middle", 1390),
        ("Right box 4", "ls -lc ctime, ", 25, "sans", 1220, 340, "middle", 1390),
        ("Right box 5", "ls -lu atime", 25, "sans", 1220, 340, "middle", 1390),

        # Bottom bar:
        ("Bottom bar", "ctime is not the creation time", 30, "sans", 40, 1520, "middle", 800),
    ]

    print("=== Checking Horizontal Paddings (>= 16px) ===")
    all_ok = True
    for name, text, fs, ftype, bx, bw, anchor, tx in text_checks:
        cwidth = 0.62 * fs if ftype == "mono" else 0.6 * fs
        tlen = len(text) * cwidth
        if anchor == "middle":
            x_left = tx - tlen / 2
            x_right = tx + tlen / 2
        else:
            x_left = tx
            x_right = tx + tlen
        pad_left = x_left - bx
        pad_right = (bx + bw) - x_right
        ok = (pad_left >= 16 and pad_right >= 16)
        if not ok:
            all_ok = False
        print(f"[{'PASS' if ok else 'FAIL'}] {name:16s} len={tlen:5.1f} pad_l={pad_left:5.1f} pad_r={pad_right:5.1f} in box [{bx}..{bx+bw}]")

    assert all_ok, "Some text lines failed horizontal padding check!"
    print("\nALL HORIZONTAL PADDINGS PASS (>= 16px)!")

if __name__ == '__main__':
    test_paddings()
