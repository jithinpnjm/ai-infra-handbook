step3 = [
    ("3 dynamic read-only attributes x, y, z, t through __match_args__", 30, False),
    ("and __getattr__ reading self._components[0..3];", 24, False),
    ("trap: v.x = 10 creates v.__dict__[x], which shadows __getattr__", 24, False),
    ("while v[0] stays unchanged; fix: __setattr__ raises AttributeError", 24, False),
    ("for single lowercase letters a to z; allowed writes use", 24, False),
    ("super().__setattr__(attr, val) to avoid infinite recursion", 24, False)
]

for l, fs, mono in step3:
    factor = 0.62 if mono else 0.60
    w = len(l) * fs * factor
    print(f"{w:6.1f} px (len {len(l)}): {l}")
    assert w <= 1200

print("Step 3 wrapped beautifully and safely under 1200 px!")
