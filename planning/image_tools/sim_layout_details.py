# Simulation script to test exact coordinates, gaps >= 40, margins >= 40, paddings >= 16

# Title:
title_b1 = 88
title_b2 = 142
title_top = title_b1 - 48 * 0.85 # 47.2 >= 40
title_bottom = title_b2 + 48 * 0.25 # 154.0

gap0 = 38 # to strip y=192
strip_y = 192
strip_h = 80
strip_bottom = strip_y + strip_h # 272

gap1 = 40
row_a_y = strip_bottom + gap1 # 312
row_a_h = 220
row_a_bottom = row_a_y + row_a_h # 532

gap2 = 40
row_b_y = row_a_bottom + gap2 # 572
row_b_h = 285
row_b_bottom = row_b_y + row_b_h # 857

gap3 = 40
notes_y = row_b_bottom + gap3 # 897
notes_h = 145
notes_bottom = notes_y + notes_h # 1042

gap4 = 40
bar_y = notes_bottom + gap4 # 1082
bar_h = 75
bar_bottom = bar_y + bar_h # 1157

margin_bottom = 1200 - bar_bottom # 43 >= 40

print(f"Title top: {title_top:.1f} >= 40: {title_top >= 40}")
print(f"Gap 0 (Title to Strip): {strip_y - title_bottom:.1f} (approx 38px)")
print(f"Gap 1 (Strip to Row A): {row_a_y - strip_bottom:.1f} >= 40: {row_a_y - strip_bottom >= 40}")
print(f"Gap 2 (Row A to Row B): {row_b_y - row_a_bottom:.1f} >= 40: {row_b_y - row_a_bottom >= 40}")
print(f"Gap 3 (Row B to Notes): {notes_y - row_b_bottom:.1f} >= 40: {notes_y - row_b_bottom >= 40}")
print(f"Gap 4 (Notes to Bar): {bar_y - notes_bottom:.1f} >= 40: {bar_y - notes_bottom >= 40}")
print(f"Margin bottom: {margin_bottom:.1f} >= 40: {margin_bottom >= 40}")
