import re

items = [
    ("len(inv) is 52", False),
    ("inv[0] == Node(slot=01, rack=r1)", True),
    ("inv[-1] == Node(slot=13, rack=r4)", True),
    ("choice(inv) random selection", False),
    ("inv[:3] first three nodes", True),
    ("inv[12::13] slot 13 of every rack: start at index 12, step 13", False),
    ("for node in inv and reversed(inv)", True),
    ("Node(07, r2) in inv is True, Node(07, r9) in inv is False (a sequential scan)", False),
    ("sorted(inv, key=drain_order): slot position times the number of racks plus rack priority from RACK_PRIORITY = r4:3, r3:2, r2:1, r1:0, so slot 01 of r1 ranks 0 and slot 13 of r4 ranks 51", False),
    ("random.shuffle(inv) needs __setitem__", True)
]

def wrap_text(text, max_w, fs=24):
    words = text.split()
    lines = []
    cur = []
    for w in words:
        test_line = ' '.join(cur + [w])
        char_w = fs * 0.60
        if len(test_line) * char_w <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(' '.join(cur))
            cur = [w]
    if cur:
        lines.append(' '.join(cur))
    return lines

# Option 1:
# What if the right column has:
# A large container (light green #e8f1ea, stroke #207448).
# Inside the container:
# What if we have 2 columns of items?
# Left sub-column: items 1, 2, 3, 4, 5
# Right sub-column: items 6, 7, 8, 10
# And item 9 spanning across both at the bottom?
# Let's check widths:
# Container width: 810.
# Inner padding: 20 px left/right -> 770 px.
# Sub-column width: (770 - 20 gap) / 2 = 375 px.
# Bottom item 9 width: 770 px.
print("=== Arrangement A ===")
print("Left sub-col (w=375, usable=343):")
for i in [0, 1, 2, 3, 4]:
    lines = wrap_text(items[i][0], 343)
    print(f"  Item {i+1}: {len(lines)} lines -> {lines}")

print("\nRight sub-col (w=375, usable=343):")
for i in [5, 6, 7, 9]:
    lines = wrap_text(items[i][0], 343)
    print(f"  Item {i+1}: {len(lines)} lines -> {lines}")

print("\nBottom Item 9 (w=770, usable=738):")
lines9 = wrap_text(items[8][0], 738)
print(f"  Item 9: {len(lines9)} lines -> {lines9}")

