hy = 64
hh = 62
gap = 6
rh1 = 152
rh2 = 152
rh3 = 84
rh4 = 110
rh5 = 110
rh6 = 84

table_bottom = hy + hh + gap + rh1 + gap + rh2 + gap + rh3 + gap + rh4 + gap + rh5 + gap + rh6
print("Table bottom:", table_bottom)

story_y = table_bottom + 8
story_h = 56
rules_y = story_y + story_h + 8
rules_h = 82
time_y = rules_y + rules_h + 8
time_h = 136
bot_y = time_y + time_h + 8
bot_h = 58
total_h = bot_y + bot_h
print(f"Total H: {total_h}")
print(f"Margin at bottom before 1200: {1200 - total_h}")
