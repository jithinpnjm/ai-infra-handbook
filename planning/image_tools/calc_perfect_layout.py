# Let's calculate proper heights for all boxes so EVERY padding is >= 16px:

# For font-size fs:
# 1 line:  height >= fs + 32  (fs=30: h>=62; fs=24: h>=56)
# 2 lines: height >= fs + dy + 32 (fs=24, dy=26: h >= 24+26+32 = 82)
# 3 lines: height >= fs + 2*dy + 32 (fs=24, dy=26: h >= 24+52+32 = 108)
# 4 lines: height >= fs + 3*dy + 32 (fs=24, dy=26: h >= 24+78+32 = 134)
# 5 lines: height >= fs + 4*dy + 26 + 32 (fs=24, dy=25: h >= 24+100+32 = 156)
# 6 lines: height >= fs + 5*dy + 32 (fs=24, dy=25: h >= 24+125+32 = 181)

# Headers: fs=30 -> hh = 56 (text at hy + 38: top_pad = 38-22.5 = 15.5, let's use hh=60, text at hy+40: top_pad=17.5, bot_pad=12.5. hh=62, text at hy+41: top_pad=18.5, bot_pad=13.5. With hh=64, text at hy+42: top_pad=19.5, bot_pad=14.5. hh=66, text at hy+43: top_pad=20.5, bot_pad=15.5)

# Row 1 (JSON, 5 lines in trap): rh1 = 156 (dy=25)
# Row 2 (YAML, 5 lines in trap): rh2 = 156 (dy=25)
# Row 3 (TOML, 2 lines in safe call): rh3 = 84 (dy=26)
# Row 4 (CSV, 3 lines in trap): rh4 = 110 (dy=26)
# Row 5 (INI, 3 lines in safe call): rh5 = 110 (dy=26)
# Row 6 (Parquet, 2 lines in format): rh6 = 84 (dy=26)

# Story strip (1 line, fs=24): story_h = 58
# Rules strip (2 lines, fs=24, dy=26): rules_h = 84
# Time panel (6 lines, fs=24, dy=25): time_h = 184
# Bottom bar (1 line, fs=26): bot_h = 52

# Let's sum everything:
title_h = 60 # title at y=48
hy = 66
hh = 56
gap = 6

table_h = hh + gap + 156 + gap + 156 + gap + 84 + gap + 110 + gap + 110 + gap + 84
print("Table ends at:", hy + table_h)

y = hy + table_h + 10
print("Story starts at:", y)
y += 58 + 8
print("Rules starts at:", y)
y += 84 + 8
print("Time starts at:", y)
y += 184 + 8
print("Bottom bar starts at:", y)
y += 52
print("Total SVG height:", y)
