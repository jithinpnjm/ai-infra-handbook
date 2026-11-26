title_top = 40
title_b1 = 74
title_b2 = 124
title_bot = 132

analogy_y = 148
analogy_h = 44
analogy_bot = analogy_y + analogy_h # 192

gap_analogy_main = 40
main_y = analogy_bot + gap_analogy_main # 232
main_h = 580
main_bot = main_y + main_h # 812

gap_main_cmd = 40
cmd_y = main_bot + gap_main_cmd # 852
cmd_h = 218
cmd_bot = cmd_y + cmd_h # 1070

gap_cmd_bottom_bar = 40
bar_y = cmd_bot + gap_cmd_bottom_bar # 1110
bar_h = 44
bar_bot = bar_y + bar_h # 1154

margin_bottom = 1200 - bar_bot # 46

print(f"Title top: {title_top}")
print(f"Analogy: {analogy_y}..{analogy_bot} (h={analogy_h})")
print(f"Gap Analogy->Main: {gap_analogy_main}")
print(f"Main: {main_y}..{main_bot} (h={main_h})")
print(f"Gap Main->Cmd: {gap_main_cmd}")
print(f"Command strip: {cmd_y}..{cmd_bot} (h={cmd_h})")
print(f"Gap Cmd->Bar: {gap_cmd_bottom_bar}")
print(f"Bottom bar: {bar_y}..{bar_bot} (h={bar_h})")
print(f"Bottom margin: {margin_bottom}")

assert gap_analogy_main >= 40
assert gap_main_cmd >= 40
assert gap_cmd_bottom_bar >= 40
assert margin_bottom >= 40
print("ALL CONSTRAINTS PERFECTLY SATISFIED!")
