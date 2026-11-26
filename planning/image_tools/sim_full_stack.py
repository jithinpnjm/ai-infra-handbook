# Layout plan:
# Canvas: 1600 x H

# 1. Title: y = 60
# Title height: ~80

# 2. Gates row (two cards side by side): y = 100 to y = 200 (height = 100)
# Card 1 (Latency): x=50, y=100, w=730, h=100
# Card 2 (Quality): x=820, y=100, w=730, h=100

# 3. Decision Rules (Rules top to bottom, 4 stacked cards, width=1500):
# Gap: 20px -> starts at y = 220
# Rule 1 (Hard failures rollback): y = 220, h = 145 (3 lines) [ORANGE BORDER]
# Gap: 15px -> y = 380
# Rule 2 (Below minimum requests): y = 380, h = 80 (1 line)
# Gap: 15px -> y = 475
# Rule 3 (Soft signals hold): y = 475, h = 95 (2 lines)
# Gap: 15px -> y = 585
# Rule 4 (Otherwise promote): y = 585, h = 75 (1 line)

# 4. Operational Rules (two cards side by side, width=730 each):
# Gap: 20px -> starts at y = 680
# Card 1 (Prefix cache): x=50, y=680, w=730, h=125 (3 lines)
# Card 2 (Router weights): x=820, y=680, w=730, h=125 (2 lines)

# 5. Takeaway bar / Reasons (full width 1500):
# Gap: 20px -> starts at y = 825
# Takeaway bar: x=50, y=825, w=1500, h=110 (2 lines)
# Total height = 825 + 110 + 45 = 980 px!

# Check canvas constraint:
# 900 <= H <= 1200
# 980 (or 1000 or 1050) is absolutely gorgeous!
print("Total H = 1000 fits perfectly within 900 <= H <= 1200!")
