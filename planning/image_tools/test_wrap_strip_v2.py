strip_lines = [
    ("Vector([3, 4, 5]) + (10, 20) and (10, 20) + Vector([3, 4, 5]) both give", 24, False),
    ("Vector([13.0, 24.0, 5.0]) using zip_longest(self, other, fillvalue=0.0) and __radd__ = __add__;", 24, False),
    ("adding 1 is rejected cleanly by returning NotImplemented in except TypeError;", 24, False),
    ("Vector([1, 2, 3]) @ Vector([4, 5, 6]) == 32.0 after checking isinstance(other, abc.Sized)", 24, False),
    ("and Iterable; if __iadd__ is missing, v1 += v2 falls back to v1 = v1 + v2 and changes id(v1),", 24, False),
    ("while a mutable class returns self", 24, False)
]

mw = 1380
for l, fs, mono in strip_lines:
    factor = 0.62 if mono else 0.60
    w = len(l) * fs * factor
    print(f"{w:6.1f} px (len {len(l)}): {l}")
    assert w <= mw

print("Strip fits in 6 lines under 1380px!")
