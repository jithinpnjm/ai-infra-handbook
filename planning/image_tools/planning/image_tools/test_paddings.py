# Check text width and padding for every element
# Need boxes: x = 40, width = 640.
# In Need boxes, icon is at x = 56, width ~56 -> ends at 112.
# Text starts at x = 124.
# Box right edge is 40 + 640 = 680.
# Available width for text = 680 - 124 = 556 px.
# Right padding is 680 - (124 + text_width). We need right padding >= 16 px -> text_width <= 540 px.

# Let's verify each text line:
checks = [
    # (label, font_family, font_size, max_available_width)
    ("Need", "sans", 30, 640),
    ("Feature", "sans", 30, 860),
    ("Long loop with no progress", "sans", 24, 540),
    ("looks like a hang", "sans", 24, 540),
    ("progress bar", "sans", 26, 760),
    ("Waiting on something", "sans", 26, 540),
    ("spinner", "sans", 26, 760),
    ("Watch a changing state", "sans", 26, 540),
    ("--watch polls and redraws the screen", "mono", 25, 760),
    ("Stream new output", "sans", 26, 540),
    ("--follow", "mono", 26, 760),
    ("Operation that finishes", "sans", 24, 540),
    ("asynchronously", "sans", 24, 540),
    ("--wait and --timeout flags; poll the status", "mono", 24, 760),
    ("endpoint with backoff like kubectl rollout status", "mono", 24, 760),
    ("User presses Ctrl+C", "sans", 26, 540),
    ("catch KeyboardInterrupt, clean up,", "mono", 24, 760),
    ("return exit code 130", "mono", 24, 760),
    ("start operation", "sans", 26, 335 - 32), # centered in 335
    ("poll status", "sans", 26, 335 - 32),
    ("with backoff", "sans", 26, 335 - 32),
    ("done, or", "sans", 25, 335 - 32),
    ("--timeout reached", "sans", 25, 335 - 32),
    ("exit code", "sans", 26, 335 - 32),
    ("progress and spinners go to stderr and only on a terminal", "sans", 28, 1520 - 144 - 20),
    ("Think of the person running your tool at 3 a.m.", "sans", 28, 1520 - 40)
]

print("=== CHECKING PADDINGS AND WIDTHS ===")
for text, font_type, size, max_w in checks:
    char_factor = 0.62 if font_type == "mono" else 0.60
    est_w = len(text) * size * char_factor
    padding = max_w - est_w
    ok = padding >= 16
    print(f"[{'PASS' if ok else 'FAIL'}] '{text}' ({font_type} {size}px): est_w={est_w:.1f}px, max_w={max_w}px, slack={padding:.1f}px")
    assert ok, f"Padding violation for '{text}'!"
print("\nALL PADDING CHECKS PASSED!")
