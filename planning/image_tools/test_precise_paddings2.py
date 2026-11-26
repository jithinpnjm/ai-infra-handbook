import re

# Let's adjust line wraps for sub-col w=380:
# Usable width with 20px padding on each side = 340 px!
# At fs=24 sans (0.60 * 24 = 14.4 px/char): max chars = 340 / 14.4 = 23.6 chars.
# At fs=24 mono (0.62 * 24 = 14.88 px/char): max chars = 340 / 14.88 = 22.8 chars.

cards = [
    ("Card 1", 760, 185, 380, 80, ["len(inv) is 52"], 24, False),
    ("Card 5", 1160, 185, 380, 80, ["inv[:3]", "first three nodes"], 24, False),
    ("Card 2", 760, 280, 380, 85, ["inv[0] ==", "Node(slot=01, rack=r1)"], 24, True),
    ("Card 3", 1160, 280, 380, 85, ["inv[-1] ==", "Node(slot=13, rack=r4)"], 24, True),
    ("Card 4", 760, 380, 380, 85, ["choice(inv)", "random selection"], 24, False),
    ("Card 7", 1160, 380, 380, 85, ["for node in inv", "and reversed(inv)"], 24, True),
    ("Card 6", 760, 480, 380, 115, ["inv[12::13] slot 13 of", "every rack: start at", "index 12, step 13"], 24, False),
    ("Card 8", 1160, 480, 380, 115, [
        "Node(07, r2) in inv is True,",
        "Node(07, r9) in inv is False",
        "(a sequential scan)"
    ], 24, False),
    ("Card 9", 760, 610, 780, 140, [
        "sorted(inv, key=drain_order): slot position times the number",
        "of racks plus rack priority from RACK_PRIORITY = r4:3, r3:2,",
        "r2:1, r1:0, so slot 01 of r1 ranks 0 and slot 13 of r4 ranks 51"
    ], 24, False),
    ("Card 10", 760, 765, 780, 80, ["random.shuffle(inv) needs __setitem__"], 24, True)
]

# Wait, check Card 8 line 1: "Node(07, r2) in inv is True," -> 28 chars!
# 28 chars * 14.4 = 403.2 > 380!
# So Card 8 must be 4 lines:
# Line 1: "Node(07, r2) in inv" (19 chars = 273.6 px)
# Line 2: "is True, Node(07, r9)" (21 chars = 302.4 px)
# Line 3: "in inv is False" (15 chars = 216.0 px)
# Line 4: "(a sequential scan)" (19 chars = 273.6 px)

cards[7] = ("Card 8", 1160, 480, 380, 115, [
    "Node(07, r2) in inv",
    "is True, Node(07, r9)",
    "in inv is False",
    "(a sequential scan)"
], 24, False)

all_ok = True
for name, bx, by, bw, bh, lines, fs, is_mono in cards:
    print(f"\n--- {name} (w={bw}, h={bh}) ---")
    char_factor = 0.62 if is_mono else 0.60
    for l in lines:
        w = len(l) * fs * char_factor
        pad = (bw - w) / 2
        ok = pad >= 16.0
        if not ok:
            all_ok = False
        print(f"  [{'PASS' if ok else 'FAIL'}] w={w:5.1f} | pad={pad:4.1f} px | '{l}'")
    
    total_text_h = (len(lines) - 1) * 26 + fs
    v_pad = (bh - total_text_h) / 2
    v_ok = v_pad >= 16.0
    if not v_ok:
        all_ok = False
    print(f"  [{'PASS' if v_ok else 'FAIL'}] V-pad: {v_pad:.1f} px (total text h={total_text_h})")

assert all_ok, "Some paddings failed!"
print("\nALL CARDS PASS STRICT PADDING CHECKS!")
