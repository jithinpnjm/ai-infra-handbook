# Check clearance between icon and text in panel-access-note:
box_x = 40
box_y = 685
box_w = 740
box_h = 260

icon_x = 65
icon_y = 725
icon_w = 56
icon_h = 56

text_x = 145
text_y0 = 738
line_h = 32
fs = 24

lines = [
    "I._C1__X is still readable: mangling",
    "prevents collisions in deep hierarchies,",
    "it does not prevent deliberate access,",
    "much as Java private fields can be read",
    "through setAccessible(True) reflection"
]

print("Access Note:")
print(f"Icon rect: x=[{icon_x}, {icon_x+icon_w}], y=[{icon_y}, {icon_y+icon_h}]")
for i, l in enumerate(lines):
    w = len(l) * 0.6 * fs
    ty = text_y0 + i * line_h
    t_top = ty - fs
    t_bottom = ty
    print(f"Line {i}: x=[{text_x}, {text_x+w:.1f}], y=[{t_top}, {t_bottom}]")
    # check overlap with icon
    x_overlap = not (text_x + w < icon_x or text_x > icon_x + icon_w)
    y_overlap = not (t_bottom < icon_y or t_top > icon_y + icon_h)
    if x_overlap and y_overlap:
        print(f"  OVERLAP with icon on line {i}!")
    else:
        print(f"  NO overlap with icon (gap = {text_x - (icon_x + icon_w)}px)")

