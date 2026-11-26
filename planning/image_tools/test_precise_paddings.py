def check_paddings():
    # Let's test Row 3 (Subprocess) with 6 lines in h = 170:
    # ry = 0, rh = 170
    # fs = 24
    # line_step = 25
    # y0 = 34
    # y lines: 34, 59, 84, 109, 134, 159
    # top_y = 34 - 24 = 10 -> pad_t = 10.
    # bot_y = 159 + 0.25*24 = 165 -> pad_b = 170 - 165 = 5.
    # Wait! If we have extra space on the canvas (78px!), we can make h = 186 or 190 for Subprocess!
    # Let's see: if canvas H = 1200, we have 78px to spare!
    # We can distribute that 78px into the rows:
    # Subprocess: h = 186 (+16px) -> y0 = 38, line_step = 26:
    # y: 38, 64, 90, 116, 142, 168.
    # top_y = 38 - 24 = 14.
    # bot_y = 168 + 6 = 174 -> pad_b = 186 - 174 = 12.
    # If y0 = 40, line_step = 26:
    # y: 40, 66, 92, 118, 144, 170.
    # top_y = 40 - 24 = 16 -> pad_t = 16!
    # bot_y = 170 + 6 = 176.
    # If h = 194:
    # bot_y = 176 -> pad_b = 194 - 176 = 18!
    # BOTH pad_t >= 16 and pad_b >= 16!
    pass

# Let's calculate the optimal row heights where pad_t >= 16 and pad_b >= 16 for all rows!
rows = [
    ("Exceptions", 3, 2),
    ("Files", 4, 2),
    ("Subprocess", 6, 3),
    ("Global state", 3, 2),
    ("Re-runs", 1, 3),
    ("Signals", 2, 1),
    ("Untrusted input", 3, 2)
]

print("Optimal row heights for pad_t >= 16 and pad_b >= 16:")
total_h = 0
for name, m, f in rows:
    nl = max(m, f)
    # y0 = 40 (so pad_t = 40 - 24 = 16)
    # y_last = 40 + (nl - 1) * 26
    # bot_y = y_last + 6
    # rh = bot_y + 16 (so pad_b = 16)
    rh = 40 + (nl - 1) * 26 + 6 + 16
    total_h += rh
    print(f"  {name:15s}: {nl} lines -> rh = {rh}px (y0=40, y_last={40+(nl-1)*26}, bot={40+(nl-1)*26+6})")

print(f"Total rows height: {total_h}px")
gaps = 6 * 8
print(f"Total with gaps: {total_h + gaps}px")
