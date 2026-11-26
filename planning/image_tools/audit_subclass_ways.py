import xml.etree.ElementTree as ET
import re

svg_file = "candidate_subclass_ways.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

# 3. Check text elements and font-size >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text '{full_text}'"
    size = float(fs)
    assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, size))

print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Four ways a subclass talks to its superclass, plus mixins and delegation",
    "Inheritor(Super): pass, inherits methods unchanged",
    "Replacer(Super): overrides method(self) completely",
    "Extender(Super): overrides method(self) and calls back Super.method(self); example Manager.giveRaise(self, percent, bonus=.10) calls Person.giveRaise(self, percent + bonus)",
    "Provider(Super): implements the abstract action(self) hook that Super.delegate(self) expects, the Template Method pattern",
    "Mixins",
    "a small class named ...Mixin adding one independent capability through multiple inheritance: AttrDisplay, ListInstance (inspects self.__dict__), ListInherited (dir(self)), ListTree (climbs __class__ and __bases__); UpperCaseMixin uppercases string keys with super().__setitem__(_upper(key), item) and must be listed first: class UpperDict(UpperCaseMixin, collections.UserDict): pass, so it intercepts calls before UserDict on the MRO",
    "subclassing a built-in C type such as dict or list directly is risky because C methods ignore Python overrides; use collections.UserDict, UserList or UserString",
    "Composition and delegation",
    "inheritance models is-a (PizzaRobot is a Chef, a Chef is an Employee); composition models has-a (PizzaShop contains Server, PizzaRobot and Oven; Department gathers Person and Manager objects); delegation: a wrapper holds an embedded object and forwards requests with def __getattr__(self, attr): return getattr(self.person, attr); special operators such as __str__ or __add__ are looked up on the class directly, so they bypass instance-level __getattr__",
    "isinstance(x, Base) and issubclass respect inheritance; type(x) is T checks the exact type, rarely wanted; Liskov: a subclass accepts at least what the base accepts, returns no less than the base promises, and adds no surprising exceptions",
    "Customize a component without touching its source"
]

found_texts = [t for t, fs in text_elements]

print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n6. No forbidden words found! (PASS)")

# 6. Check orange count
with open(svg_file, 'r', encoding='utf-8') as f:
    svg_str = f.read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 10, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n8. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"

# 8. Check colors present
assert "#f5f8f5" in svg_str
assert "#303a36" in svg_str
assert "#207448" in svg_str

print("\nALL 8 SVG AUDIT CHECKS PASSED PERFECTLY!")
