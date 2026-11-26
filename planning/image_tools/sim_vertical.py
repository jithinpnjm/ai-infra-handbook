# Total Height budget: up to 1200 (or let's see if 1200 or 1250 is needed)
# "width 1600, viewBox 0 0 1600 H. Use H=900, or up to 1200 if the content needs more room."
# Let's check H=1200:
# Title at top:
# y = 40 to y = 140 (title text at 48px, 2 lines)
# Header row for columns: y = 160 to y = 220 (height = 60)
# Fabrics rows:
# Row 1 (Ethernet with TCP): 4 lines in fabric header, 2 lines in col 1, 2 lines in col 2, 2 lines in col 3.
# Row 2 (RoCE v2): 1 line fabric, 3 lines col 1, 1 line col 2, 4 lines col 3.
# Row 3 (InfiniBand): 1 line fabric, 3 lines col 1, 5 lines col 2, 4 lines col 3.
# Row 4 (NVLink): 2 lines fabric, 3 lines col 1, 2 lines col 2, 2 lines col 3.
# Row 5 (PCIe): 1 line fabric, 2 lines col 1, 1 line col 2, 2 lines col 3.

# Max lines per row:
# Row 1: 4 lines (Col 0) -> height ~ 150 px
# Row 2: 4 lines (Col 3) -> height ~ 150 px
# Row 3: 5 lines (Col 2) -> height ~ 165 px
# Row 4: 3 lines (Col 1) -> height ~ 135 px
# Row 5: 2 lines (Col 1/3) -> height ~ 115 px

# Sum of row heights = 150 + 150 + 165 + 135 + 115 = 715 px
# Gaps between rows: 4 gaps * 15 px = 60 px
# Total grid rows height = 775 px.
# Header row height = 50 px. Gap = 15 px.
# Total grid = 50 + 15 + 775 = 840 px.
# Y start = 170.
# Grid Y ends at 170 + 840 = 1010.
# Gap to bottom bar = 25 px.
# Bottom bar: Y = 1035, height = 80 px (ends at 1115).
# Canvas margin bottom = 40 px.
# 1115 + 40 = 1155 <= 1200!
# Everything fits comfortably within H=1200!
print("Fits within H=1200!")
