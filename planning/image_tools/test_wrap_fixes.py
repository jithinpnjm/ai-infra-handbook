lines_dash = [
    ("replica count rose at", 24, 880, 145),
    ("once while serving", 24, 908, 145),
    ("count stayed flat;", 24, 936, 145),
    ("that gap is what to explain", 24, 964, 145)
]

# Dashboard box: (55, 836, 550, 164)
bx, by, bw, bh = 55, 836, 550, 164
for txt, fs, baseline, anchor_x in lines_dash:
    w = len(txt) * fs * 0.6
    pad_l = anchor_x - bx
    pad_r = (bx + bw) - (anchor_x + w)
    pad_t = (baseline - fs) - by
    pad_b = (by + bh) - baseline
    print(f"Dash: '{txt}' pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
    assert pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16

lines_card2 = [
    ("--max-node-provision-time default 15 minutes:", 24, 334, 746, True),
    ("if a node has not registered by then", 24, 362, 746, False),
    ("the autoscaler stops counting it,", 24, 390, 746, False),
    ("which is why you keep warm capacity", 24, 418, 746, False)
]

# Card 2 box: (675, 290, 870, 150)
bx, by, bw, bh = 675, 290, 870, 150
for txt, fs, baseline, anchor_x, is_mono in lines_card2:
    w = len(txt) * fs * (0.62 if is_mono else 0.6)
    pad_l = anchor_x - bx
    pad_r = (bx + bw) - (anchor_x + w)
    pad_t = (baseline - fs) - by
    pad_b = (by + bh) - baseline
    print(f"Card2: '{txt}' pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
    assert pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16

print("\nAll wrapped lines PASS strict padding audit!")
