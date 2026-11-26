#!/usr/bin/env python3

def calc_box(y_start, num_lines, dy=30, fs=24):
    text_span = (num_lines - 1) * dy + fs
    # we want top_pad >= 16 and bottom_pad >= 16
    # top = y1 - 0.8 * fs
    # we want y1 - 0.8 * fs - y_start >= 16  => y1 >= y_start + 16 + 0.8 * fs
    y1 = y_start + 17 + 0.8 * fs
    # bottom = y1 + (num_lines - 1) * dy + 0.2 * fs
    bottom = y1 + (num_lines - 1) * dy + 0.2 * fs
    # box_h >= bottom + 17 - y_start
    box_h = int(bottom + 17 - y_start) + 2
    return y1, box_h

for n in [1, 2, 3]:
    y1, h = calc_box(100, n)
    top_pad = (y1 - 0.8 * 24) - 100
    bot_pad = (100 + h) - (y1 + (n - 1) * 30 + 0.2 * 24)
    print(f"{n} lines: h={h}, y1={y1:.1f}, top_pad={top_pad:.1f}, bot_pad={bot_pad:.1f}")
