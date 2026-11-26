# Let's optimize the vertical spacing of the lower strips:
# Panels end at y = 810
# Gap 1 = 20 px -> Footer starts at y = 830
# Footer: y = 830, h = 106.
# Footer text lines: 3 lines, line-spacing = 28 px.
# Baseline line 1 = 860, line 2 = 888, line 3 = 916.
# Text top ~ 860 - 18 = 842 (pad_t = 842 - 830 = 12 -> let's make baseline 866).
# If baseline line 1 = 866, line 2 = 894, line 3 = 922:
# Text top = 866 - 18 = 848 (pad_t = 848 - 830 = 18 px >= 16).
# Text bottom = 922 + 6 = 928 (pad_b = (830 + 106) - 928 = 8 px -> need h = 120).
# With Footer y = 825, h = 120, baseline 1 = 863:
# pad_t = (863 - 18) - 825 = 20 px.
# pad_b = (825 + 120) - (863 + 56 + 6) = 945 - 925 = 20 px!
# Footer ends at 945.

# Gap 2 = 18 px -> Result row starts at y = 963
# Result row: y = 963, h = 88.
# 2 lines, line-spacing = 32 px.
# Baseline line 1 = 998, line 2 = 1030.
# pad_t = (998 - 18) - 963 = 17 px >= 16.
# pad_b = (963 + 88) - (1030 + 5) = 1051 - 1035 = 16 px >= 16.
# Result row ends at 1051.

# Gap 3 = 19 px -> Bottom bar starts at y = 1070
# Bottom bar: y = 1070, h = 90.
# 2 lines, line-spacing = 32 px.
# Baseline line 1 = 1106, line 2 = 1138.
# pad_t = (1106 - 18) - 1070 = 18 px >= 16.
# pad_b = (1070 + 90) - (1138 + 5) = 1160 - 1143 = 17 px >= 16.
# Bottom bar ends at 1160.
# Margin to canvas bottom (1200) = 40 px!

print("Testing lower strips spacing:")
print("Footer:", 825, "to", 825 + 120, "pad_t=20", "pad_b=20")
print("Gap 1:", 963 - (825 + 120))
print("Result:", 963, "to", 963 + 88, "pad_t=17", "pad_b=16")
print("Gap 2:", 1070 - (963 + 88))
print("Bottom bar:", 1070, "to", 1070 + 90, "pad_t=18", "pad_b=17")
print("Bottom margin:", 1200 - (1070 + 90))
