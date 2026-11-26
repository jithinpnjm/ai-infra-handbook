# Let's test the math for 6 stacked blocks:
title_h = 75
gap_title = 40
gaps = 5 * 40 # 5 gaps between 6 blocks = 200px
bottom_margin = 40
top_margin = 40

# Available height for the 6 blocks:
# 1200 - 40 (top) - 75 (title) - 40 (gap) - 200 (5 gaps) - 40 (bottom) = 805px!
print(f"Available height for 6 blocks: {805}px")

# What are the 6 blocks?
# 1. Ladder 1 (header + 4 rungs): min height ~ 300px
# 2. Ladder 2 (header + 4 rungs): min height ~ 260px
# 3. Surprise story: min height ~ 65px
# 4. Commands strip: min height ~ 75px
# 5. Rules strip: min height ~ 95px
# 6. Bottom bar: min height ~ 50px
total_blocks = 300 + 260 + 65 + 75 + 95 + 50
print(f"Total needed for 6 blocks: {total_blocks}px")
print(f"Difference: {805 - total_blocks}px")
