# Let's check exact heights
title_y = 48
header_y = 78
header_h = 38

gap_row = 6

# Row heights:
# Row 1 (JSON, 5 lines): h = 148
# Row 2 (YAML, 5 lines): h = 148
# Row 3 (TOML, 2 lines): h = 80
# Row 4 (CSV, 3 lines):  h = 104
# Row 5 (INI, 2 lines):  h = 80
# Row 6 (Parquet, 2 lines): h = 76

r_heights = [148, 148, 80, 104, 80, 76]
table_content_h = sum(r_heights) + 5 * gap_row
table_total_h = header_h + 6 + table_content_h
table_bottom = header_y + table_total_h
print(f"Table starts at y={header_y}, ends at y={table_bottom} (total table h={table_total_h})")

# Remaining space up to 1200:
# Bottom bar: h = 48, y = 1144 to 1192 (bottom margin 8)
space_avail = 1144 - table_bottom
print(f"Space available between table and bottom bar: {space_avail}px")
