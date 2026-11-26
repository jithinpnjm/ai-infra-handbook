# Test layout adjustments for all failing items

# 1. Right fix list:
# If width = 460 (x: 1090..1550)
# Let text start at x = 1115 (left pad = 25px)
# In Fix 2:
# "set the application backlog too, such as nginx listen ... backlog="
# If split into 3 lines:
# Line 1: "set the application" (19 chars * 14.4 = 273.6 px)
# Line 2: "backlog too, such as" (20 chars * 14.4 = 288 px)
# Line 3: "nginx listen ... backlog=" (25 chars * 14.88 = 372 px)
# Max line is 372 px!
# 1115 + 372 = 1487.
# Right pad = 1550 - 1487 = 63 px!
# And where is the icon?
# Placed above or beside! E.g. at x = 1460, y = 350 (size 56px, stroke 4).
# Wait, if icon is at top-right (x = 1460), Line 3 is at y = 450, icon is at y = 350.
# At y = 350, Line 1 is "set the application" which ends at 1115 + 273.6 = 1388.6 < 1460!
# No overlap at all!

# In Fix 4:
# "fix any slow accept() loop, because that loop is what fills the queue"
# If split into 3 lines:
# Line 1: "fix any slow accept() loop," (27 chars = 388.8 px)
# Line 2: "because that loop is what" (25 chars = 360 px)
# Line 3: "fills the queue" (15 chars = 216 px)
# 1115 + 388.8 = 1503.8.
# Right pad = 1550 - 1503.8 = 46.2 px >= 16 px!

# In Fix 5:
# "ss -ltn shows queue length in Recv-Q"
# If split into 2 lines:
# Line 1: "ss -ltn shows" (13 chars = 195 px)
# Line 2: "queue length in Recv-Q" (22 chars * 14.88 = 327.4 px)
# 1115 + 327.4 = 1442.4. Right pad = 1550 - 1442.4 = 107.6 px!

print("Testing text layout logic")
