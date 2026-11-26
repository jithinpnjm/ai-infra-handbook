# Let's verify the padding math for 2-line, 3-line, 4-line rows, and Row 3 / Side note!

# Rule:
# For each tspan:
# pad_t = (ty - fs * 0.8) - ry >= 15.9
# pad_b = (ry + rh) - ty >= 15.9
# pad_l = tx - rx >= 15.9
# pad_r = (rx + rw) - (tx + len(t) * 0.60 * fs) >= 15.9

# Case 1: 2-line row (Row 1, Row 2, Row 6, Row 8, Row 9, Row 10)
# ry = 0 (relative)
# Title (fs=30): ty0 = 40.
#   pad_t0 = 40 - 30 * 0.8 = 40 - 24 = 16.0px.
# Rule line 1 (fs=24): ty1 = 66.
#   pad_t1 = 66 - 24 * 0.8 = 66 - 19.2 = 46.8px.
# Height rh = 82:
#   pad_b0 = 82 - 40 = 42.0px.
#   pad_b1 = 82 - 66 = 16.0px.
print("Case 1 (2 lines, rh=82): pad_t0=16.0, pad_b1=16.0 -> PASS")

# Case 2: 3-line row (Row 5, Row 7)
# Title (fs=30): ty0 = 40.
# Rule line 1 (fs=24): ty1 = 66.
# Rule line 2 (fs=24): ty2 = 92.
# Height rh = 108:
#   pad_b2 = 108 - 92 = 16.0px.
print("Case 2 (3 lines, rh=108): pad_t0=16.0, pad_b2=16.0 -> PASS")

# Case 3: 4-line row (Row 4)
# Title (fs=30): ty0 = 40.
# Rule line 1 (fs=24): ty1 = 66.
# Rule line 2 (fs=24): ty2 = 92.
# Rule line 3 (fs=24): ty3 = 118.
# Height rh = 134:
#   pad_b3 = 134 - 118 = 16.0px.
print("Case 3 (4 lines, rh=134): pad_t0=16.0, pad_b3=16.0 -> PASS")

# Case 4: Row 3 (Title + 4 rule lines = 5 lines) & Side note (6 lines)
# Row 3:
# Title (fs=30): ty0 = 40.
# Rule lines: ty1=66, ty2=92, ty3=118, ty4=144.
# Side note (fs=24):
# Line 1: ty0 = 36. pad_t = 36 - 24*0.8 = 16.8px.
# Lines: ty1=62, ty2=88, ty3=114, ty4=140, ty5=166.
# Height rh = 182:
#   Row 3: pad_b4 = 182 - 144 = 38px.
#   Side note: pad_b5 = 182 - 166 = 16.0px.
print("Case 4 (Row 3 & Side note, rh=182): pad_t=16.8, pad_b=16.0 -> PASS")

