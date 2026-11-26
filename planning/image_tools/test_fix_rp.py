# Fix icon and tx in RP items
# box_x = 850, box_w = 670 -> box_r = 1520
# icon at x = 865, width = 44 -> icon_r = 909
# tx = 935

icon_r = 909
tx = 935
box_r = 1520

lines = [
    'types.MappingProxyType(d) is a',
    'read-only view that still reflects',
    'later updates to d, so callers cannot',
    'change a hardware pin map while the',
    'owner keeps it current',
    'dict.keys() and dict.items() are live',
    'views with no copying and support',
    '& | - ^',
    'Python scope lookup uses the same',
    'idea: ChainMap(locals(), globals(),',
    'vars(builtins))',
    'merge: a | b, {**a, **b}, or',
    'ChainMap; a deep merge needs',
    'recursion',
    'dicts compare equal regardless of key',
    'order, lists are order-sensitive'
]

for l in lines:
    w = len(l) * 0.60 * 24
    pad_l = tx - icon_r
    pad_r = box_r - (tx + w)
    assert pad_l >= 16.0, f"pad_l failed: {pad_l}"
    assert pad_r >= 16.0, f"pad_r failed: {pad_r}"

print("All RP lines pass padding >= 16px with flying colors!")
