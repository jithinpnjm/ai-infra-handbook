def check_box(label, text_lines, box_x, box_y, box_w, box_h, align="left", font_family="sans"):
    factor = 0.62 if font_family == "monospace" else 0.6
    print(f"\n--- Checking {label} (box: x={box_x}, y={box_y}, w={box_w}, h={box_h}) ---")
    for i, (line_text, fs, baseline_y, anchor_x) in enumerate(text_lines):
        line_w = len(line_text) * fs * factor
        if align == "middle":
            t_left = anchor_x - line_w / 2
            t_right = anchor_x + line_w / 2
        elif align == "right":
            t_left = anchor_x - line_w
            t_right = anchor_x
        else: # left
            t_left = anchor_x
            t_right = anchor_x + line_w
        
        pad_left = t_left - box_x
        pad_right = (box_x + box_w) - t_right
        pad_top = (baseline_y - fs) - box_y
        pad_bottom = (box_y + box_h) - baseline_y
        
        print(f"  Line '{line_text}' (fs={fs}):")
        print(f"    width={line_w:.1f}px, x=[{t_left:.1f}, {t_right:.1f}]")
        print(f"    pad_left={pad_left:.1f}px, pad_right={pad_right:.1f}px, pad_top={pad_top:.1f}px, pad_bottom={pad_bottom:.1f}px")
        
        assert pad_left >= 16, f"pad_left {pad_left:.1f} < 16 for '{line_text}'"
        assert pad_right >= 16, f"pad_right {pad_right:.1f} < 16 for '{line_text}'"
        assert pad_top >= 16, f"pad_top {pad_top:.1f} < 16 for '{line_text}'"
        assert pad_bottom >= 16, f"pad_bottom {pad_bottom:.1f} < 16 for '{line_text}'"

# Let's test with the adjusted heights & baselines:

# 1. Main Title: canvas 1600x1200
check_box("Title", [
    ("Which driver branch wins: ", 48, 68, 800),
    ("a worked run through the stack", 48, 122, 800)
], 0, 0, 1600, 140, align="middle")

# 2. Analogy panel: rect x=40, y=145, w=1520, h=105
# baseline_1 = 186, baseline_2 = 218. box_y = 145, box_h = 105 (ends at 250).
# pad_top = 186 - 24 - 145 = 17 >= 16. pad_bottom = 250 - 218 = 32 >= 16.
check_box("Analogy Panel", [
    ("transparent sheets: where the top sheet has writing you read it, ", 24, 186, 145),
    ("where it is blank the sheet below shows through", 24, 218, 145)
], 40, 145, 1520, 105, align="left")

# 3. Sheet 3 (host_vars): rect x=65, y=300, w=690, h=95
check_box("Sheet 3 (host_vars)", [
    ("a host_vars file for one node ", 24, 342, 160),
    ("sets nothing", 24, 372, 160)
], 65, 300, 690, 95, align="left")

# 4. Sheet 2 (gpu_h100): rect x=65, y=412, w=690, h=92
check_box("Sheet 2 (gpu_h100)", [
    ("gpu_h100 group sets 550", 25, 468, 160)
], 65, 412, 690, 92, align="left")

# 5. Sheet 1 (role default): rect x=65, y=524, w=690, h=95
check_box("Sheet 1 (role default)", [
    ("role default sets an ", 24, 566, 160),
    ("older driver branch", 24, 596, 160)
], 65, 524, 690, 95, align="left")

# 6. Scenario 1 Result: rect x=65, y=645, w=690, h=135
check_box("Scenario 1 Result", [
    ("that node gets 550, ", 24, 688, 160),
    ("because the group layer ", 24, 720, 160),
    ("sits above the role default", 24, 752, 160)
], 65, 645, 690, 135, align="left")

# 7. Scenario 2 Top Sheet (Orange): rect x=845, y=300, w=690, h=160
check_box("Scenario 2 Top Sheet (Orange)", [
    ("extra vars on the command line: ", 24, 348, 940),
    ("-e nvidia_driver_branch", 24, 382, 940),
    (" with a newer value", 24, 416, 940)
], 845, 300, 690, 160, align="left")

# 8. Scenario 2 Result: rect x=845, y=645, w=690, h=135
check_box("Scenario 2 Result", [
    ("every host gets that newer value, ", 24, 688, 940),
    ("because extra vars sit ", 24, 720, 940),
    ("at the top of the stack", 24, 752, 940)
], 845, 645, 690, 135, align="left")

# 9. Debug Panel: rect x=40, y=855, w=1520, h=165
# baseline_1 = 896, line 4 = 896+3*30 = 986.
# pad_top = 896 - 24 - 855 = 17 >= 16. pad_bottom = (855 + 165) - 986 = 34 >= 16.
check_box("Debug Method Panel", [
    ("when a variable has the wrong value, check each layer in order before editing anything: ", 24, 896, 145),
    ("work from the bottom upward, find the lowest layer holding the value you expected, ", 24, 926, 145),
    ("then look at each layer above it until you find the one that replaced it; ", 24, 956, 145),
    ("that is the layer to change, editing any other layer changes nothing", 24, 986, 145)
], 40, 855, 1520, 165, align="left")

# 10. Takeaway Bar: rect x=40, y=1065, w=1520, h=75
check_box("Bottom Bar", [
    ("Find the layer that replaced it", 28, 1112, 800)
], 40, 1065, 1520, 75, align="middle")

print("\nALL BOXES PASSED STRICT CHECK_BOX AUDIT!")
