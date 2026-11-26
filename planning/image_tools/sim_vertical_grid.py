# Let's verify row coordinates:
# Margins: left=40, right=1560. Available width = 1520.
# Left col: x=40, width=860 (from 40 to 900)
# Gap between cols: 40px (from 900 to 940)
# Right col: x=940, width=620 (from 940 to 1560)

# Let's check each row:
# Row 1: CLI & Exit Codes
# Left: cli.py
# y = 95, h = 120 (ends y=215)
# Right: Exit code table
# y = 95, h = 220? Wait!
# If Exit code table is y=95, h=220, then it ends at y=315!
# But what about collect.py?
# If collect.py starts at y=255, h=140 (ends y=395)
# And models.py on the right: starts at y=335, h=100 (ends y=435)?
# Wait! Let's check how the rows align.

