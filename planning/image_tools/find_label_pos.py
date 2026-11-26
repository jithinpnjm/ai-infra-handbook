import math

# Test coordinates for gpu and rack1
# Left circle cx=1120, right circle cx=1255, cy=380, r=80
r = 80
cy = 380

# gpu at (1085, 345)
# rack1 at (1290, 345)

for name, txt, cx, is_mono, fs in [("gpu", "gpu", 1120, True, 26), ("rack1", "rack1", 1255, True, 26)]:
    tw = len(txt) * 0.62 * fs
    th = fs
    print(f"\nTesting {name}: tw={tw:.1f}, th={th}")
    
    # Try different y positions
    for ty in range(330, 360, 5):
        # find distance from center
        dy = abs(ty - cy)
        # horizontal span of circle at ty
        dx_circle = math.sqrt(r**2 - dy**2)
        circle_left = cx - dx_circle
        circle_right = cx + dx_circle
        
        # let's try tx
        for tx in range(cx - 30, cx + 40, 5):
            left_t = tx - tw / 2
            right_t = tx + tw / 2
            pad_l = left_t - circle_left
            pad_r = circle_right - right_t
            
            top_t = ty - th
            # circle top at tx
            dx_from_center = abs(tx - cx)
            if dx_from_center < r:
                circle_top_at_tx = cy - math.sqrt(r**2 - dx_from_center**2)
                pad_t = top_t - circle_top_at_tx
            else:
                pad_t = -999
                
            if pad_l >= 16 and pad_r >= 16 and pad_t >= 16:
                print(f"  MATCH: ty={ty}, tx={tx} -> padL={pad_l:.1f}, padR={pad_r:.1f}, padT={pad_t:.1f}")
                break
