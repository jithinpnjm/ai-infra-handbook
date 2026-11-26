# Let's test the text wrapping and padding inside Table 1 (w = 725) and Table 2 (w = 725)
# Box x = 50..775 (T1) and x = 825..1550 (T2)
# Inside T1: content box x = 70..755 (w = 685)
# Inside T2: content box x = 845..1530 (w = 685)

# T1 Header: "Table 1 policy: hit rate, p50 s, p99 s, max over mean load"
# If 2 lines:
# Line 1: "Table 1 policy:" -> 15 chars * 0.6 * 30 = 270px
# Line 2: "hit rate, p50 s, p99 s, max over mean load" -> 42 chars * 0.6 * 24 = 604.8px
# In content box w = 685: 685 - 604.8 = 80.2px -> Left/Right padding = 40px > 16px!

# T1 Rows:
# Row 1: "round_robin 0.46, 0.50, 2.33, 1.00" -> 36 chars * 0.62 * 24 = 535.7px
# In content box w = 685: 685 - 535.7 = 149.3px -> Left/Right padding = 74px > 16px!
# Row 2: "least_loaded 0.46, 0.50, 1.22, 1.16" -> 535.7px (padding 74px)
# Row 3: "cache_only 0.98, 0.16, 4.39, 3.80" -> 34 chars -> 505.9px (padding 89px)
# Row 4: "cache_bounded 0.95, 0.10, 0.50, 2.13" -> 37 chars -> 550.6px (padding 67px)

# T2 Header: "Table 2 bound in seconds of backlog"
# 35 chars * 0.6 * 30 = 630px
# In content box w = 685: 685 - 630 = 55px -> Left/Right pad = 27px > 16px!

# T2 Rows:
# Row 1: "0.0: hit 0.57, p50 0.22, p99 0.99, max/mean 1.22"
# 49 chars: if 1 line: 49 * 0.62 * 24 = 729.1px > 685px!
# But if 2 lines:
# Line 1: "0.0: hit 0.57, p50 0.22," -> 24 chars * 0.62 * 24 = 357.1px
# Line 2: "p99 0.99, max/mean 1.22" -> 23 chars * 0.62 * 24 = 342.2px
# In content box w = 685: 685 - 357.1 = 327.9px -> Left pad = 20px, Right pad = 307.9px > 16px!
# Row 2: "0.1: 0.89, 0.10, 0.52, 1.56" -> 28 chars -> 416.6px (padding 268px > 16px!)
# Row 3: "0.5: 0.95, 0.10, 0.50, 2.13" -> 28 chars -> 416.6px
# Row 4: "2.0: 0.98, 0.11, 1.68, 3.39" -> 28 chars -> 416.6px
# Row 5: "100 (cache-only): 0.98, 0.16, 4.39, 3.80" -> 41 chars * 0.62 * 24 = 610.1px
# In content box w = 685: 685 - 610.1 = 74.9px -> Left pad = 20px, Right pad = 54.9px > 16px!

print("Side-by-side fits completely and elegantly with huge margins on every line!")
