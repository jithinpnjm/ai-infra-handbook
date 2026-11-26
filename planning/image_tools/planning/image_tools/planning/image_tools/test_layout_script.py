import re
import xml.etree.ElementTree as ET

# Define the exact text and wrapping for each element

# 1. Title
# "Numeric types and the quiet traps they hide"
# y=75, x=800, middle, font-size=48

# 2. Six types (Left table, x=40, y=120, w=960, h=660)
# We can have 6 cards inside:
# Card 1: int (y=120, h=95)
# Card 2: float (y=230, h=115)
# Card 3: complex (y=360, h=70)
# Card 4: bool (y=445, h=80)
# Card 5: decimal.Decimal (y=540, h=100) (orange)
# Card 6: fractions.Fraction (y=655, h=75)
# Total height = 120 to 730 or similar.
# Let's adjust exact card heights and gaps.

# Let's write a script to check all paddings with the exact formula:
# factor = 0.62 if mono else 0.6
# pad_left = t_left - box_x >= 16
# pad_right = (box_x + box_w) - t_right >= 16
# pad_top = (baseline - fs) - box_y >= 16
# pad_bottom = (box_y + box_h) - baseline >= 16

def check_box(name, box, lines, align="left", is_mono=False):
    bx, by, bw, bh = box
    factor = 0.62 if is_mono else 0.6
    print(f"\n--- Checking {name}: box=({bx}, {by}, {bw}, {bh}) ---")
    for txt, fs, baseline, anchor_x in lines:
        w = len(txt) * fs * factor
        if align == "middle":
            t_left = anchor_x - w / 2
            t_right = anchor_x + w / 2
        elif align == "right":
            t_left = anchor_x - w
            t_right = anchor_x
        else: # left
            t_left = anchor_x
            t_right = anchor_x + w
        
        pad_l = t_left - bx
        pad_r = (bx + bw) - t_right
        pad_t = (baseline - fs) - by
        pad_b = (by + bh) - baseline
        
        print(f"  Line '{txt}': fs={fs}, w={w:.1f}, pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
        assert pad_l >= 16, f"pad_l {pad_l} < 16 on '{txt}' in {name}"
        assert pad_r >= 16, f"pad_r {pad_r} < 16 on '{txt}' in {name}"
        assert pad_t >= 16, f"pad_t {pad_t} < 16 on '{txt}' in {name}"
        assert pad_b >= 16, f"pad_b {pad_b} < 16 on '{txt}' in {name}"

print("Defining and testing boxes...")
