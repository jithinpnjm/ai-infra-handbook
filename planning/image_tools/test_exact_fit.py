# Let's test exact vertical positions with H=1200
# Canvas height H = 1200, width = 1600.
# Margins:
# Top: y = 35. Title at y = 70.
# Title: 48px bold.
# If title is 1 line:
# "Two state-table limits that look like random timeouts: SNAT ports and conntrack"
# Can it fit in 1 line?
# 79 chars. If font-size is 48, 79 * 48 * 0.6 = 2275 -> definitely needs 2 lines or font size 48?
# Prompt: "Title 48 px bold."
# 48px bold title in 2 lines:
# Line 1: y = 50, Line 2: y = 98.
# Title area ends at y = 115.
# Bottom takeaway bar:
# y = 1120 to 1175 (height 55px).
# Bottom margin = 25px.
# So panel top y = 135, panel bottom y = 1100.
# Available height for panel = 1100 - 135 = 965 px!

print("Available panel height: 965 px")
