#!/usr/bin/env python3

def check_text_fits(lines, box_w, fs, is_mono=False, pad=16):
    factor = 0.62 if is_mono else 0.60
    usable = box_w - 2 * pad
    all_fit = True
    for l in lines:
        w = len(l) * fs * factor
        fits = w <= usable
        if not fits:
            all_fit = False
        print(f"  [{'PASS' if fits else 'FAIL'}] w={w:5.1f}px (usable={usable:5.1f}px): '{l}'")
    return all_fit

print("--- Testing Row Descriptions in Box W = 960 px ---")
rows = [
    ("Row 1", [
        "removes the longest matching prefix up to the last slash:",
        "result 'model.final.ckpt' (same as basename)"
    ]),
    ("Row 2", [
        "removes the shortest matching suffix starting at the last slash:",
        "result '/data/run42' (same as dirname)"
    ]),
    ("Row 3", [
        "removes the shortest suffix starting at the last dot:",
        "result '/data/run42/model.final'"
    ]),
    ("Row 4", [
        "removes the longest prefix up to the last dot:",
        "result 'ckpt'"
    ])
]

for name, lines in rows:
    print(name + ":")
    check_text_fits(lines, 960, 24, False, 16)

print("\n--- Testing Side Key in Box W = 480 px ---")
key_items = [
    ("Key 1", [
        "# / ## remove shortest /",
        "longest prefix"
    ]),
    ("Key 2", [
        "% / %% remove shortest /",
        "longest suffix"
    ]),
    ("Key 3", [
        "${#path} length"
    ])
]

for name, lines in key_items:
    print(name + ":")
    check_text_fits(lines, 480, 24, False, 20)
