# Let's find perfect column positions:
# Width = 1600
# Box width = 250 (e.g. 56px icon + 16px gap + text + padding)
# Let's check if 250px is enough for box width:
# The longest node title is "ALLOCATED": 9 chars * 0.6 * 32 = 172.8px
# Icon: 48px. Gap: 14px.
# Total width of content = 48 + 14 + 172.8 = 234.8px.
# Box width = 270px -> padding horizontal = (270 - 234.8)/2 = 17.6px >= 16px!
#
# Let's check box width = 260px:
# If icon is 44px, gap 12px, text 172.8px -> content = 228.8px.
# Box width = 265px -> padding = (265 - 228.8)/2 = 18.1px >= 16px!

# Let's check 3 columns with box_w = 260:
# Col 1: [50 .. 310] (cx = 180)
# Col 2: [670 .. 930] (cx = 800)
# Col 3: [1290 .. 1550] (cx = 1420)
#
# Gap between Col 1 and Col 2 = 670 - 310 = 360px!
# 360px > 274px (clearance = (360 - 274)/2 = 43px >= 16px!)
#
# Gap between Col 2 and Col 3 = 1290 - 930 = 360px!
#
# Between Col 2 and Col 3:
# Transition: ALLOCATED -> DOWN: "node failure (jobs requeued or failed)"
# Length = 38 chars * 0.6 * 24 = 547.2px!
# WAIT!
# 547.2px is larger than 360px!
# If Col 2 and Col 3 have a gap of 360px, how can a 547.2px text fit on a 360px gap?!
# IT CANNOT!

print("Col 2 to Col 3 gap of 360px cannot fit 547px text on a straight horizontal segment!")
