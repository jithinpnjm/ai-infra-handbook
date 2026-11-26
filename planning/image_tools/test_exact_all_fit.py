# Canvas: 1600 x 1200
# Top margin: 40px
# Bottom margin: 40px
# Box widths: 1520px (x=40..1560)

# Title:
# y = 40..112 (lines at 64 and 106)
title_bot = 112

# Gap to Box 1: 40px
box1_y = 152 # Shared Host bar
box1_h = 56 # 1 line: baseline at 152 + 35 = 187, top cap 168 (pad 16), bot 192 (pad 16)
box1_bot = box1_y + box1_h # 208

# Gap 1: 40px
box2_y = box1_bot + 40 # 248 (Lane 1)
box2_h = 196 # Lane 1
box2_bot = box2_y + box2_h # 444

# Gap 2: 40px
box3_y = box2_bot + 40 # 484 (Lane 2)
box3_h = 260 # Lane 2
box3_bot = box3_y + box3_h # 744

# Gap 3: 40px
box4_y = box3_bot + 40 # 784 (Lane 3)
box4_h = 118 # Lane 3
box4_bot = box4_y + box4_h # 902

# Gap 4: 40px
box5_y = box4_bot + 40 # 942 (Footer Box)
box5_h = 134 # Footer Box
box5_bot = box5_y + box5_h # 1076

# Gap 5: 40px
box6_y = box5_bot + 40 # 1116 (Takeaway Bar)
box6_h = 44 # Takeaway Bar: wait, let's check 44 vs 56
box6_bot = box6_y + box6_h # 1160

# Margin bottom:
margin_bot = 1200 - box6_bot # 40px!

print(f"box1: {box1_y}..{box1_bot} (h={box1_h})")
print(f"box2: {box2_y}..{box2_bot} (h={box2_h})")
print(f"box3: {box3_y}..{box3_bot} (h={box3_h})")
print(f"box4: {box4_y}..{box4_bot} (h={box4_h})")
print(f"box5: {box5_y}..{box5_bot} (h={box5_h})")
print(f"box6: {box6_y}..{box6_bot} (h={box6_h})")
print(f"margin_bot: {margin_bot}")
assert margin_bot == 40
