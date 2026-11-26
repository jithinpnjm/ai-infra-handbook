step4 = [
    ("4 hashing: functools.reduce(operator.xor, (hash(x) for x in self), 0),", 30, False),
    ("initializer 0 covers empty vectors; streaming equality len(self) == len(other)", 24, False),
    ("and all(a == b for a, b in zip(self, other)) in O(1) extra memory", 24, False)
]

for l, fs, mono in step4:
    factor = 0.62 if mono else 0.60
    w = len(l) * fs * factor
    print(f"{w:6.1f} px (len {len(l)}): {l}")
    assert w <= 1260

print("Step 4 wrapped cleanly!")
