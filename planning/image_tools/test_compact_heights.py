configs = [
    (2, 5, 3), # Row 1
    (1, 4, 5), # Row 2
    (1, 6, 3), # Row 3
    (2, 3, 3), # Row 4
    (1, 3, 4), # Row 5
]

# Let's test:
# Title font: 30px bold, line-height 30px
# Conseq font: 24px, line-height 25px
# Resp font: 24px, line-height 25px
# Padding: 12px top, 12px bottom, 4px between = 28px

row_heights = []
for i, (tl, cl, rl) in enumerate(configs):
    h_diff = 24 + tl * 30 + 4 + cl * 25
    h_resp = 24 + rl * 25
    h_row = max(h_diff, h_resp)
    row_heights.append(h_row)
    print(f"Row {i+1}: diff={h_diff}, resp={h_resp} -> max={h_row}")

total_rows = sum(row_heights)
print("Total rows:", total_rows)
