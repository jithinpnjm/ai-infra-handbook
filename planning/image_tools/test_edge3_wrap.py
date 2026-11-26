#!/usr/bin/env python3

edge3_lines = [
    "import brings an object",
    "created by hand into state so",
    "apply does not collide; plan",
    "only knows what is in state"
]

box_w = 480
for i, l in enumerate(edge3_lines):
    w = len(l) * 0.60 * 24
    pad = (box_w - w) / 2
    print(f"Line {i+1}: len={len(l):2d}, w={w:5.1f}px, pad={pad:4.1f}px [{'OK' if pad>=16 else 'FAIL'}] '{l}'")

full = " ".join(edge3_lines)
print("\nReconstructed full text:")
print(f"'{full}'")
expected = "import brings an object created by hand into state so apply does not collide; plan only knows what is in state"
print(f"Matches expected: {full == expected}")
