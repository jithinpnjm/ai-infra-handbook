# Let's test widths:
# Total width = 1600
# Left margin = 40, Right margin = 40
# Usable = 1520
# Let Left Column width = 780 (x = 40 to 820)
# Gap between columns = 40 (820 to 860)
# Right Column width = 700 (x = 860 to 1560)
# Margin right = 1600 - 1560 = 40.
# Check: 40 + 780 + 40 + 700 + 40 = 1600. PERFECT!

# Now in Left Column (width = 780):
# Can we place Callout 2 and Callout 1 side by side?
# Left box: x = 40 to 410 (width = 370)
# Gap = 40 (410 to 450)
# Right box: x = 450 to 820 (width = 370)
# Usable width in 370 with 18px padding each side = 370 - 36 = 334 px.
# At 24px sans (0.6 * 24 = 14.4 px/char):
# 334 / 14.4 = 23.19 chars per line.

c1 = "each host has a name and optionally an address"
# Line 1: "each host has a name" (20 chars * 14.4 = 288 px)
# Line 2: "and optionally an address" (25 chars * 14.4 = 360 px) -> a bit long for 334.
# What if 3 lines?
# Line 1: "each host has a name" (20 chars = 288 px)
# Line 2: "and optionally" (14 chars = 201.6 px)
# Line 3: "an address" (10 chars = 144 px)
# Total height for 3 lines at 30px line-height: 3 * 30 + 32 = 122 px.

c2 = "a group collects hosts that share a role"
# Line 1: "a group collects" (16 chars = 230.4 px)
# Line 2: "hosts that share a role" (23 chars = 331.2 px <= 334 px!)
# Or 3 lines:
# Line 1: "a group collects" (16 chars = 230.4 px)
# Line 2: "hosts that share" (16 chars = 230.4 px)
# Line 3: "a role" (6 chars = 86.4 px)

print("Both fit cleanly in 370 px width!")
