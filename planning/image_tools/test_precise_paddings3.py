import re

# Layout:
# Canvas: 1600 x 1200
# Container: x = 700, y = 165, w = 860, h = 720
# Inside container:
# Sub-col 1: x = 720, w = 400
# Sub-col 2: x = 1140, w = 400
# Wide cards: x = 720, w = 820

# Let's check Card 9 line wrap into 4 lines:
# 185 chars:
# "sorted(inv, key=drain_order): slot position times the" (53 chars -> 53 * 14.4 = 763.2 px < 788 px!)
# "number of racks plus rack priority from RACK_PRIORITY =" (55 chars -> 55 * 14.4 = 792 > 788, let's break better)

def wrap_text_exact(text, max_w, fs=24, is_mono=False):
    char_w = fs * (0.62 if is_mono else 0.60)
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

lines9 = wrap_text_exact(
    "sorted(inv, key=drain_order): slot position times the number of racks plus rack priority from RACK_PRIORITY = r4:3, r3:2, r2:1, r1:0, so slot 01 of r1 ranks 0 and slot 13 of r4 ranks 51",
    788,
    fs=24
)
print(f"Card 9 has {len(lines9)} lines:")
for l in lines9:
    w = len(l) * 24 * 0.6
    print(f"   w={w:5.1f} | pad={(820-w)/2:4.1f} px | '{l}'")
    assert (820 - w)/2 >= 16.0


lines8 = wrap_text_exact(
    "Node(07, r2) in inv is True, Node(07, r9) in inv is False (a sequential scan)",
    368,
    fs=24
)
print(f"\nCard 8 has {len(lines8)} lines:")
for l in lines8:
    w = len(l) * 24 * 0.6
    print(f"   w={w:5.1f} | pad={(400-w)/2:4.1f} px | '{l}'")
    assert (400 - w)/2 >= 16.0

