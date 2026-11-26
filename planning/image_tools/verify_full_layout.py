# Verify all vertical gaps and margins

margin_top = 40
title_y1 = 65
title_y2 = 115
title_bottom = 125

gap_1 = 40
analogy_top = title_bottom + gap_1 # 165
analogy_h = 50
analogy_bottom = analogy_top + analogy_h # 215

gap_2 = 40
main_top = analogy_bottom + gap_2 # 255
main_h = 560
main_bottom = main_top + main_h # 815

gap_3 = 40
cmd_top = main_bottom + gap_3 # 855
cmd_h = 190
cmd_bottom = cmd_top + cmd_h # 1045

gap_4 = 40
bottom_bar_top = cmd_bottom + gap_4 # 1085
bottom_bar_h = 45
bottom_bar_bottom = bottom_bar_top + bottom_bar_h # 1130

margin_bottom = 1200 - bottom_bar_bottom # 70

print(f"Top margin: {margin_top}px")
print(f"Gap Title -> Analogy: {gap_1}px")
print(f"Gap Analogy -> Main: {gap_2}px")
print(f"Gap Main -> Commands: {gap_3}px")
print(f"Gap Commands -> Bottom Bar: {gap_4}px")
print(f"Bottom margin: {margin_bottom}px")
assert margin_top >= 40
assert gap_1 >= 40
assert gap_2 >= 40
assert gap_3 >= 40
assert gap_4 >= 40
assert margin_bottom >= 40
print("ALL GAPS AND MARGINS >= 40px CONFIRMED!")
