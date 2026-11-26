import xml.etree.ElementTree as ET

# Text paddings check for test_host_patterns.svg
# Rule:
# Estimate widths conservatively: sans 0.6 x font-size per character, monospace 0.62 x font-size per character.
# Every text line must fit inside its box with at least 16 px padding. Never let text touch or cross a box edge, an icon or an arrow.

text_items = [
    # (name, text, is_mono, fs, box_x, box_y, box_w, box_h, text_x, text_y, anchor)
    ("Panel 1 pattern", "gpu:login", True, 32, 40, 175, 740, 310, 145, 225, "start"),
    ("Panel 1 label", "either group", False, 26, 40, 175, 740, 310, 145, 262, "start"),
    ("Panel 2 pattern", "gpu:&rack1", True, 32, 820, 175, 740, 310, 925, 225, "start"),
    ("Panel 2 label", "both groups", False, 26, 820, 175, 740, 310, 925, 262, "start"),
    ("Panel 2 circle gpu", "gpu", True, 26, 1030, 295, 170, 170, 1080, 348, "middle"),
    ("Panel 2 circle rack1", "rack1", True, 26, 1180, 295, 170, 170, 1285, 348, "middle"),
    ("Panel 3 pattern", "gpu:!gpu02", True, 32, 40, 525, 740, 310, 145, 575, "start"),
    ("Panel 3 label", "this group without one host", False, 26, 40, 525, 740, 310, 145, 612, "start"),
    ("Panel 4 pattern", "~gpu0[1-4]", True, 32, 820, 525, 740, 310, 925, 575, "start"),
    ("Panel 4 label", "regular expression on names", False, 26, 820, 525, 740, 310, 925, 612, "start"),
    ("Bottom note line 1", "Test a pattern with --list-hosts before a change. ", False, 25, 40, 875, 1520, 95, 815, 917, "middle"),
    ("Bottom note line 2", "A pattern that matches the wrong hosts reaches machines it should not.", False, 25, 40, 875, 1520, 95, 815, 951, "middle"),
    ("Caption bar", "Read the host list before you change a group.", False, 28, 40, 1010, 1520, 70, 800, 1054, "middle")
]

print("=== CHECKING TEXT PADDING INSIDE CONTAINERS (>= 16px) ===")
for name, txt, is_mono, fs, bx, by, bw, bh, tx, ty, anchor in text_items:
    multiplier = 0.62 if is_mono else 0.60
    tw = len(txt) * multiplier * fs
    th = fs
    
    if anchor == "middle":
        left_edge = tx - tw / 2
        right_edge = tx + tw / 2
    else:
        left_edge = tx
        right_edge = tx + tw
        
    top_edge = ty - th
    bot_edge = ty
    
    pad_left = left_edge - bx
    pad_right = (bx + bw) - right_edge
    pad_top = top_edge - by
    pad_bot = (by + bh) - bot_edge
    
    print(f"{name:25s}: padL={pad_left:4.1f}, padR={pad_right:4.1f}, padT={pad_top:4.1f}, padB={pad_bot:4.1f} | tw={tw:5.1f}")
    assert pad_left >= 16, f"{name} pad_left {pad_left} < 16"
    assert pad_right >= 16, f"{name} pad_right {pad_right} < 16"
    assert pad_top >= 16, f"{name} pad_top {pad_top} < 16"
    assert pad_bot >= 16, f"{name} pad_bot {pad_bot} < 16"

print("\nALL TEXT PADDINGS >= 16px! (PASS)")
