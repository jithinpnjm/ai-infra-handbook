# test_saving_20px.py

H = 1200

title_y = 42

hdr_y = 60
hdr_h = 38
# Table rows:
row_y_start = 104
gap_row = 4

row_heights = [86, 62, 62, 62, 62, 62, 86, 86, 86, 62, 62, 86]
current_y = row_y_start
row_coords = []
for i, rh in enumerate(row_heights, 1):
    row_coords.append((i, current_y, rh))
    current_y += rh + gap_row

table_end = current_y - gap_row
print(f"Table ends at y = {table_end}")

we_gap = 8
we_y = table_end + we_gap
we_h = 86
we_end = we_y + we_h
print(f"Worked example: y={we_y} to {we_end} (h={we_h})")

bb_gap = 8
bb_y = we_end + bb_gap
bb_h = 62
bb_end = bb_y + bb_h
print(f"Bottom bar: y={bb_y} to {bb_end} (h={bb_h})")
print(f"Margin to canvas bottom (1200): {1200 - bb_end} px")
