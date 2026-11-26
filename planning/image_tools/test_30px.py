# If font-size is 26px vs 30px:
# At 30px, 0.6 * 30 = 18 px/char.
# Line 1: inventory entry gpu001 with its (31 chars * 18 = 558 px)
# Line 2: ansible_host value, and the (27 chars * 18 = 486 px)
# Line 3: cluster_domain variable (23 chars * 18 = 414 px)
# Available text width in 680px card with icon:
# Card width = 680 (x=850 to 1530). Icon at x=880..936. Text at x=960.
# Available width = 1530 - 960 - 20 = 550 px.
# 558 px might be tight against 550 px!
# But what if Card width = 700 px (x=840 to 1540), text at x=940?
# Available width = 1540 - 940 - 20 = 580 px!
# 558 px fits in 580 px with 22 px padding!
print("Calculated 30px fit")
