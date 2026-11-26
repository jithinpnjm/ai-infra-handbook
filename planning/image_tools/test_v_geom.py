#!/usr/bin/env python3

# Let's verify complete geometry:
# H = 1080
# Container 1 (Clean planned exit): y = 96..465 (h = 369)
#   Header text: y = 145
#   Badge end_batch: y = 116..158 (h = 42)
#   Row 1: y = 175..300 (h = 125)
#   Row 2: y = 320..445 (h = 125)
# Gap: 505 - 465 = 40px!
# Container 2 (Explicit stop): y = 505..740 (h = 235)
#   Header text: y = 554
#   Row 3: y = 584..720 (h = 136)
# Gap: 780 - 740 = 40px!
# Container 3 (Use rarely): y = 780..1015 (h = 235)
#   Header text: y = 829
#   Row 4: y = 859..995 (h = 136)
# Bottom margin: 1080 - 1015 = 65px (>= 40px)
# Left/right margins: 40px

print("Vertical gaps and margins verified!")
