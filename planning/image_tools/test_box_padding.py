# Verify padding >= 16px for every single line in every box

def check_box(name, box_y, box_h, lines):
    # lines is a list of tuples: (text, font_size, line_height_after)
    # first line baseline: box_y + pad_top + font_size * 0.75
    # Let's see: we want top padding >= 16px and bottom padding >= 16px
    # Total text height:
    total_text_h = lines[0][1] # first line ascent
    for i in range(len(lines) - 1):
        total_text_h += lines[i][2] # line height
    total_text_h += lines[-1][1] * 0.25 # descent of last line
    
    extra = box_h - total_text_h
    pad_top = extra / 2.0
    pad_bottom = extra / 2.0
    
    first_baseline = box_y + pad_top + lines[0][1] * 0.75
    last_baseline = first_baseline
    for i in range(len(lines) - 1):
        last_baseline += lines[i][2]
    
    actual_top = (first_baseline - lines[0][1] * 0.75) - box_y
    actual_bot = (box_y + box_h) - (last_baseline + lines[-1][1] * 0.25)
    
    print(f"{name}: h={box_h}, text_h={total_text_h:.1f}, pad_top={actual_top:.1f}, pad_bot={actual_bot:.1f}")
    assert actual_top >= 16, f"{name} top padding {actual_top} < 16"
    assert actual_bot >= 16, f"{name} bottom padding {actual_bot} < 16"

# Step 1: h=96
check_box("Step 1", 75, 96, [
    ("line 1", 30, 32),
    ("line 2", 24, 0)
])

# Step 2: h=198
check_box("Step 2", 183, 198, [
    ("line 1", 30, 31),
    ("line 2", 24, 27),
    ("line 3", 24, 27),
    ("line 4", 24, 27),
    ("line 5", 24, 27),
    ("line 6", 24, 0)
])

# Step 3: h=198
check_box("Step 3", 393, 198, [
    ("line 1", 30, 31),
    ("line 2", 24, 27),
    ("line 3", 24, 27),
    ("line 4", 24, 27),
    ("line 5", 24, 27),
    ("line 6", 24, 0)
])

# Step 4: h=120
check_box("Step 4", 603, 120, [
    ("line 1", 30, 31),
    ("line 2", 24, 27),
    ("line 3", 24, 0)
])

# Step 5: h=120
check_box("Step 5", 735, 120, [
    ("line 1", 30, 31),
    ("line 2", 24, 27),
    ("line 3", 24, 0)
])

# Strip: h=215
check_box("Strip", 875, 215, [
    ("line 1", 24, 26),
    ("line 2", 24, 26),
    ("line 3", 24, 26),
    ("line 4", 24, 26),
    ("line 5", 24, 26),
    ("line 6", 24, 26),
    ("line 7", 24, 0)
])

# Bottom bar: h=55
check_box("Bottom bar", 1110, 55, [
    ("line 1", 25, 0)
])

print("\nALL BOXES HAVE >= 16PX PADDING ON TOP AND BOTTOM!")
