#!/usr/bin/env python3

# Let's compute exact row heights:
# Header: 1 line (28px). Text height = 21px. Box height = 16 + 21 + 16 = 53 px. (Let's use 54 px).
# Baseline = box_top + 16 + 21 = box_top + 37.

# Rows:
# Row 1: max 2 lines -> h = 76
# Row 2: max 4 lines -> h = 128
# Row 3: max 2 lines -> h = 76
# Row 4: max 2 lines -> h = 76
# Row 5: max 1 line -> h = 52
# Row 6: max 1 line -> h = 52
# Row 7: max 2 lines -> h = 76
# Row 8: max 1 line -> h = 52
# Row 9: max 3 lines -> h = 102

rows = [
    ("Header", 54),
    ("Row 1", 76),
    ("Row 2", 128),
    ("Row 3", 76),
    ("Row 4", 76),
    ("Row 5", 52),
    ("Row 6", 52),
    ("Row 7", 76),
    ("Row 8", 52),
    ("Row 9", 102)
]

total_table = sum(h for _, h in rows)
print("Total table height:", total_table)
y_table_top = 75
y_table_bot = y_table_top + total_table
print(f"Table from {y_table_top} to {y_table_bot}")

# Below table:
# Remaining space in H=1200:
rem = 1200 - y_table_bot
print("Remaining height:", rem)
