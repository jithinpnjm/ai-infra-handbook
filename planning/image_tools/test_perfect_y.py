senders = [
    (1, "U", "A"),
    (2, "A", "S"),
    (3, "S", "A"),
    (4, "A", "K"),
    (5, "K", "K"),
    (6, "K", "D"),
    (7, "K", "V"),
    (8, "K", "R"),
    (9, "R", "C"),
    (10, "K", "R"),
    (11, "K", "R"),
    (12, "R", "X"),
    (13, "K", "A"),
    (14, "NOTE", "KX"),
    (15, "U", "A"),
    (16, "A", "K"),
    (17, "K", "X"),
    (18, "K", "R"),
    (19, "K", "V"),
    (20, "K", "A")
]

# Exact deltas:
# If same sender: dy = 49
# If Note: dy = 48
# If 2 lines: dy = 44
# Otherwise: dy = 41

dys = [
    0,   # 1: U
    42,  # 2: A
    44,  # 3: S (2 lines)
    42,  # 4: A
    46,  # 5: K (2 lines)
    49,  # 6: K (same sender!)
    49,  # 7: K (same sender!)
    49,  # 8: K (same sender!)
    42,  # 9: R
    42,  # 10: K
    49,  # 11: K (same sender!)
    42,  # 12: R
    44,  # 13: K (2 lines)
    48,  # 14: NOTE
    48,  # 15: U
    42,  # 16: A
    42,  # 17: K
    49,  # 18: K (same sender!)
    49,  # 19: K (same sender!)
    49   # 20: K (same sender!)
]

y_start = 264
ys = []
cur = y_start
for dy in dys:
    cur += dy
    ys.append(cur)

print("Generated Y coordinates:")
for (num, s, r), y in zip(senders, ys):
    print(f"Step {num:2d} ({s:4s}->{r:4s}): y = {y}")

print(f"\nFinal step at y = {ys[-1]}, circle bottom = {ys[-1] + 24}")
print(f"Bottom margin = {1200 - (ys[-1] + 24)}")
assert 1200 - (ys[-1] + 24) >= 40, "Bottom margin < 40!"
print("Bottom margin check PASS!")
