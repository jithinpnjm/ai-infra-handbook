import re
import xml.etree.ElementTree as ET

# Let's test the tightened coordinates:
# Header:
# y = 100, h = 44 (ends at 144)
# Rows start at y = 150
# row_gap = 6

rows_data = [
    ("exceptions", 3, 2, 104),
    ("files", 4, 2, 130),
    ("subprocess", 6, 3, 178),
    ("global_state", 3, 2, 104),
    ("reruns", 1, 3, 104),
    ("signals", 2, 1, 78),
    ("untrusted_input", 3, 2, 104)
]

cur_y = 150
for name, m, f, rh in rows_data:
    print(f"{name:15s}: y={cur_y:4d}..{cur_y+rh:4d} (rh={rh})")
    cur_y += rh + 6

table_end = cur_y - 6
print(f"Table ends at {table_end}")

stories_y = table_end + 12
stories_h = 76
print(f"Stories strip:  y={stories_y:4d}..{stories_y+stories_h:4d} (h={stories_h})")

bottom_y = stories_y + stories_h + 12
bottom_h = 50
print(f"Bottom bar:     y={bottom_y:4d}..{bottom_y+bottom_h:4d} (h={bottom_h})")
print(f"Margin to 1200: {1200 - (bottom_y + bottom_h)}px")
assert bottom_y + bottom_h <= 1200
