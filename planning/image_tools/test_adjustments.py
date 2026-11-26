import re, subprocess, json

# Adjustments:
# Task 3 box: height 130 (y=710, y2=840)
# Arrow Task 3 -> Task 4: y=840 to 868
# Task 4 box: y=870, height 155 (y2=1025)
# Red diamond center y: 947.5 (same as Task 4 center: 870 + 155/2 = 947.5!)
# Diamond: top tip: 947.5 - 100 = 847.5, bottom tip: 947.5 + 100 = 1047.5
# Left tip: 700, Right tip: 1120
# Arrow from Task 4 (x=660, y=947.5) to Diamond (x=700, y=947.5)
# Stage 5 box: height 200 (y=225, y2=425)
# Takeaway bar: y=1075, height 70 (y2=1145)
# Canvas H = 1200!
# Bottom margin = 1200 - 1145 = 55 px >= 40 px!
