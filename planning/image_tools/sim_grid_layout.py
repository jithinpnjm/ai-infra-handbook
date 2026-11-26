import re

def wrap_text(text, max_w, fs=24):
    char_w = fs * 0.60
    words = text.split()
    lines = []
    cur = []
    for w in words:
        test_line = ' '.join(cur + [w])
        if len(test_line) * char_w <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(' '.join(cur))
            cur = [w]
    if cur:
        lines.append(' '.join(cur))
    return lines

# Let's test widths and heights:
# Container x: 680 to 1560 -> width = 880
# Inside container: padding 20 px -> usable x: 700 to 1540 (w = 840)
# Sub-columns: 2 columns of width 405, gap = 30 -> 405 + 30 + 405 = 840!

items = {
    1: "len(inv) is 52",
    2: "inv[0] == Node(slot=01, rack=r1)",
    3: "inv[-1] == Node(slot=13, rack=r4)",
    4: "choice(inv) random selection",
    5: "inv[:3] first three nodes",
    6: "inv[12::13] slot 13 of every rack: start at index 12, step 13",
    7: "for node in inv and reversed(inv)",
    8: "Node(07, r2) in inv is True, Node(07, r9) in inv is False (a sequential scan)",
    9: "sorted(inv, key=drain_order): slot position times the number of racks plus rack priority from RACK_PRIORITY = r4:3, r3:2, r2:1, r1:0, so slot 01 of r1 ranks 0 and slot 13 of r4 ranks 51",
    10: "random.shuffle(inv) needs __setitem__"
}

print("=== Col A (w=405, usable=373) ===")
for i in [1, 2, 3, 4]:
    lines = wrap_text(items[i], 373)
    print(f"Item {i} ({len(lines)} lines): {lines}")

print("\n=== Col B (w=405, usable=373) ===")
for i in [5, 6, 7, 8]:
    lines = wrap_text(items[i], 373)
    print(f"Item {i} ({len(lines)} lines): {lines}")

print("\n=== Full width or bottom row ===")
# What if Item 9 is width 530, and Item 10 is width 280 (gap 30 -> 530 + 30 + 280 = 840)?
lines9 = wrap_text(items[9], 530 - 32)
lines10 = wrap_text(items[10], 280 - 32)
print(f"Item 9 (w=530, usable=498): {len(lines9)} lines:")
for l in lines9:
    print(f"   {len(l)*24*0.6:5.1f}px | {l}")

print(f"\nItem 10 (w=280, usable=248): {len(lines10)} lines:")
for l in lines10:
    print(f"   {len(l)*24*0.6:5.1f}px | {l}")

