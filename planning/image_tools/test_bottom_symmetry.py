# Check Note Box with icon beside text:
# Box: x=1020, y=850, w=540, h=230 (right edge=1560)
# Icon at x=1048, y=918, w=48, h=38 (ends at x=1096, y=956)
# Text starts at x=1115.
# Text lines at y=930, 968, 1006 (fs=24).
# Text top: 930 - 24 = 906.
# Text bottom: 1006 + 6 = 1012.
# Box top pad: 906 - 850 = 56 px.
# Box bottom pad: 1080 - 1012 = 68 px.
# Icon vertical center: (918 + 956) / 2 = 937.
# Text block center: (906 + 1012) / 2 = 959.
# Gap between icon right (1096) and text (1115): 19 px >= 16 px.
# Left pad to box edge: 1048 - 1020 = 28 px >= 16 px.
# Max text width: 335.04 px (Line 2).
# Right edge of text: 1115 + 335.04 = 1450.04.
# Right padding: 1560 - 1450.04 = 109.96 px >= 16 px.
print("Symmetric layout for bottom row: PERFECT!")
