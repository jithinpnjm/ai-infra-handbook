#!/usr/bin/env python3

def calc_width(text, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * factor * fs

lines = [
    ("kubectl debug -it trainer-0 ", 27, True),
    ("--image=nicolaka/netshoot ", 26, True),
    ("--target=pytorch", 16, True),
]

for l, c, m in lines:
    w = calc_width(l, 24, m)
    print(f"'{l}': {w:.1f}px (need box at least {w + 32:.1f}px)")
