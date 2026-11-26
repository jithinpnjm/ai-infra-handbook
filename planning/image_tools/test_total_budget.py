# Total height test
title_y = 48
hy = 68
hh = 52 # header height
gap = 6

# Row heights:
# Row 1 (JSON, 5 lines, dy=24): rh1 = 144
# Row 2 (YAML, 5 lines, dy=24): rh2 = 144
# Row 3 (TOML, 2 lines, dy=26): rh3 = 80
# Row 4 (CSV, 3 lines, dy=26): rh4 = 104
# Row 5 (INI, 3 lines, dy=24): rh5 = 100
# Row 6 (Parquet, 2 lines, dy=24): rh6 = 76

rh1 = 144
rh2 = 144
rh3 = 80
rh4 = 104
rh5 = 100
rh6 = 76

table_h = hh + gap + rh1 + gap + rh2 + gap + rh3 + gap + rh4 + gap + rh5 + gap + rh6
table_bottom = hy + table_h
print("Table bottom:", table_bottom)

# Story strip: h=54
story_y = table_bottom + 10
story_h = 54
print("Story bottom:", story_y + story_h)

# Rules strip: h=76
rules_y = story_y + story_h + 8
rules_h = 76
print("Rules bottom:", rules_y + rules_h)

# Time panel: h=136 (4 lines, dy=25: 3*25 + 24 = 99px, 99 + 37 = 136px)
time_y = rules_y + rules_h + 8
time_h = 136
print("Time bottom:", time_y + time_h)

# Bottom bar: h=52
bot_y = time_y + time_h + 8
bot_h = 52
print("Bottom bar bottom:", bot_y + bot_h)
print("Canvas height remaining before 1200:", 1200 - (bot_y + bot_h))
