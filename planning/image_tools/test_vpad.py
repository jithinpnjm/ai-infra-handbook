def check_box_vpadding(box_y, box_h, lines_y, font_sizes):
    # Ascender top
    top_text = lines_y[0] - 0.75 * font_sizes[0]
    top_pad = top_text - box_y
    # Descender bottom
    bot_text = lines_y[-1] + 0.25 * font_sizes[-1]
    bot_pad = (box_y + box_h) - bot_text
    return top_pad, bot_pad

# Step 1: box_y=130, h=136 (or 138)
# If lines at:
# Line 1: y = 130 + 30 = 160 (fs=30) -> top = 160 - 22.5 = 137.5 -> top_pad = 7.5
# If Line 1 at y = 130 + 38 = 168 (fs=30) -> top = 168 - 22.5 = 145.5 -> top_pad = 15.5
# If line spacing is 24px:
# y = 166, 190, 214, 238, 262.
# Last line y = 262 (fs=24) -> bot = 262 + 6 = 268.
# For bot_pad >= 16: box_bottom >= 268 + 16 = 284 -> box_h = 284 - 130 = 154!

print("Testing box heights and vertical padding...")
