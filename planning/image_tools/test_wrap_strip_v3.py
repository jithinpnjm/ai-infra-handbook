strip_lines = [
    ("Vector([3, 4, 5]) + (10, 20) and (10, 20) + Vector([3, 4, 5]) both give", 24, False),
    ("Vector([13.0, 24.0, 5.0]) using zip_longest(self, other, fillvalue=0.0)", 24, False),
    ("and __radd__ = __add__; adding 1 is rejected cleanly by returning NotImplemented", 24, False),
    ("in except TypeError; Vector([1, 2, 3]) @ Vector([4, 5, 6]) == 32.0", 24, False),
    ("after checking isinstance(other, abc.Sized) and Iterable; if __iadd__ is missing,", 24, False),
    ("v1 += v2 falls back to v1 = v1 + v2 and changes id(v1),", 24, False),
    ("while a mutable class returns self", 24, False)
]

mw = 1250
for l, fs, mono in strip_lines:
    factor = 0.62 if mono else 0.60
    w = len(l) * fs * factor
    print(f"{w:6.1f} px (len {len(l)}): {l}")
    assert w <= mw

print("Strip fits in 7 lines under 1250px!")
