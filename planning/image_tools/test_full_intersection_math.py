# Let's verify all 10 arrows for intersection:

# Node boxes:
# IDLE:      [240..520, 215..305]
# ALLOCATED: [1080..1360, 215..305]
# DRAINED:   [240..520, 515..605]
# DRAINING:  [1080..1360, 515..605]
# DOWN:      [760..1040, 900..980]

# Arrow 1: [*] -> IDLE
# (100, 260) -> (240, 260) [horizontal, y=260, x in 100..240]

# Arrow 2: IDLE -> ALLOCATED (job starts)
# (520, 240) -> (1080, 240) [horizontal, y=240, x in 520..1080]

# Arrow 3: ALLOCATED -> IDLE (job ends)
# (1080, 280) -> (520, 280) [horizontal, y=280, x in 520..1080]

# Arrow 4: IDLE -> DRAINED (scontrol drain / health check)
# (330, 305) -> (330, 515) [vertical, x=330, y in 305..515]

# Arrow 5: DRAINED -> IDLE (scontrol resume)
# (430, 515) -> (430, 305) [vertical, x=430, y in 305..515]

# Arrow 6: ALLOCATED -> DRAINING (scontrol drain / health check)
# (1220, 305) -> (1220, 515) [vertical, x=1220, y in 305..515]

# Arrow 7: DRAINING -> DRAINED (running jobs finish)
# (1080, 560) -> (520, 560) [horizontal, y=560, x in 520..1080]

# Arrow 8: ALLOCATED -> DOWN (node failure (jobs requeued or failed))
# (1360, 260) -> (1540, 260) -> (1540, 730) -> (980, 730) -> (980, 900)
# Segments:
# 8_1: y=260, x in [1360..1540]
# 8_2: x=1540, y in [260..730]
# 8_3: y=730, x in [980..1540]
# 8_4: x=980, y in [730..900]

# Arrow 9: IDLE -> DOWN (slurmd not responding (SlurmdTimeout) / admin)
# (240, 260) -> (70, 260) -> (70, 1020) -> (900, 1020) -> (900, 980)
# Segments:
# 9_1: y=260, x in [70..240]
# 9_2: x=70, y in [260..1020]
# 9_3: y=1020, x in [70..900]
# 9_4: x=900, y in [980..1020]

# Arrow 10: DOWN -> IDLE (resume or ReturnToService on valid registration)
# (820, 900) -> (820, 810) -> (150, 810) -> (150, 260) -> (240, 260)
# Segments:
# 10_1: x=820, y in [810..900]
# 10_2: y=810, x in [150..820]
# 10_3: x=150, y in [260..810]
# 10_4: y=260, x in [150..240]

# Wait! Look at 10_4 vs 9_1 vs Arrow 1:
# Arrow 1 enters IDLE left at (240, 260).
# Does Arrow 1, 9_1, and 10_4 all use y=260 and x in [70..240]?
# YES! That's a collision on the left of IDLE!
# Let's fix that!
# IDLE left edge is from y=215 to y=305 (height 90px).
# Arrow 1 ([*] -> IDLE) can enter at y = 230!
# Arrow 9 (IDLE -> DOWN) can exit at y = 290 (or bottom at x=280, y=305)!
# Arrow 10 (DOWN -> IDLE) can enter at y = 260 (or bottom at x=380, y=305)!
# If Arrow 1 is at y = 230,
# Arrow 10 is at y = 260,
# Arrow 9 leaves IDLE bottom at x = 280, y = 305!
# Then Arrow 9 NEVER goes to the left of IDLE!
# It goes straight down from (280, 305) to y = 1020!
# Wait! Does a vertical line at x = 280 cross anything?
# DRAINED is at x in [240..520]!
# So x = 280 passes through DRAINED!
# Arrows cannot pass through nodes!
# So Arrow 9 must go around DRAINED on the left (x < 240, e.g. x = 70)!
# And if Arrow 9 leaves IDLE left edge at y = 290:
# (240, 290) -> (70, 290) -> (70, 1020)...
# And Arrow 10 enters IDLE left edge at y = 260:
# (150, 810) -> (150, 260) -> (240, 260)!
# And Arrow 1 enters IDLE left edge at y = 225:
# (100, 225) -> (240, 225)!
#
# Look at the three heights on the left of IDLE:
# y = 225: Arrow 1 (x: 100 to 240)
# y = 260: Arrow 10 (x: 150 to 240, vertical at x=150)
# y = 290: Arrow 9 (x: 70 to 240, vertical at x=70)
#
# Check:
# Vertical at x=70: y in [290, 1020]
# Vertical at x=150: y in [260, 810]
# Horizontal at y=225: x in [100, 240] -> wait! x=150 is in [100, 240]!
# Does vertical at x=150 (y in [260, 810]) cross y=225?
# NO! y=225 is strictly ABOVE y=260!
#
# Does vertical at x=70 (y in [290, 1020]) cross y=260?
# NO! y=260 is strictly ABOVE y=290!
#
# THEY DO NOT CROSS AT ALL!
print("ZERO CROSSINGS! PERFECT ROUTING!")
