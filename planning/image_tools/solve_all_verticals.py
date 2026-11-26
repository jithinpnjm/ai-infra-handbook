# We have:
# Canvas height = 1200
# Margin top: Title at y=42, 84.
# Header Scenario: y_start = 96
# Bottom bar: y_end = 1184 (height 48 or 50, e.g. 1134 to 1184)
# Space available for:
# Scenario row (height ~108)
# Gap: 12
# 5 Rows:
# Row 1 (Diff 1: title 2 lines, conseq 5 lines; Resp 1: 3 lines) -> max lines = 7
# Row 2 (Diff 2: title 1 line, conseq 4 lines; Resp 2: 5 lines) -> max lines = 5
# Row 3 (Diff 3: title 1 line, conseq 6 lines; Resp 3: 4 lines) -> max lines = 7
# Row 4 (Diff 4: title 2 lines, conseq 3 lines; Resp 4: 3 lines) -> max lines = 5
# Row 5 (Diff 5: title 1 line, conseq 3 lines; Resp 5: 5 lines) -> max lines = 5

# Let's inspect line counts and heights needed for each row:
# For Diff box:
# Title: font 30, line height 34.
# Gap: 10
# Consequence: font 24, line height 26.
# Padding top: 20, padding bottom: 20.

def diff_box_height(title_lines, conseq_lines):
    # Title height:
    t_h = title_lines * 34
    # Conseq height:
    c_h = conseq_lines * 26
    # Total inner:
    inner = t_h + 8 + c_h
    return inner + 36 # 18 top, 18 bottom

def resp_box_height(resp_lines):
    # Resp lines: font 24, line height 26.
    c_h = resp_lines * 26
    return c_h + 36

# Rows:
# Row 1: title=2, c=5 -> diff_h = 2*34 + 8 + 5*26 + 36 = 68 + 8 + 130 + 36 = 242.
# Wait, can title be 1 line?
# "1 Requests are long, variable and somewhat stateful" = 51 chars.
# At 30px, 51 * 18 = 918px. Box width is 740, so title MUST be 2 lines.
# But what about consequence?
# If consequence is 4 lines instead of 5:
# 201 chars / 4 = 50.25 chars. At x=60, 50 * 14.4 = 720. 60 + 720 = 780 (box edge). So 5 lines is needed.
# Let's check Row 1 height = 205 px if line height is 24/25:
# Let's write an optimizer.
