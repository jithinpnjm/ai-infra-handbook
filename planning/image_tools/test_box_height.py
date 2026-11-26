# Check vertical padding for 3 lines of 24px text inside a box of height H
# Font size = 24
# Cap height ~ 17px
# Descent ~ 5px
# Total glyph height ~ 22px

for H in [108, 112, 114, 116, 118, 120]:
    # If 3 lines:
    # We want top padding >= 16px and bottom padding >= 16px.
    # Total available height between top padding and bottom padding = H - 32px.
    # For 3 lines:
    # Top of line 1: y_top + 16
    # Baseline of line 1: y_top + 16 + 17 = y_top + 33
    # Bottom of line 3: y_top + H - 16
    # Baseline of line 3: y_top + H - 16 - 5 = y_top + H - 21
    # Distance between baseline 1 and baseline 3 = (H - 21) - 33 = H - 54.
    # Line spacing dy = (H - 54) / 2
    dy = (H - 54) / 2
    print(f"H={H}: dy={dy:.1f}px. (Baseline 1: 33, Baseline 2: {33+dy:.1f}, Baseline 3: {33+2*dy:.1f})")
