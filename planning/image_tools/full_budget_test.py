# Let's write out exact y coordinates for every element and box
# We want H = 1200 or less, viewBox="0 0 1600 1200".
# Canvas margin = 40.
# Box margin / gap >= 40.

# Let's see:
# Top margin = 40.
# Title text:
# y = 68 (line 1), y = 114 (line 2)
# Bottom of title = 125.

# Distance to Host container:
# y = 145. (gap from title = 20-30px, or 40px? Title is text. Let's make gap = 30px -> y = 145)

# Host container:
# x = 40, width = 1520.
# What is the height of Host container?
# Inside Host container:
# 1. Host header row with 4 shared nodes:
#    - c1 (10.10.0.11)
#    - br0 (10.10.0.1/24)
#    - c2 (10.10.0.12)
#    - uplink NIC
#    y_top = 160, h = 60.
# 2. Lane 1:
#    y_top = 235, h = 180.
# 3. Lane 2:
#    y_top = 430, h = 265.
# 4. Lane 3:
#    y_top = 710, h = 125.
# Bottom of Host container = 850! (Total Host container height = 850 - 145 = 705)

# Then outside Host container:
# Gap = 20-30px? Wait! What does the rule say?
# "Leave at least 40 px between boxes and 40 px outside margin."
# Let's check this carefully!
# If rule says: "Leave at least 40 px between boxes and 40 px outside margin."
# If Host container ends at y = 850:
# Gap of 40px -> next box starts at y = 890!
# Next box: Footer & Docker note box:
# y = 890 to y = 1070 (h = 180)
# Gap of 40px -> next box starts at y = 1110!
# Next box: Takeaway Bottom bar:
# y = 1110 to y = 1160 (h = 50)
# Bottom margin = 1200 - 1160 = 40 px! EXACTLY 40 PX!
print("850 + 40 = 890")
print("890 + 180 = 1070")
print("1070 + 40 = 1110")
print("1110 + 50 = 1160")
print("1200 - 1160 = 40")
