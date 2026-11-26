def check_line(text, font_size=24, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * font_size * factor

max_w = 1320 # safe limit for 1335px box

# Step 1
s1 = [
    ("1 short __repr__ with reprlib.repr:", 30, False),
    ("Vector(range(1000)) is truncated, like Vector([0.0, 1.0, 2.0, 3.0, 4.0, ...])", 24, True)
]

# Step 2
# Original text: '2 slice-aware __getitem__: if isinstance(key, slice): return type(self)(self._components[key]); else operator.index(key), which calls __index__ and raises TypeError for floats or tuples; slice.indices(length) normalizes bounds; SkipObject returns a new iterator from each __iter__ call so [x + y for x in skipper for y in skipper] makes 9 pairs from aa to ee, while Squares returns self from __iter__ and scans only once'
s2 = [
    ("2 slice-aware __getitem__:", 30, False),
    ("if isinstance(key, slice): return type(self)(self._components[key]);", 24, True),
    ("else operator.index(key), which calls __index__ and raises TypeError for floats or tuples;", 24, False),
    ("slice.indices(length) normalizes bounds; SkipObject returns a new iterator from each", 24, False),
    ("__iter__ call so [x + y for x in skipper for y in skipper] makes 9 pairs from aa to ee,", 24, False),
    ("while Squares returns self from __iter__ and scans only once", 24, False)
]

# Step 3
# Original text: '3 dynamic read-only attributes x, y, z, t through __match_args__ and __getattr__ reading self._components[0..3]; trap: v.x = 10 creates v.__dict__[x], which shadows __getattr__ while v[0] stays unchanged; fix: __setattr__ raises AttributeError for single lowercase letters a to z; allowed writes use super().__setattr__(attr, val) to avoid infinite recursion'
s3 = [
    ("3 dynamic read-only attributes x, y, z, t through __match_args__ and", 30, False),
    ("__getattr__ reading self._components[0..3];", 30, False),
    ("trap: v.x = 10 creates v.__dict__[x], which shadows __getattr__ while v[0] stays unchanged;", 24, False),
    ("fix: __setattr__ raises AttributeError for single lowercase letters a to z;", 24, False),
    ("allowed writes use super().__setattr__(attr, val) to avoid infinite recursion", 24, False)
]

# Step 4
# Original text: '4 hashing: functools.reduce(operator.xor, (hash(x) for x in self), 0), initializer 0 covers empty vectors; streaming equality len(self) == len(other) and all(a == b for a, b in zip(self, other)) in O(1) extra memory'
s4 = [
    ("4 hashing: functools.reduce(operator.xor, (hash(x) for x in self), 0),", 30, False),
    ("initializer 0 covers empty vectors; streaming equality len(self) == len(other) and", 24, False),
    ("all(a == b for a, b in zip(self, other)) in O(1) extra memory", 24, False)
]

# Step 5
# Original text: '5 operators: __neg__, __pos__, __add__, __radd__, __mul__, __rmul__, __matmul__, __rmatmul__, __contains__, __iadd__; format h for hyperspherical coordinates'
s5 = [
    ("5 operators: __neg__, __pos__, __add__, __radd__, __mul__, __rmul__,", 30, False),
    ("__matmul__, __rmatmul__, __contains__, __iadd__; format h for hyperspherical coordinates", 24, False)
]

# Strip:
# Original text: 'Vector([3, 4, 5]) + (10, 20) and (10, 20) + Vector([3, 4, 5]) both give Vector([13.0, 24.0, 5.0]) using zip_longest(self, other, fillvalue=0.0) and __radd__ = __add__; adding 1 is rejected cleanly by returning NotImplemented in except TypeError; Vector([1, 2, 3]) @ Vector([4, 5, 6]) == 32.0 after checking isinstance(other, abc.Sized) and Iterable; if __iadd__ is missing, v1 += v2 falls back to v1 = v1 + v2 and changes id(v1), while a mutable class returns self'
# Strip width: box from x=40 to 1560 (width 1520), text area width = 1440
strip_lines = [
    ("Vector([3, 4, 5]) + (10, 20) and (10, 20) + Vector([3, 4, 5]) both give Vector([13.0, 24.0, 5.0])", 24, True),
    ("using zip_longest(self, other, fillvalue=0.0) and __radd__ = __add__; adding 1 is rejected cleanly", 24, False),
    ("by returning NotImplemented in except TypeError; Vector([1, 2, 3]) @ Vector([4, 5, 6]) == 32.0", 24, False),
    ("after checking isinstance(other, abc.Sized) and Iterable; if __iadd__ is missing, v1 += v2 falls back", 24, False),
    ("to v1 = v1 + v2 and changes id(v1), while a mutable class returns self", 24, False)
]

# Bottom:
bottom_lines = [
    ("If an operator has no natural meaning for your type, give the method a name", 25, False)
]

all_steps = [('s1', s1, 1320), ('s2', s2, 1320), ('s3', s3, 1320), ('s4', s4, 1320), ('s5', s5, 1320), ('strip', strip_lines, 1440), ('bottom', bottom_lines, 1440)]

for name, lines, mw in all_steps:
    print(f"=== {name} ===")
    full_text = " ".join([l[0] for l in lines])
    print("Words count:", len(full_text.split()))
    for l, fs, mono in lines:
        w = check_line(l, fs, mono)
        print(f"  {w:6.1f} / {mw} px (len {len(l)}): {l}")
        assert w <= mw, f"FAILED: {l} ({w} > {mw})"

print("\nALL LINES FIT SAFELY!")
