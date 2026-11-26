# Let's test the text wrapping of each node to make sure NO text line exceeds width - 32px padding

def check_lines(name, lines, width, font_size, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    max_w = width - 32 # 16px padding on left and right
    print(f"=== {name} (Box width: {width}, max text width: {max_w}) ===")
    ok = True
    for i, line in enumerate(lines):
        w = len(line) * factor * font_size
        status = "OK" if w <= max_w else f"OVERFLOW by {w - max_w:.1f}px"
        if w > max_w:
            ok = False
        print(f"  Line {i+1} [{w:.1f}px / {max_w}px] ({status}): '{line}'")
    return ok

# Test Small example:
# Label: 'ChainMap({retries: 5}, {retries: 3, timeout: 10}): cfg[retries] is 5, cfg[timeout] is 10'
lines_example = [
    "ChainMap({retries: 5}, {retries: 3, timeout: 10}):",
    "cfg[retries] is 5, cfg[timeout] is 10"
]
# Wait, let's check mono vs sans for small example
check_lines("Small example (mono 24px)", lines_example, 730, 24, is_mono=True)
# If box width is 730, text width after 56px icon + 20px gap: width for text is 730 - 90 = 640.
check_lines("Small example with icon (mono 24px)", lines_example, 640, 24, is_mono=True)

