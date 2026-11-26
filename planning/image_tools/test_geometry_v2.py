# Optimize box heights and y-coordinates for H=1200

# Available vertical space:
# Title: y=20 to y=60 (baseline at 52)
# Margin between title and Step 1: 15px -> Step 1 starts at y=75
# Bottom margin: at least 15px -> total usable height = 1200 - 15 = 1185
# Elements:
# Step 1: 2 lines (fs=30, fs=24)
# Step 2: 6 lines (fs=30, fs=24 x 5)
# Step 3: 6 lines (fs=30, fs=24 x 5)
# Step 4: 3 lines (fs=30, fs=24 x 2)
# Step 5: 3 lines (fs=30, fs=24 x 2)
# Strip: 7 lines (fs=24 x 7)
# Bottom bar: 1 line (fs=25)

# If line spacing:
# fs=30 -> line height 34
# fs=24 -> line height 28
# Padding top: 20px (baseline of first line = box_y + 20 + fs * 0.8)
# Padding bottom: 20px

def get_box_height(font_sizes, line_heights, pad_top=20, pad_bottom=20):
    # text height from top of line 0 to baseline of line N-1 + descent
    h_text = font_sizes[0] # ascent/height of first line
    for i in range(len(font_sizes) - 1):
        h_text += line_heights[i]
    return pad_top + h_text + pad_bottom

h1 = get_box_height([30, 24], [32], 20, 20) # 30 + 32 = 62 -> 102
h2 = get_box_height([30, 24, 24, 24, 24, 24], [32, 28, 28, 28, 28], 20, 20) # 30 + 144 = 174 -> 214
h3 = get_box_height([30, 24, 24, 24, 24, 24], [32, 28, 28, 28, 28], 20, 20) # 214
h4 = get_box_height([30, 24, 24], [32, 28], 20, 20) # 30 + 60 = 90 -> 130
h5 = get_box_height([30, 24, 24], [32, 28], 20, 20) # 130

# Strip: 7 lines of 24
h_strip = get_box_height([24]*7, [27]*6, 20, 20) # 24 + 162 = 186 -> 226

# Bottom bar:
h_bottom = 50

print("Heights:", h1, h2, h3, h4, h5, h_strip, h_bottom)
total_boxes = h1 + h2 + h3 + h4 + h5 + h_strip + h_bottom
print("Sum of boxes:", total_boxes)
# Gaps: 6 gaps between 7 boxes
# 75 (start) + total_boxes + 6 * gap <= 1185
rem = 1185 - 75 - total_boxes
gap = rem / 6
print("Remaining space for 6 gaps:", rem, "-> gap =", gap)
