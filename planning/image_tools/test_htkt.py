#!/usr/bin/env python3

text = "how to keep them together"
fs = 30
w = len(text) * 0.60 * fs
print(f"Text width: {w} px")
x = 1085
rx = 1020
rw = 540
pad_left = x - rx
pad_right = (rx + rw) - (x + w)
print(f"pad_left: {pad_left} px, pad_right: {pad_right} px")
assert pad_left >= 16
assert pad_right >= 16
print("PASS!")
