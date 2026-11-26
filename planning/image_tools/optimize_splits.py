# Let's write a python script to optimize splits and layout.

# 1. First, what are the widths of the 4 columns?
# Total width available: 1600 - 2*40 = 1520 px.
# 3 gaps between columns = 3 * 16px = 48px.
# Remaining for 4 columns = 1520 - 48 = 1472px.
# Let's allocate:
# Col 0 (Resource header): 320 px
# Col 1 (Utilisation): 384 px
# Col 2 (Saturation): 384 px
# Col 3 (Errors): 384 px
# 320 + 384 * 3 = 1472 px! Exactly 1472 + 48 = 1520!

# Let's check max characters per line for each column:
# For Col 0 (Resource): width = 320 px.
# Node titles: at least 30 px bold sans (0.6 * 30 = 18 px/char).
# If icon is placed ABOVE the title in Col 0:
# Available width = 320 - 32 = 288 px.
# 288 / 18 = 16 characters max per line!
# What about Col 1, 2, 3: width = 384 px.
# At 24 px:
# Conservative monospace (0.62 * 24 = 14.88 px/char):
# Available width = 384 - 32 = 352 px.
# 352 / 14.88 = 23.6 characters max per line!
# For sans-serif (0.6 * 24 = 14.4 px/char):
# 352 / 14.4 = 24.4 characters max per line!

# Let's write an automatic word-wrapping function that splits text into lines such that each line <= max_chars.
def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    current_line = []
    current_len = 0
    for w in words:
        # If adding w exceeds max_chars:
        needed = len(w) if not current_line else current_len + 1 + len(w)
        if needed <= max_chars:
            current_line.append(w)
            current_len = needed
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [w]
            current_len = len(w)
    if current_line:
        lines.append(" ".join(current_line))
    return lines

