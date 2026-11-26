# Check vertical space for 2-line bottom bar:
# Rows end at y = 1096
# bottom_y = 1106
# bottom_h = 76
# bottom ends at 1106 + 76 = 1182
# Margin at bottom = 1200 - 1182 = 18 px! (>= 16 px!)

bottom_y = 1106
bottom_h = 76

# If 2 lines:
# Line 1: 'A guess that a second source agrees with is a conclusion;' (57 chars)
# Line 2: 'one nothing else supports is only a hypothesis' (46 chars)

# Text x = 110 (with icon at x=70, size 36x36)
# Max line width: 57 * 0.6 * 24 = 820.8 px.
# 110 + 820.8 = 930.8 px << 1560 px!

print("Bottom bar ends at:", bottom_y + bottom_h)
print("Bottom margin:", 1200 - (bottom_y + bottom_h))
