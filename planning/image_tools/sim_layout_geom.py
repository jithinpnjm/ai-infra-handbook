# Complete layout geometry simulator

def text_width(s, fs=24, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(s) * fs * rate

# Canvas: 1600 x 1200

# 1. Pipeline Stages (Row 1: y=95 to 335, h=240)
# Can the 6 stage boxes fit in width 1520 (x=40..1560)?
# Let's allocate widths:
# Box 1: x=40,   w=180 -> right=220
# Gap 1-2: 24px -> x=244
# Box 2: x=244,  w=236 -> right=480
# Gap 2-3: 24px -> x=504
# Box 3: x=504,  w=190 -> right=694
# Gap 3-4: 26px -> x=720
# Box 4: x=720,  w=236 -> right=956
# Gap 4-5: 26px -> x=982
# Box 5: x=982,  w=250 -> right=1232
# Gap 5-6: 32px -> x=1264
# Box 6: x=1264, w=296 -> right=1560

# Margin left = 40, Margin right = 40.
# All gaps between stage boxes: 24, 24, 26, 26, 32.
print("Stage boxes x-coordinates:")
stages_geom = [
    (1, 40, 180, 220),
    (2, 244, 236, 480),
    (3, 504, 190, 694),
    (4, 720, 236, 956),
    (5, 982, 250, 1232),
    (6, 1264, 296, 1560)
]
for num, x, w, r in stages_geom:
    print(f"  Stage {num}: x={x}, w={w}, right={r}")

for i in range(len(stages_geom)-1):
    g = stages_geom[i+1][1] - stages_geom[i][3]
    print(f"  Gap {stages_geom[i][0]}->{stages_geom[i+1][0]}: {g}px")
