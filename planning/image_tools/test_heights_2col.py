# Height calculation:
# Title font: 30px bold, line-height 34px
# Conseq font: 24px, line-height 28px
# Resp font: 24px, line-height 28px

# In Left box (Diff):
# Top padding: 14px
# Title: tl * 34px
# Gap: 8px
# Conseq: cl * 28px
# Bottom padding: 14px
# h_diff = 14 + tl*34 + 8 + cl*28 + 14

# In Right box (Resp):
# Top padding: 16px
# Resp: rl * 28px
# Bottom padding: 16px
# h_resp = 16 + rl*28 + 16

configs = [
    (2, 5, 3), # Row 1
    (1, 4, 5), # Row 2
    (1, 6, 3), # Row 3
    (2, 3, 3), # Row 4
    (1, 3, 4), # Row 5
]

print("Row heights:")
row_heights = []
for i, (tl, cl, rl) in enumerate(configs):
    h_diff = 14 + tl * 34 + 8 + cl * 28 + 14
    h_resp = 16 + rl * 28 + 16
    h_row = max(h_diff, h_resp)
    row_heights.append(h_row)
    print(f"  Row {i+1}: diff={h_diff}, resp={h_resp} -> max={h_row}")

total_rows = sum(row_heights)
print("Total rows height:", total_rows)

# Available space:
# Canvas: 1200
# Title: y=38 to y=88 (ends at ~98)
# Left Scenario + Right Visual: y=108 to y=208 (height = 100)
# Gap: 14
# Rows start: y = 222
# Gaps between 5 rows: 4 * 12 = 48
# Rows end: 222 + total_rows + 48
rows_end = 222 + total_rows + 48
print("Rows end at:", rows_end)
print("Gap to bottom bar:", 1146 - rows_end)
print("Bottom bar at y=1146, height=44, ends at 1190.")
