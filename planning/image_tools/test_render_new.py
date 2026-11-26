import re

# Let's check vertical budget if:
# Row 1: y = 70 to 154 (h = 84)
# Row 2: y = 164 to 248 (h = 84)
# Step 1 starts at y = 260.

# For each step:
# Card sits at y = by, height = bh.
# Arrow is at ay = by + bh + 4.
# Circle is centered at ay: cy = ay, r = 24.
# Next step starts at by_next = ay + 24 + gap.
# If previous step is K and current step is K:
# We need cy_curr - cy_prev >= 49.
# cy_curr = by_curr + bh_curr + 4.
# cy_prev = by_prev + bh_prev + 4.
# So (by_curr + bh_curr) - (by_prev + bh_prev) >= 49.

