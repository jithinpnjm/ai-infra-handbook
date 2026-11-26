#!/usr/bin/env python3

def calc_card(by, n_lines, dy, fs):
    y1 = round(by + 18 + 0.8 * fs)
    y_last = round(y1 + (n_lines - 1) * dy)
    last_bottom = y_last + 0.2 * fs
    bh = round(last_bottom - by + 18)
    
    top_pad = (y1 - 0.8 * fs) - by
    bot_pad = (by + bh) - (y_last + 0.2 * fs)
    return y1, bh, top_pad, bot_pad

print("Card 1 (3 lines, dy=30, fs=24):", calc_card(240, 3, 30, 24))
print("Card 2 (4 lines, dy=30, fs=24):", calc_card(376, 4, 30, 24))
print("Card 3 (1 line,  dy=30, fs=24):", calc_card(536, 1, 30, 24))
print("Card 4 (2 lines, dy=30, fs=24):", calc_card(612, 2, 30, 24))
