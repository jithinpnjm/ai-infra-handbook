# Total canvas H = 1200
# Outside margins: top >= 40, bottom >= 40, left >= 40, right >= 40
# Inter-box gaps >= 40

# Title: y = 50, 104 (spans y = 25 to 115)
# Title to Section 1: y = 145 (gap from text baseline 104 is 41px, box starts at 145)

# If Section 1 height = 180:
# y = 145 .. 325 (h = 180)
# Gap = 40
# Section 2: y = 365 .. 795 (h = 430)
# Gap = 40
# Section 3: y = 835 .. 1075 (h = 240)
# Gap = 40
# Section 4 (Takeaway): y = 1115 .. 1175 (h = 60)
# Margin to bottom: 1200 - 1175 = 25px
# WAIT! The bottom margin is 25px, but rule says:
# "Leave at least 40 px between boxes and 40 px outside margin."
# So bottom margin MUST BE >= 40px! That means Section 4 must end at y <= 1160!

print("Testing with bottom ending at 1155 (outside margin = 45 >= 40):")
# Available vertical span for boxes:
# From y = 140 to y = 1155 (total = 1015 px)
# There are 4 sections (Sec 1, Sec 2, Sec 3, Sec 4)
# Between them are 3 gaps of >= 40px = 120px
# Remaining height for the 4 boxes = 1015 - 120 = 895 px.
# Let's see:
# Sec 4 (Takeaway bar): 60px
# Remaining for Sec 1, 2, 3: 895 - 60 = 835 px!
# How to divide 835 px among Sec 1, Sec 2, Sec 3?
# For example:
# Sec 1: 175 px
# Sec 2: 430 px
# Sec 3: 230 px
# Total = 175 + 430 + 230 = 835 px! Exact!

s1_y = 140
s1_h = 175
s2_y = s1_y + s1_h + 40 # 355
s2_h = 430
s3_y = s2_y + s2_h + 40 # 825
s3_h = 230
s4_y = s3_y + s3_h + 40 # 1095
s4_h = 60
s4_bottom = s4_y + s4_h # 1155
bottom_margin = 1200 - s4_bottom # 45

print(f"Sec 1: y={s1_y}..{s1_y+s1_h} (h={s1_h})")
print(f"Gap 1-2: {s2_y - (s1_y+s1_h)}")
print(f"Sec 2: y={s2_y}..{s2_y+s2_h} (h={s2_h})")
print(f"Gap 2-3: {s3_y - (s2_y+s2_h)}")
print(f"Sec 3: y={s3_y}..{s3_y+s3_h} (h={s3_h})")
print(f"Gap 3-4: {s4_y - (s3_y+s3_h)}")
print(f"Sec 4: y={s4_y}..{s4_bottom} (h={s4_h})")
print(f"Bottom margin: {bottom_margin} >= 40: {bottom_margin >= 40}")
