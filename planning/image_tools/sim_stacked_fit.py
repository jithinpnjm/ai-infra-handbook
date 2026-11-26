# Canvas: 1600 x 1200
# Stacked vertically:
# Node 1: Setup (or Title + Setup)
# Node 2: Table 1 (4 rows)
# Node 3: Table 2 (5 rows)
# Node 4: Reading Takeaway

# Height budget = 1200
# Gaps between nodes = 40px
# Top margin = 40px, Bottom margin = 40px

# Title: y = 55 (font 48px)
# Subtitle chip: x = 460, y = 78..126 (h = 48)
# Gap: 40px -> Node 1 (Setup) starts at y = 166

# Setup (Node 1):
# y = 166..250 (h = 84px)
# Gap: 40px -> Node 2 (Table 1) starts at y = 290

# Table 1 (Node 2):
# Needs: Header (1 line: "Table 1 policy: hit rate, p50 s, p99 s, max over mean load")
# + 4 rows
# Header: y = 305..350 (h = 45)
# 4 rows: each row h = 46, gap between rows = 8px
# Row 1: y = 360..406
# Row 2: y = 414..460
# Row 3: y = 468..514
# Row 4: y = 522..568
# Table 1 box bottom: y = 580 (total h = 290)
# Gap: 40px -> Node 3 (Table 2) starts at y = 620

# Table 2 (Node 3):
# Needs: Header ("Table 2 bound in seconds of backlog")
# + 5 rows
# Header: y = 635..680 (h = 45)
# 5 rows: each row h = 46, gap between rows = 8px
# Row 1: y = 690..736
# Row 2: y = 744..790
# Row 3: y = 798..844
# Row 4: y = 852..898
# Row 5: y = 906..952
# Table 2 box bottom: y = 964 (total h = 344)
# Gap: 40px -> Node 4 (Takeaway) starts at y = 1004

# Takeaway (Node 4):
# y = 1004..1155 (h = 151)
# Bottom margin: 1200 - 1155 = 45px >= 40px!

print("PERFECT FIT:")
print(f"Top margin: 40px")
print(f"Node 1 (Setup): y = 166..250 (h = 84)")
print(f"Gap 1-2: 40px")
print(f"Node 2 (Table 1): y = 290..580 (h = 290)")
print(f"Gap 2-3: 40px")
print(f"Node 3 (Table 2): y = 620..964 (h = 344)")
print(f"Gap 3-4: 40px")
print(f"Node 4 (Takeaway): y = 1004..1155 (h = 151)")
print(f"Bottom margin: {1200 - 1155}px >= 40px")
