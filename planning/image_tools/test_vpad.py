# Check vertical padding for all cards

card_v = [
    # (name, box_y, box_h, [(text, baseline_y, font_size)])
    ("Card 1", 115, 145, [
        ("code", 165, 26),
        ("c1_1", 205, 24),
        ("c1_2", 237, 24)
    ]),
    ("Card 2", 280, 115, [
        ("code", 325, 26),
        ("c2", 365, 24)
    ]),
    ("Card 3", 415, 180, [
        ("code", 460, 26),
        ("c3_1", 500, 24),
        ("c3_2", 532, 24),
        ("c3_3", 564, 24)
    ]),
    ("Card 4", 615, 305, [
        ("code1", 655, 24),
        ("code2", 687, 24),
        ("c4_1", 727, 24),
        ("c4_2", 759, 24),
        ("c4_3", 791, 24),
        ("c4_4", 823, 24),
        ("c4_5", 855, 24),
        ("c4_6", 887, 24)
    ]),
    ("Card 5", 940, 80, [
        ("code", 985, 26)
    ]),
    ("Input", 200, 240, [
        ("in1", 270, 26),
        ("in2", 312, 26),
        ("in3", 354, 26)
    ]),
    ("Output", 660, 260, [
        ("out1", 725, 26),
        ("out2", 767, 26),
        ("out3", 809, 26)
    ]),
    ("Warning", 1040, 60, [
        ("warn", 1076, 24)
    ]),
    ("Bottom", 1120, 65, [
        ("bot", 1162, 28)
    ])
]

all_v_pass = True
for name, by, bh, lines in card_v:
    top_y = lines[0][1] - lines[0][2]
    bot_y = lines[-1][1] + 6 # descent
    top_pad = top_y - by
    bot_pad = (by + bh) - bot_y
    if top_pad < 16 or bot_pad < 16:
        print(f"FAIL: {name} top_pad={top_pad:.1f}, bot_pad={bot_pad:.1f}")
        all_v_pass = False
    else:
        print(f"PASS: {name} top_pad={top_pad:.1f}, bot_pad={bot_pad:.1f}")

print(f"\nAll vertical padding >= 16px: {all_v_pass}")
print("\n--- Testing adjusted Warning and Bottom ---")
# Warning: by=1035, bh=65, baseline=1075
top_y = 1075 - 24
bot_y = 1075 + 6
print(f"Warning: top_pad={top_y - 1035}, bot_pad={(1035 + 65) - bot_y}")

# Bottom: by=1115, bh=70, baseline=1160
top_y = 1160 - 28
bot_y = 1160 + 7
print(f"Bottom: top_pad={top_y - 1115}, bot_pad={(1115 + 70) - bot_y}")
