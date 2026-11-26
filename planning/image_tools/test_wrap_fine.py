# Let's test lines with width <= 1250 px for maximum safety and elegance

step2 = [
    ("2 slice-aware __getitem__:", 30, False),
    ("if isinstance(key, slice): return type(self)(self._components[key]); else", 24, False),
    ("operator.index(key), which calls __index__ and raises TypeError for floats or tuples;", 24, False),
    ("slice.indices(length) normalizes bounds; SkipObject returns a new iterator from each", 24, False),
    ("__iter__ call so [x + y for x in skipper for y in skipper] makes 9 pairs from aa to ee,", 24, False),
    ("while Squares returns self from __iter__ and scans only once", 24, False)
]

for l, fs, mono in step2:
    factor = 0.62 if mono else 0.60
    w = len(l) * fs * factor
    print(f"{w:6.1f} px: {l}")
    assert w <= 1260

print("Step 2 wrapped cleanly!")
