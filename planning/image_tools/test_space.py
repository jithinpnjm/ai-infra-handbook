# Title ends at 104
# Gap 1: 40 -> Lanes top = 144
# Lanes height = 356 -> Lanes bottom = 500
# Gap 2: 40 -> Fix top = 540
# Fix height = 130 -> Fix bottom = 670
# Gap 3: 40 -> Checks top = 710
# Gap 4: 40 -> Rules
# Gap 5: 40 -> Bar
# Bar ends at <= 1160 (so Bar top = 1104, Bar h = 56).
# From Checks top (710) to Bar top (1104):
# Total space = 1104 - 710 = 394px!
# Between Checks and Rules: 40px gap.
# Between Rules and Bar: 40px gap.
# So space for Checks + Rules = 394 - 80 = 314px!
print(f"Space for Checks + Rules: {314}px")
