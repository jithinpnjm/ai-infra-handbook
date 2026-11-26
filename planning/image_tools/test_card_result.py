# Verify card-result 3-line layout
box_x, box_y, box_w, box_h = 845, 455, 690, 125
icon_x, icon_y, icon_w, icon_h = 865, 489, 56, 56
lines = [
    ("the quota is burned early in each", 940, 492),
    ("period, then every thread pauses", 940, 524),
    ("even though other CPUs are idle", 940, 556)
]

print("Card Result Check:")
for text, tx, ty in lines:
    w = len(text) * 0.6 * 24
    pad_l = tx - box_x
    pad_r = (box_x + box_w) - (tx + w)
    top_y = ty - 24 * 0.8
    bot_y = ty + 24 * 0.2
    pad_t = top_y - box_y
    pad_b = (box_y + box_h) - bot_y
    gap_icon = tx - (icon_x + icon_w)
    print(f"  '{text}'")
    print(f"    w={w:5.1f}, pad_l={pad_l:4.1f}, pad_r={pad_r:4.1f}, pad_t={pad_t:4.1f}, pad_b={pad_b:4.1f}, gap_icon={gap_icon:4.1f}")
    assert pad_l >= 16
    assert pad_r >= 16
    assert pad_t >= 16
    assert pad_b >= 16
    assert gap_icon >= 16

print("Card Result 3-line layout is PERFECT!")
