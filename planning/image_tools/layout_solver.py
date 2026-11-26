# Let's write a solver that checks all constraints:
# 1. Canvas: 1600 x 1200
# 2. Outside margin >= 40 on all 4 sides
# 3. Gaps between distinct boxes >= 40
# 4. Text padding inside every box: left >= 16, right >= 16, top >= 16, bottom >= 16
# 5. Font sizes >= 24 everywhere

# Let's inspect Section 2:
# What if the chain of rules does NOT have nested <rect> boxes for each rule,
# but instead has the container rect, and the rules are rows within the container?
# OR what if the rules DO have rects?
# Let's test both!
