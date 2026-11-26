# Canvas width = 1600.
# Available height = up to 1200. Let's use H = 1180 or 1200.
# Margin left = 40, Margin right = 40. Available width = 1520.

# 1. Three Phase Cards:
# Gap between cards = 40 px.
# Total width of 3 cards = 1520 - 2 * 40 = 1440.
# Width of each card = 1440 / 3 = 480 px.
# Card 1: x = 40, w = 480 (x: 40 to 520)
# Gap: 520 to 560 (40 px)
# Card 2: x = 560, w = 480 (x: 560 to 1040)
# Gap: 1040 to 1080 (40 px)
# Card 3: x = 1080, w = 480 (x: 1080 to 1560)
# Margin right: 1560 to 1600 = 40 px.

# Vertical layout:
# Top margin: 40 px.
# Title: font-size 48. Baseline at y = 68. (Cap height ~34, ascenders ~36, so text fits between y=34 and y=76).
# Margin between title and Phase cards:
# Phase cards top: y = 115. (115 - 76 = 39 -> let's make top y = 120! 120 - 76 = 44 px >= 40 px).

# Let's see Phase card height:
# Inside Phase card (w = 480):
# If icon is 56px:
# Let's place icon at top: x = x_card + 32, y = y_card + 20, size 56x56 (ends at y_card + 76).
# Or icon at top left, title beside icon:
# "Phase 1 expand:" -> 15 chars * 30 * 0.6 = 270 px.
# If icon is x = x_card + 24, w = 56 (ends at x_card + 80).
# Gap between icon and title: 16 px -> title starts at x_card + 96.
# Available width beside icon: 480 - 16 - 96 = 368 px.
# 270 px <= 368 px! Fits!
# "Phase 2 move the code" -> 21 chars * 30 * 0.6 = 378 px > 368 px!
# What if for Phase 2:
# Title beside icon is: "Phase 2" (7 chars * 30 * 0.6 = 126 px)?
# BUT wait! Does test_migration_svg allow splitting "Phase 2" and "move the code over..."?
# In SVG:
# <text x="..." y="...">
#   <tspan x="..." dy="...">Phase 2 move the code</tspan> ...
# </text>
# Remember: test_migration_svg joins all tspans inside the <text> element!
# So we can break into whatever lines we want!
# But what if the icon is placed centered at the top, or placed at top-left with all text below it?
# Let's check:
# If icon is at x = x_card + 24, y = y_card + 20, size = 56x56 (ends at y_card + 76).
# Then text starts at y = y_card + 115, x = x_card + 24!
# Available text width across the card: 480 - 24 - 16 = 440 px!
# At 440 px:
# Phase 1:
# Line 1: "Phase 1 expand:" (15 chars, fs=30) -> 270 px
# Line 2: "add the new piece in a" (22 chars, fs=24) -> 316.8 px
# Line 3: "way old code ignores" (20 chars, fs=24) -> 288 px
# (or Line 2: "add the new piece in a way" 26 chars -> 374.4 px, Line 3: "old code ignores" 16 chars -> 230.4 px)
#
# Phase 2:
# Line 1: "Phase 2 move the code" (21 chars, fs=30) -> 378 px <= 440 px! (Right padding = 440 - 378 + 16 = 78 px!)
# Line 2: "over with serial rolling," (25 chars, fs=24) -> 360 px <= 440 px! (Right padding = 96 px!)
# Line 3: "old and new run side by side" (28 chars, fs=24) -> 403.2 px <= 440 px! (Right padding = 52.8 px!)
#
# Phase 3:
# Line 1: "Phase 3 contract:" (17 chars, fs=30) -> 306 px <= 440 px!
# Line 2: "later remove the old piece" (26 chars, fs=24) -> 374.4 px <= 440 px!

print("All lines comfortably fit within 440 px width!")
