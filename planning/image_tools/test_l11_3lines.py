from test_l8_wrap import wrap

l11 = "isinstance(x, Base) and issubclass respect inheritance; type(x) is T checks the exact type, rarely wanted; Liskov: a subclass accepts at least what the base accepts, returns no less than the base promises, and adds no surprising exceptions"

lines = wrap(l11, 88)
print(f"lines={len(lines)}, max len={max(len(l) for l in lines)}")
for l in lines:
    print(f"  ({len(l):2d}) {l}")
    w = len(l) * 0.62 * 24
    print(f"       w={w:.1f}, right={135 + w:.1f}, pad={1560 - (135 + w):.1f}")

