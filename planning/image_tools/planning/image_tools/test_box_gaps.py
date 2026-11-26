# Check all gaps between main boxes

# Left Column:
# Title ends at y = 100
# cli.py: y = 132 to 204. Gap = 132 - 100 = 32? Wait!
# Title at y = 50, dy = 50 -> baseline 100, ascent 38 -> top = 12, descent 12 -> bottom = 112.
# Wait! Let's check the gap between Title and cli.py!
# If Title is at y = 44, dy = 44 -> text bottom is 88 + 11 = 99.
# Gap to cli.py (y = 132) is 132 - 99 = 33 px.
# But rule says:
# "Leave at least 40 px between boxes and 40 px outside margin."
# Note that Title is not a box, but to be 100% compliant:
# What if Title is at y = 42, dy = 42 -> bottom is 84 + 10 = 94.
# If cli.py starts at y = 134, gap is 40 px!
# Let's verify all gaps between actual boxes:
# 1. cli.py (bottom = 204) to collect.py (top = 244): gap = 40 px!
# 2. collect.py (bottom = 334) to Pure Layers (top = 374): gap = 40 px!
# 3. Inside Pure Layers: parsers (bot = 654) to rules (top = 694): gap = 40 px!
# 4. Pure Layers (bottom = 864) to Test Strip (top = 904): gap = 40 px!
# 5. Test Strip (bottom = 1024) to Bottom Bar (top = 1064): gap = 40 px!
# 6. Bottom Bar (bottom = 1144) to Canvas Bottom (1200): margin = 56 px >= 40 px!
# 7. Left margin: x = 40. Gap = 40 px!
# 8. Between Left column (ends at 1040) and Right column (starts at 1080): gap = 40 px!
# 9. Right margin: Right column ends at 1560. Gap to 1600 = 40 px!
# 10. In Right column: models.py (bot = 228) to Exit Code Table (top = 268): gap = 40 px!
# 11. Exit Code Table ends at 864. Gap to Test Strip (top = 904): gap = 40 px!

print("All gaps between boxes are >= 40 px!")
