import math

# Cards definition (cx, cy, cw, ch)
# Let's test the ladder:
# Canvas: 1600 x 1200

# Let's test baseline positions:
# For a rung with card: cy, ch = 92 (top=cy, bottom=cy+92)
# Title: fs=30, sans (0.60).
# Check: fs=24, mono (0.62).

# For pad_t of Title:
# pad_t = (ly1 - 30 * 0.8) - cy >= 16
# ly1 - 24 - cy >= 16 => ly1 >= cy + 40.

# For pad_b of Check:
# pad_b = (cy + ch) - (ly2 + 24 * 0.2) >= 16
# (cy + 92) - (ly2 + 4.8) >= 16 => ly2 <= cy + 92 - 20.8 = cy + 71.2.

# Distance between ly1 and ly2:
# If ly1 = cy + 41, ly2 = cy + 71:
# ly2 - ly1 = 30px!
# Let's check:
# Title at ly1 = cy + 41:
# pad_t = (cy + 41 - 24) - cy = 17.0 >= 16.0!
# Check at ly2 = cy + 71:
# pad_b = (cy + 92) - (cy + 71 + 4.8) = 92 - 75.8 = 16.2 >= 16.0!
# Distance between Title baseline (cy+41) and Check baseline (cy+71) is 30px!
# Check text top = cy + 71 - 24 * 0.8 = cy + 71 - 19.2 = cy + 51.8.
# Title baseline = cy + 41. Title text bottom = cy + 41 + 6 = cy + 47.
# Gap between Title bottom (cy+47) and Check top (cy+51.8) is 4.8px! No overlap!

print("Testing exact formula for single-line check cards (ch=92):")
cy = 140
ch = 92
ly1 = cy + 41
ly2 = cy + 71
pad_t = (ly1 - 30 * 0.8) - cy
pad_b = (cy + ch) - (ly2 + 24 * 0.2)
print(f"ly1={ly1}, ly2={ly2}: pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
assert pad_t >= 16.0 and pad_b >= 16.0
print("PASS!")
