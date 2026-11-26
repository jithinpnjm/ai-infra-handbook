import math
from PIL import Image

def circ_pt(cx, cy, r, deg):
    rad = math.radians(deg)
    return round(cx + r * math.cos(rad), 2), round(cy + r * math.sin(rad), 2)

# Let's test different layout coordinates
cx_c, cy_c = 420, 360
cx_o, cy_o = 1180, 360
cx_h, cy_h = 800, 750
R = 160

# Arrow 1: Closed -> Open (too many failures)
# Across top:
# start at -20 deg on Closed, end at -160 deg on Open
p1_s = circ_pt(cx_c, cy_c, R, -20)
p1_e = circ_pt(cx_o, cy_o, R, -160)
p1_ctrl = (800, 190)

# Arrow 2: Open -> Half-open (after a cool-down)
# Outer right curve:
# start at 35 deg on Open:
p2_s = circ_pt(cx_o, cy_o, R, 35)
# end at -10 deg on Half-open:
p2_e = circ_pt(cx_h, cy_h, R, -10)
p2_ctrl = (1280, 640)

# Arrow 4: Half-open -> Open (trial fails)
# Inner curve:
# start at -65 deg on Half-open:
p4_s = circ_pt(cx_h, cy_h, R, -65)
# end at 135 deg on Open:
p4_e = circ_pt(cx_o, cy_o, R, 135)
p4_ctrl = (960, 520)

# Arrow 3: Half-open -> Closed (trial succeeds)
# Gentle outer left curve or symmetric to Arrow 2:
# If symmetric to Arrow 2:
# start at 190 deg (-170 deg) on Half-open:
p3_s = circ_pt(cx_h, cy_h, R, -170)
# end at 145 deg on Closed:
p3_e = circ_pt(cx_c, cy_c, R, 145)
p3_ctrl = (320, 640)

print("P1:", p1_s, p1_ctrl, p1_e)
print("P2:", p2_s, p2_ctrl, p2_e)
print("P3:", p3_s, p3_ctrl, p3_e)
print("P4:", p4_s, p4_ctrl, p4_e)
