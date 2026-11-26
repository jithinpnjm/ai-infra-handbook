from test_card_text import check_lines

# Let's test wrapping RP items with max_w = 600 (card width 670, text width 600)
# Item 1:
lines_rp1 = [
    "types.MappingProxyType(d) is a read-only view",
    "that still reflects later updates to d, so callers",
    "cannot change a hardware pin map while",
    "the owner keeps it current"
]
# Wait, let's test with max_w = 540 and max_w = 600
def find_wrap(text, max_chars):
    words = text.split()
    lines = []
    curr = []
    for w in words:
        if sum(len(x) for x in curr) + len(curr) + len(w) <= max_chars:
            curr.append(w)
        else:
            lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))
    return lines

item1 = "types.MappingProxyType(d) is a read-only view that still reflects later updates to d, so callers cannot change a hardware pin map while the owner keeps it current"
item2 = "dict.keys() and dict.items() are live views with no copying and support & | - ^"
item3 = "Python scope lookup uses the same idea: ChainMap(locals(), globals(), vars(builtins))"
item4 = "merge: a | b, {**a, **b}, or ChainMap; a deep merge needs recursion"
item5 = "dicts compare equal regardless of key order, lists are order-sensitive"

for i, it in enumerate([item1, item2, item3, item4, item5], 1):
    # If text has 560px width, max chars at sans 24px (14.4px/char) is 560 / 14.4 = 38 chars
    lines = find_wrap(it, 37)
    print(f"\nItem {i} wrapped at 37 chars:")
    for l in lines:
        print(f"  '{l}' ({len(l)} chars, {len(l)*14.4:.1f}px)")
