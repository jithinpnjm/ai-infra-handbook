import xml.etree.ElementTree as ET
import re

tree = ET.parse("output.svg")
root = tree.getroot()

# Check namespace
ns = {"svg": "http://www.w3.org/2000/svg"}

# Check title and desc
assert root[0].tag.endswith("title"), "First child must be title"
assert root[1].tag.endswith("desc"), "Second child must be desc"

print("Title:", root[0].text)
print("Desc:", root[1].text[:60], "...")

# Collect all text from text elements and tspans
all_texts = []
for text_elem in root.iter("{http://www.w3.org/2000/svg}text"):
    full = "".join(text_elem.itertext())
    all_texts.append(full)

print(f"\nTotal text elements: {len(all_texts)}")
for t in all_texts:
    print("  ->", t)

# Source texts:
source_labels = [
    '1 short __repr__ with reprlib.repr: Vector(range(1000)) is truncated, like Vector([0.0, 1.0, 2.0, 3.0, 4.0, ...])',
    '2 slice-aware __getitem__: if isinstance(key, slice): return type(self)(self._components[key]); else operator.index(key), which calls __index__ and raises TypeError for floats or tuples; slice.indices(length) normalizes bounds; SkipObject returns a new iterator from each __iter__ call so [x + y for x in skipper for y in skipper] makes 9 pairs from aa to ee, while Squares returns self from __iter__ and scans only once',
    '3 dynamic read-only attributes x, y, z, t through __match_args__ and __getattr__ reading self._components[0..3]; trap: v.x = 10 creates v.__dict__[x], which shadows __getattr__ while v[0] stays unchanged; fix: __setattr__ raises AttributeError for single lowercase letters a to z; allowed writes use super().__setattr__(attr, val) to avoid infinite recursion',
    '4 hashing: functools.reduce(operator.xor, (hash(x) for x in self), 0), initializer 0 covers empty vectors; streaming equality len(self) == len(other) and all(a == b for a, b in zip(self, other)) in O(1) extra memory',
    '5 operators: __neg__, __pos__, __add__, __radd__, __mul__, __rmul__, __matmul__, __rmatmul__, __contains__, __iadd__; format h for hyperspherical coordinates',
    'Vector([3, 4, 5]) + (10, 20) and (10, 20) + Vector([3, 4, 5]) both give Vector([13.0, 24.0, 5.0]) using zip_longest(self, other, fillvalue=0.0) and __radd__ = __add__; adding 1 is rejected cleanly by returning NotImplemented in except TypeError; Vector([1, 2, 3]) @ Vector([4, 5, 6]) == 32.0 after checking isinstance(other, abc.Sized) and Iterable; if __iadd__ is missing, v1 += v2 falls back to v1 = v1 + v2 and changes id(v1), while a mutable class returns self',
    'If an operator has no natural meaning for your type, give the method a name'
]

# Check that every word from the source labels appears in the SVG text
joined_svg_text = " ".join(all_texts)

# Verify no style words appear as literal text
for forbidden in ['orange', 'green', 'grey']:
    m = re.findall(rf'\b{forbidden}\b', joined_svg_text, re.IGNORECASE)
    assert len(m) == 0, f"Forbidden style word found in rendered text: {forbidden}"

print("\nForbidden style words check PASSED (none found).")

# Verify each source label reconstructed matches
# Group by id
step_groups = {
    'step1': root.find(".//*[@id='step1']", ns),
    'step2': root.find(".//*[@id='step2']", ns),
    'step3': root.find(".//*[@id='step3']", ns),
    'step4': root.find(".//*[@id='step4']", ns),
    'step5': root.find(".//*[@id='step5']", ns),
    'strip': root.find(".//*[@id='worked-results']", ns),
    'bottom': root.find(".//*[@id='bottom-bar']", ns),
}

for name, elem in step_groups.items():
    # get all text except the step number badge text if it's just '1','2', etc.
    texts_in_elem = []
    for t_el in elem.iter("{http://www.w3.org/2000/svg}text"):
        txt = "".join(t_el.itertext()).strip()
        if txt in ['1', '2', '3', '4', '5'] and 'step-num-txt' in t_el.attrib.get('class', ''):
            continue
        texts_in_elem.append(txt)
    reconstructed = " ".join(texts_in_elem)
    # Normalize multiple spaces
    reconstructed = re.sub(r'\s+', ' ', reconstructed)
    print(f"\n[{name}] reconstructed:")
    print(" ", reconstructed)

