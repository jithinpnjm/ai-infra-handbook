#!/usr/bin/env python3

def test_centered_col1():
    # Col 1: x = 55 to 345 (width = 290, center = 200)
    # Row height = 118 px (e.g. y = 175 to 293)
    # Inner rect: x = 55, y = 181, w = 290, h = 106
    # Icon: cx = 200, cy = 212, size = 44x44 (x: 178..222, y: 190..234)
    # Title: y = 265 (font-size 26 bold, cap-height ~18px, y: 247..265)
    # Top pad of icon: 190 - 181 = 9px. If inner rect y=177: 190 - 177 = 13px.
    # What if row height = 124 px?
    # Let's calculate:
    titles = [
        ("Resource", 28),
        ("ContainerResource", 24),
        ("Pods", 28),
        ("Object", 28),
        ("External", 28)
    ]
    for name, fs in titles:
        w = len(name) * 0.6 * fs
        left = 200 - w / 2
        right = 200 + w / 2
        pad_l = left - 55
        pad_r = 345 - right
        print(f"{name:18s} (fs={fs}): w={w:5.1f} | left_pad={pad_l:4.1f}, right_pad={pad_r:4.1f} | min_pad={min(pad_l, pad_r):4.1f}")

test_centered_col1()
