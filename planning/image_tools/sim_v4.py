# Let's check the complete vertical layout with Section 1 h=160 and Section 3 h=290:
s1_y = 130
s1_h = 160
s1_bottom = s1_y + s1_h # 290

gap_1_2 = 40
s2_y = s1_bottom + gap_1_2 # 330
s2_h = 360
s2_bottom = s2_y + s2_h # 690

gap_2_3 = 40
s3_y = s2_bottom + gap_2_3 # 730
s3_h = 290
s3_bottom = s3_y + s3_h # 1020

gap_3_4 = 40
s4_y = s3_bottom + gap_3_4 # 1060
s4_h = 70
s4_bottom = s4_y + s4_h # 1130

bottom_margin = 1200 - s4_bottom # 70

print(f"Sec 1: {s1_y}..{s1_bottom} (h={s1_h})")
print(f"Gap 1-2: {gap_1_2}")
print(f"Sec 2: {s2_y}..{s2_bottom} (h={s2_h})")
print(f"Gap 2-3: {gap_2_3}")
print(f"Sec 3: {s3_y}..{s3_bottom} (h={s3_h})")
print(f"Gap 3-4: {gap_3_4}")
print(f"Sec 4: {s4_y}..{s4_bottom} (h={s4_h})")
print(f"Bottom margin: {bottom_margin} >= 40: {bottom_margin >= 40}")
