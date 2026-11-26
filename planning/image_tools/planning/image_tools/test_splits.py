#!/usr/bin/env python3

def test_split(lines, max_w, is_mono=True, fs=24):
    factor = 0.62 if is_mono else 0.60
    for l in lines:
        w = len(l) * factor * fs
        print(f"  '{l}': {w:.1f}px (fits in {max_w}? {w <= max_w - 32})")

print("--- Card 4 in 350px box (max_w=350, max content = 318px) ---")
test_split([
    "kubectl debug -it ",
    "trainer-0 ",
    "--image=nicolaka/",
    "netshoot ",
    "--target=pytorch"
], 350)
