# Monospace 24px: 0.62 * 24 = 14.88 px/char
# Box width = 412 px (x = 74 to 486). Left = 74, Right = 486.
# If text is left aligned at x = 96 (22px from left edge):
# Max allowed x = 486 - 16 = 470 px.
# Max allowed width = 470 - 96 = 374 px.
# Max allowed chars = 374 / 14.88 = 25.13 chars -> 25 chars.

line1 = "slurmctld: error: Nodes dgx-h100-14 not responding"
# Split into 3 lines:
l1_parts = [
    "slurmctld: error:",
    "Nodes dgx-h100-14",
    "not responding"
]

print("=== LINE 1 WRAPPING ===")
for p in l1_parts:
    w = len(p) * 14.88
    pad_left = 96 - 74 # 22px
    pad_right = 486 - (96 + w)
    print(f"  [{len(p):2d}c, {w:5.1f}px] left_pad={pad_left:.1f}px, right_pad={pad_right:.1f}px: '{p}'")

line2 = "slurmctld: Node dgx-h100-14 now responding"
# Split into 3 lines:
l2_parts = [
    "slurmctld: Node",
    "dgx-h100-14 now",
    "responding"
]

print("\n=== LINE 2 WRAPPING ===")
for p in l2_parts:
    w = len(p) * 14.88
    pad_left = 96 - 74 # 22px
    pad_right = 486 - (96 + w)
    print(f"  [{len(p):2d}c, {w:5.1f}px] left_pad={pad_left:.1f}px, right_pad={pad_right:.1f}px: '{p}'")
