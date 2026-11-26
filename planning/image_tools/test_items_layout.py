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
        # conservative: 0.62 for mono if starts with code, or 0.60
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

print("=== 2 Sub-columns: Left col w=410, Right col w=410 ===")
usable_w = 410 - 32 # 378 px
for i, (t, is_code) in enumerate(items):
    lines = wrap_text(t, usable_w)
    print(f"Item {i+1:2d} ({len(lines)} lines, max line len={max(len(l) for l in lines)}):")
    for l in lines:
        print(f"    {l}")

