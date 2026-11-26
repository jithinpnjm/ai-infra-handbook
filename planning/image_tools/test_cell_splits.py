# Let's test line splits for every cell.
# Suppose:
# Col 0 (Resource): width = 340 px, max_text_w = 340 - 32 = 308 px.
# But wait: if icon is in Col 0, where is the icon placed?
# "placed beside or above its title, never overlapping text."
# If icon is 56x56, placed at the left (e.g. x = col_x + 16, y = centered),
# then text starts at x = col_x + 16 + 56 + 16 = col_x + 88.
# Remaining width for text = 340 - 88 - 16 = 236 px.
# At 30 px bold (0.6 * 30 = 18 px/char):
# 236 / 18 = 13.1 characters per line!
# Can resource titles wrap in 13 characters?
# "PCIe" (4)
# "(GPU, NIC," (10)
# "NVMe)" (5)
# "GPU compute" (11)
# "(SMs, tensor" (12)
# "cores)" (6)
# "GPU memory" (10)
# "(HBM)" (5)
# "capacity" (8)
# "NVLink and" (10)
# "NVSwitch" (8)
# "Power and" (9)
# "thermal" (7)
# That wraps nicely!
# OR: What if icon is placed ABOVE the title?
# If icon is placed ABOVE the title (centered in Col 0):
# Then the entire width of 340 - 32 = 308 px is available for text!
# At 18 px/char: 308 / 18 = 17.1 characters per line!
# Let's check which layout (icon beside vs icon above) is better.

# Let's check row height:
# If a row has 4 lines of text at 24px:
# line height ~ 30px (e.g. dy=30).
# 4 lines * 30px = 90px + 32px padding = 122px minimum box height.
# If row height = 130px:
# 5 rows * 130px = 650px.
# Headers row = 50px.
# Title = 80px.
# Footnote = 40px.
# Callout = 80px.
# Bottom bar = 55px.
# Gaps = 6 * 12px = 72px.
# Total height = 80 + 50 + 650 + 72 + 40 + 80 + 55 = 1027px!
# This fits within H = 1100 to 1200 comfortably!

print("Row height calculation looks very promising.")
