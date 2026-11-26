# Header row 2 ends at y = 248.
# Step 1 can start at y = 256.

steps_config = [
    # 1: 1 line, h=32
    {"num": 1, "lines": 1, "h": 32},
    # 2: 1 line, h=32
    {"num": 2, "lines": 1, "h": 32},
    # 3: 2 lines, h=52
    {"num": 3, "lines": 2, "h": 52},
    # 4: 1 line, h=32
    {"num": 4, "lines": 1, "h": 32},
    # 5: 2 lines, h=52
    {"num": 5, "lines": 2, "h": 52},
    # 6: 1 line, h=32
    {"num": 6, "lines": 1, "h": 32},
    # 7: 1 line, h=32
    {"num": 7, "lines": 1, "h": 32},
    # 8: 1 line, h=32
    {"num": 8, "lines": 1, "h": 32},
    # 9: 1 line, h=32
    {"num": 9, "lines": 1, "h": 32},
    # 10: 1 line, h=32
    {"num": 10, "lines": 1, "h": 32},
    # 11: 1 line, h=32
    {"num": 11, "lines": 1, "h": 32},
    # 12: 1 line, h=32
    {"num": 12, "lines": 1, "h": 32},
    # 13: 3 lines, h=76
    {"num": 13, "lines": 3, "h": 76},
    # Note: 1 line, h=38
    {"num": "note", "lines": 1, "h": 38},
    # 14: 1 line, h=32
    {"num": 14, "lines": 1, "h": 32},
    # 15: 1 line, h=32
    {"num": 15, "lines": 1, "h": 32},
    # 16: 1 line, h=32
    {"num": 16, "lines": 1, "h": 32},
    # 17: 1 line, h=32
    {"num": 17, "lines": 1, "h": 32},
    # 18: 1 line, h=32
    {"num": 18, "lines": 1, "h": 32},
    # 19: 1 line, h=32
    {"num": 19, "lines": 1, "h": 32}
]

cur_y = 256.0
gap = 10.0 # gap between cards
for sc in steps_config:
    sc["by"] = cur_y
    # circle cy: for 1 line, by + 16. For multiline, by + 24 (or by + h/2)
    sc["cy"] = cur_y + max(16.0, sc["h"] / 2.0)
    cur_y += sc["h"] + gap

total_height = cur_y - gap
print(f"Total height ends at: {total_height:.1f}")
print(f"Bottom margin (H=1200): {1200.0 - total_height:.1f}px")
