import math

cx = 1265
cy = 380
r = 85
tx = 1280
ty = 350
tw = 80.6
th = 26

dy = abs(ty - cy)
dx_circle = math.sqrt(r**2 - dy**2)
circle_left = cx - dx_circle
circle_right = cx + dx_circle

left_t = tx - tw / 2
right_t = tx + tw / 2
pad_l = left_t - circle_left
pad_r = circle_right - right_t
top_t = ty - th
dx_from_center = abs(tx - cx)
circle_top_at_tx = cy - math.sqrt(r**2 - dx_from_center**2)
pad_t = top_t - circle_top_at_tx

print(f"pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}")
