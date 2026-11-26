title_bottom = 125
analogy_h = 44
analogy_top = title_bottom + 40 # 165
analogy_bottom = analogy_top + analogy_h # 209

main_top = analogy_bottom + 40 # 249
main_h = 580 # let's test 580 or 600
main_bottom = main_top + main_h

cmd_top = main_bottom + 40
cmd_h = 190
cmd_bottom = cmd_top + cmd_h

bottom_bar_top = cmd_bottom + 40
bottom_bar_h = 44
bottom_bar_bottom = bottom_bar_top + bottom_bar_h

margin_bottom = 1200 - bottom_bar_bottom
print(f"main_h = {main_h} -> bottom margin = {margin_bottom}px")
