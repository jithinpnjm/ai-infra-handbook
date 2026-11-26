import re
import xml.etree.ElementTree as ET

tree = ET.parse("test_output.svg")
root = tree.getroot()

# Estimate character widths
def est_text_width(text, font_size, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * font_size * factor

print("Checking paddings and widths...")
# Let's inspect each text element in the SVG
# Check that text does not exceed its container
boxes = [
    # (id, x, y, w, h)
    ("left_table", 50, 120, 300, 520),
    ("middle_box", 420, 120, 680, 520),
    ("end_box", 1170, 120, 380, 250),
    ("sort_box", 1170, 410, 380, 230),
    ("comp_box", 50, 665, 1500, 260),
    ("bottom_bar", 50, 955, 1500, 70),
]

for name, bx, by, bw, bh in boxes:
    print(f"Box {name}: width={bw}, height={bh}")

print("Check individual text lines:")
# 1. Main Title
w_title = est_text_width("awk group-by: an associative array counts as the lines pass", 48, False)
print(f"Title width: {w_title:.1f}px inside 1600px canvas (margin={(1600-w_title)/2:.1f}px)")

# 2. Bottom bar
w_bar = est_text_width("An associative array is a lookup table keyed by text, so no sort | uniq -c is needed", 26, False)
print(f"Bottom bar text width: {w_bar:.1f}px inside 1500px box (padding={(1500-w_bar)/2:.1f}px)")

# 3. Middle awk title
w_awk = est_text_width("awk { c[$1]++ }", 32, True)
print(f"awk title width: {w_awk:.1f}px, available space in middle box: {680-100}px")

# 4. Snapshots
for snap_str in ["alice = 1", "alice = 2, bob = 1", "alice = 3, bob = 2"]:
    w_snap = est_text_width(snap_str, 26, True)
    print(f"Snapshot '{snap_str}' width: {w_snap:.1f}px inside 530px container (padding={530-w_snap:.1f}px)")

# 5. END text lines
w_end1 = est_text_width("END { for (k in c)", 24, True)
w_end2 = est_text_width("print c[k], k }", 24, True)
print(f"END line 1 width: {w_end1:.1f}px inside 380-90={290}px")
print(f"END line 2 width: {w_end2:.1f}px inside 380-90={290}px")

# 6. runs once after the last line
w_runs = est_text_width("runs once after the last line", 24, False)
print(f"runs once width: {w_runs:.1f}px inside 380px box (padding={(380-w_runs)/2:.1f}px)")

# 7. Uniq -c without sort outputs
for txt in ["1 alice", "1 bob", "2 alice", "1 bob"]:
    w = est_text_width(txt, 26, True)
    print(f"output card '{txt}' width: {w:.1f}px inside 135px box (padding={(135-w)/2:.1f}px)")

# 8. Sort | uniq -c outputs
for txt in ["3 alice", "2 bob"]:
    w = est_text_width(txt, 30, True)
    print(f"output card '{txt}' width: {w:.1f}px inside 240px box (padding={(240-w)/2:.1f}px)")

print("All width and padding calculations completed!")
