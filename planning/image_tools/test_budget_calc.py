# Let's test full height budget with a 180px Card 2

# Canvas height = 1200.
# Margin top = 40, bottom = 40.
# Available height = 1200 - 80 = 1120px.

# Title:
# y = 40..136 (h = 96)
# Gap = 40

# Ladders:
# Start at y = 176.
# If Ladders height = 480:
# Ladders end at y = 656.
# Gap = 40 -> y = 696.

# Commands strip:
# y = 696..812 (h = 116)
# Gap = 40 -> y = 852.

# Surprise story:
# y = 852..938 (h = 86)
# Gap = 40 -> y = 978.

# Rules strip:
# y = 978..1094 (h = 116)
# Gap = 40 -> y = 1134.

# Bottom bar:
# y = 1134..1190 (h = 56).
# Bottom margin = 1200 - 1190 = 10px ???
# Wait! 10px is less than 40px outside margin!
# 1190 > 1160!
# Total height with 480px ladder exceeds 1160 by 30px!

print("Need 30px more space to have 40px bottom margin.")
