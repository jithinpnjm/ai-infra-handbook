#!/usr/bin/env python3

def check_card2_wrap(lines, start_x, card_w, card_x, fs=24):
    coeff = 0.60
    card_end = card_x + card_w
    print(f"Card 2: x={card_x}..{card_end} (w={card_w})")
    all_ok = True
    for i, line in enumerate(lines, 1):
        w = len(line) * fs * coeff
        end_x = start_x + w
        pad_right = card_end - end_x
        pad_left = start_x - card_x
        ok = pad_right >= 16 and pad_left >= 16
        print(f"  Line {i}: '{line}' | w={w:.1f}px, end_x={end_x:.1f}px, pad_right={pad_right:.1f}px [{'OK' if ok else 'FAIL'}]")
        if not ok: all_ok = False
    return all_ok

check_card2_wrap([
    "uid identifies",
    "one instance; a recreated",
    "object gets a new uid"
], start_x=650, card_w=460, card_x=590)
