step5 = [
    ("5 operators: __neg__, __pos__, __add__, __radd__, __mul__, __rmul__,", 30, False),
    ("__matmul__, __rmatmul__, __contains__, __iadd__;", 24, True),
    ("format h for hyperspherical coordinates", 24, False)
]

for l, fs, mono in step5:
    factor = 0.62 if mono else 0.60
    w = len(l) * fs * factor
    print(f"{w:6.1f} px (len {len(l)}): {l}")
    assert w <= 1250

print("Step 5 wrapped cleanly!")
