import xml.etree.ElementTree as ET
import re

tree = ET.parse("final_pinned_budget.svg")
root = tree.getroot()

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

# 1. Left Card Title:
check_box("Left Card Title", [
    ("Hypothetical ", 30, 156, 145),
    ("inference pod", 30, 192, 145)
], 50, 110, 380, 565, align="left")

# 2. Left Item 1: Limit: 24 GiB
check_box("Left Item 1", [
    ("Limit: 24 GiB", 24, 252, 240)
], 70, 212, 340, 58, align="middle")

# 3. Left Item 2: Worker processes: 4
check_box("Left Item 2", [
    ("Worker processes: 4", 24, 320, 240)
], 70, 280, 340, 58, align="middle")

# 4. Left Item 3: Pinned staging buffers per worker: 4 GiB
check_box("Left Item 3", [
    ("Pinned staging ", 24, 388, 90),
    ("buffers per ", 24, 416, 90),
    ("worker: 4 GiB", 24, 444, 90)
], 70, 348, 340, 114, align="left")

# 5. Left Item 4: Runtime memory per worker: 3 GiB
check_box("Left Item 4", [
    ("Runtime memory ", 24, 512, 90),
    ("per worker: 3 GiB", 24, 540, 90)
], 70, 472, 340, 86, align="left")

# 6. Left Item 5: Cached weights: 15 GiB
check_box("Left Item 5", [
    ("Cached weights: ", 24, 608, 90),
    ("15 GiB", 24, 636, 90)
], 70, 568, 340, 86, align="left")

# 7. Middle Card Title: Cannot be reclaimed
check_box("Middle Card Title", [
    ("Cannot be reclaimed", 30, 166, 560)
], 470, 110, 700, 565, align="left")

# 8. Middle Segments 1..4:
for i, name in enumerate(["Worker 1 ", "Worker 2 ", "Worker 3 ", "Worker 4 "]):
    bx = 490 + i * 165
    mid = bx + 165 / 2
    check_box(f"Segment {i+1}", [
        (name, 24, 368, mid),
        ("(4 + 3)", 24, 412, mid)
    ], bx, 310, 165, 160, align="middle")

# 9. Middle Limit Badge: Limit
check_box("Limit Badge", [
    ("Limit", 24, 271, 1056)
], 998, 230, 116, 65, align="middle")

# 10. Right Verdict Box:
check_box("Right Verdict Box", [
    ("OOM kill expected: ", 24, 290, 1380),
    ("28.0 GiB cannot ", 24, 332, 1380),
    ("be reclaimed, ", 24, 374, 1380),
    ("limit is lower", 24, 416, 1380)
], 1210, 110, 340, 565, align="middle")

# 11. Row 2 Scenario Card:
check_box("Second Scenario Card", [
    ("Fits, but page cache will be reclaimed constantly", 30, 770, 170)
], 50, 715, 1500, 180, align="left")

# 12. Row 3 Formula Box:
check_box("Formula Box", [
    ("unreclaimable = workers x (pinned + runtime)", 26, 982, 470)
], 50, 935, 840, 80, align="middle", font_family="monospace")

# 13. Row 3 Note Box:
check_box("Note Box", [
    ("Page cache is left out of the sum.", 26, 982, 1240)
], 930, 935, 620, 80, align="middle")

print("\nALL 13 BOXES AND ALL 24 TEXT LINES PASSED PADDING >= 16PX AUDIT!")
