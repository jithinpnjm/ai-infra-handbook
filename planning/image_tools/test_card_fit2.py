def est_w(s, fs=24, is_mono=False):
    return len(s) * (0.62 if is_mono else 0.60) * fs

step3 = [
    ("3 expander picks among groups:", False),
    ("random picks any, least-waste leaves", False),
    ("the fewest empty seats, most-pods", False),
    ("carries the most waiting pods", False)
]

print("Testing Step 3 (4 lines):")
for l, is_m in step3:
    w = est_w(l, 24, is_m)
    fits = w <= 650
    print(f"  [{w:5.1f} / 650 | {'OK' if fits else 'FAIL'}] {l}")
    assert fits
print("Step 3 PASS!")
