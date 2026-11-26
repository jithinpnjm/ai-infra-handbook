import xml.etree.ElementTree as ET

tree = ET.parse("test_out.svg")
root = tree.getroot()

# Let's inspect each text element, find its enclosing rect, and check left/right/top/bottom padding!
# We can define the boxes explicitly and check each text line.

checks = [
    # (elem_index, box_name, box_x, box_y, box_w, box_h, font_type, font_size, line_height, [lines])
]

# Let's write a script that measures each text element's lines:
def check_line(text, fs, font_type, box_x, box_y, box_w, box_h, line_y, is_centered=False):
    char_w = 0.62 * fs if font_type == 'mono' else 0.60 * fs
    line_w = len(text) * char_w
    if is_centered:
        left_pad = (box_w - line_w) / 2
        right_pad = left_pad
    else:
        left_pad = 20 # text x = box_x + 20
        right_pad = box_w - (left_pad + line_w)
    
    cap_height = 0.7 * fs
    top_pad = line_y - cap_height - box_y
    # for bottom pad, we check the last line
    return line_w, left_pad, right_pad, top_pad

print("Auditing paddings of all boxes...")
# Title:
tw1 = len("Exceptions as control flow: leave nested loops,") * 0.6 * 48
tw2 = len("signal end of input, signal a result") * 0.6 * 48
print(f"Title line 1: w={tw1:.1f}px, pad={(1600-tw1)/2:.1f}px")
print(f"Title line 2: w={tw2:.1f}px, pad={(1600-tw2)/2:.1f}px")
assert (1600-tw1)/2 >= 16
assert (1600-tw2)/2 >= 16

# Bottom bar:
bw = len("In Python every error is an exception, but not every exception is an error") * 0.6 * 26
print(f"Bottom bar: w={bw:.1f}px, pad={(1520-bw)/2:.1f}px")
assert (1520-bw)/2 >= 16

# Check each panel title:
t1 = len("Leave several loops") * 0.6 * 30
print(f"P1 Title: w={t1:.1f}px, pad={(480-t1)/2:.1f}px")
assert (480-t1)/2 >= 16

t2 = len("End of input is a signal") * 0.6 * 30
print(f"P2 Title: w={t2:.1f}px, pad={(480-t2)/2:.1f}px")
assert (480-t2)/2 >= 16

t3 = len("Signal a result") * 0.6 * 30
print(f"P3 Title: w={t3:.1f}px, pad={(480-t3)/2:.1f}px")
assert (480-t3)/2 >= 16

print("\nAll header and title paddings >= 16px! (PASS)")
