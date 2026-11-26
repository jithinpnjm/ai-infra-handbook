# Let's solve the exact geometry:

# Canvas width = 1600, H = 1050 (or 1040)
# Arrow: x = 50, y = 140 to 935.
# Arrow label: 'Each rung down costs more'
# Line 1: 'Each rung down ' (15 chars) * 14.4 = 216 px
# Line 2: 'costs more' (10 chars) * 14.4 = 144 px
# Label at x = 75: ends at 75 + 216 = 291 px.
# Left margin of ladder rungs: rx = 330! (gap 330 - 291 = 39 px -> let rx = 340, text at x = 70 -> gap = 340 - 286 = 54 px >= 40 px!)

# Inside each rung:
# rx = 330 (or 320)
# Icon: width 56, x = rx + 16 to rx + 72.
# Text starts at x = rx + 90 = 410 (or 420).
# Icon clearance: 90 - 72 = 18 px >= 16 px!

# Left text lengths:
# 1: "L1 cache reference: " -> 20 chars -> 288 px. Ends at 410 + 288 = 698 px.
# 2: "Main memory reference: " -> 23 chars -> 331.2 px. Ends at 410 + 331.2 = 741.2 px.
# 3: "Send 2K bytes over 1 Gbps network: " -> 34 chars -> 489.6 px. Ends at 410 + 489.6 = 899.6 px.
# 4: "Round trip within same datacenter: " -> 35 chars -> 504 px. Ends at 410 + 504 = 914 px.
# 5: "Disk seek: " -> 11 chars -> 158.4 px. Ends at 410 + 158.4 = 568.4 px.
# 6: "Send packet CA to Netherlands and back: " -> 40 chars -> 576 px. Ends at 410 + 576 = 986 px.

# Right text lengths:
# 1: "0.5 ns, ratio 0.005" -> 19 chars -> 273.6 px.
# 2: "100 ns, ratio 1" -> 16 chars -> 230.4 px.
# 3: "20,000 ns, ratio 200" -> 20 chars -> 288 px.
# 4: "500,000 ns, ratio 5,000" -> 22 chars -> 316.8 px.
# 5: "10,000,000 ns, ratio 100,000" -> 28 chars -> 403.2 px.
# 6: "150,000,000 ns, ratio 1,500,000" -> 31 chars -> 446.4 px.

# Let's set r_start with col_gap >= 24 px:
# 1: r_start = 724. r_end = 724 + 273.6 = 997.6 px.
#    rw must be at least 997.6 + 20 - 320 = 697.6 -> let rw = 710! (box ends at 320 + 710 = 1030).
#    Right pad = 1030 - 997.6 = 32.4 px >= 16 px!

# 2: r_start = 766. r_end = 766 + 230.4 = 996.4 px.
#    In rung 2, badge is at rx + rw - 70.
#    We need badge_x - r_end >= 16 px -> badge_x >= 1012.4.
#    rx + rw - 70 >= 1013 -> rx + rw >= 1083 -> let rw = 790! (box ends at 320 + 790 = 1110).
#    badge_x = 1110 - 70 = 1040. Clearance badge to text = 1040 - 996.4 = 43.6 px >= 16 px!

# 3: r_start = 924. r_end = 924 + 288 = 1212 px.
#    rw must be at least 1212 + 20 - 320 = 912 -> let rw = 920! (box ends at 1240).
#    Right pad = 1240 - 1212 = 28 px >= 16 px!

# 4: r_start = 938. r_end = 938 + 316.8 = 1254.8 px.
#    rw must be at least 1254.8 + 20 - 320 = 954.8 -> let rw = 1030! (box ends at 1350).
#    Right pad = 1350 - 1254.8 = 95.2 px >= 16 px!

# 5: r_start = 938. r_end = 938 + 403.2 = 1341.2 px.
#    rw must be at least 1341.2 + 20 - 320 = 1041.2 -> let rw = 1140! (box ends at 1460).
#    Right pad = 1460 - 1341.2 = 118.8 px >= 16 px!

# 6: r_start = 1010. r_end = 1010 + 446.4 = 1456.4 px.
#    rw must be at least 1456.4 + 20 - 320 = 1156.4 -> let rw = 1240! (box ends at 1560).
#    Right pad = 1560 - 1456.4 = 103.6 px >= 16 px!
#    Right margin to canvas edge 1600 = 1600 - 1560 = 40 px!

# Now let's check Card Note:
# Position: x = 1080, y = 140, w = 480, h = 120.
# Left edge: 1080.
# Rung 1 ends at 1030: Gap Rung 1 to Card = 1080 - 1030 = 50 px >= 40 px!
# Card ends vertically at y = 140 + 120 = 260.
# Rung 2 starts at y = 300! (y = 300 to 390).
# Vertical gap Card bottom (260) to Rung 2 top (300) = 40 px >= 40 px!
# And inside Card:
# Text:
# Line 1: baseline 173 -> top ~ 155. Top pad = 155 - 140 = 15 px -> let h = 126, y = 135!
# y = 135 to 260.
# Line 1: baseline 172. Top pad: 172 - 18 - 135 = 19 px >= 16 px!
# Line 3: baseline 236. Bot pad: 260 - (236 + 6) = 18 px >= 16 px!
# Card bottom is 260. Rung 2 starts at 300: 300 - 260 = 40 px!

print("All clearances and paddings verified mathematically!")
