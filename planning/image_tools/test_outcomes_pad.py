# Test outcome boxes padding
# Outcome 1: w=460, x=80..540
cx1 = 310
w1 = 28 * 14.4
left1 = cx1 - w1 / 2
right1 = cx1 + w1 / 2
pad_l1 = left1 - 80
pad_r1 = 540 - right1
print(f"Outcome 1: left={left1:.1f}, right={right1:.1f}, pad_l={pad_l1:.1f}, pad_r={pad_r1:.1f} (>=16: {pad_l1 >= 16 and pad_r1 >= 16})")

# Outcome 2: w=400, x=600..1000
cx2 = 800
w2 = 23 * 14.4
left2 = cx2 - w2 / 2
right2 = cx2 + w2 / 2
pad_l2 = left2 - 600
pad_r2 = 1000 - right2
print(f"Outcome 2: left={left2:.1f}, right={right2:.1f}, pad_l={pad_l2:.1f}, pad_r={pad_r2:.1f} (>=16: {pad_l2 >= 16 and pad_r2 >= 16})")
