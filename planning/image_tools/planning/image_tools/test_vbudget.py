# Vertical budget solver for the whole SVG canvas

H = 1200
# Margins:
# Top margin = 40
# Bottom margin = 40
# Available height = 1120 (from y = 40 to y = 1160)

# Let's see:
# 1. Title: y = 40 to 118 (ends at 118)
# Gap = 40 -> y = 158

# Bottom elements:
# Takeaway bar: y = 1100 to 1160 (h = 60). Ends at 1160. Margin to 1200 is 40.
# Gap = 40 -> ends at 1100, so Test strip ends at 1060.
# Test strip: y = 940 to 1060 (h = 120).
# Gap = 40 -> middle section must end at y = 900.

# Available height for Middle Section: 900 - 158 = 742 px!
print(f"Available middle section height: {742} px")
