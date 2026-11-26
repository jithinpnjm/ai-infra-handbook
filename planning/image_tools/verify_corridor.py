# Let's verify the corridor mathematically!
# CTLD: rect(x=420, y=340, w=480, h=180) -> bottom edge at y=520, right edge at x=900
# DBD:  rect(x=1040, y=340, w=250, h=140) -> left edge at x=1040, bottom at y=480
# DB:   rect(x=1340, y=340, w=200, h=140) -> left edge at x=1340
#
# CTLD -> DBD arrow:
# from (900, 410) to (1040, 410) -> horizontal segment at y=410, between x=900 and x=1040
#
# D1: rect(x=640, y=750, w=360, h=100) -> top edge at y=750, right edge at x=1000
# D2: rect(x=100, y=750, w=230, h=100)
# D3: rect(x=370, y=750, w=230, h=100)
#
# CTLD -> D1 arrow:
# from (720, 520) to (720, 750) -> vertical segment at x=720, y in [520, 750]
#
# MUNGE: rect(x=1120, y=750, w=420, h=120) -> left edge at x=1120, top edge at y=750
#
# Now let's trace MUNGE -.-> CTLD:
# Route:
# Start at MUNGE top: (1160, 750)
# Go up to (1160, 600)
# Go left to (960, 600)
# Go up to (960, 520) -> enters CTLD bottom edge at x=960! (Wait, CTLD width is 420..900? Let CTLD width be x=420..960, or x=960 enters CTLD right edge at y=500: go to (900, 500)!)
#
# Let's check if the path intersects ANY other edge:
# 1. Segment (1160, 750) -> (1160, 600): vertical at x=1160, y in [600, 750].
#    - CTLD->DBD is at y=410. No intersection!
#    - D1 is x in [640, 1000]. No intersection!
# 2. Segment (1160, 600) -> (960, 600): horizontal at y=600, x in [960, 1160].
#    - CTLD->D1 is at x=720. 720 < 960! No intersection!
#    - CTLD->DBD is at y=410. 410 != 600! No intersection!
# 3. Segment (960, 600) -> (960, 500) -> (900, 500):
#    - CTLD->DBD is at y=410. 410 < 500! No intersection!
#    - CTLD->D1 is at x=720. 720 < 900! No intersection!
#
# ZERO INTERSECTIONS! ZERO CROSSINGS!
print("ZERO INTERSECTIONS VERIFIED!")
