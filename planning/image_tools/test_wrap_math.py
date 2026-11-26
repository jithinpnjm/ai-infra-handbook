def check_box(box_name, text, box_x, box_w, fs, font_type, lines):
    char_w = 0.62 * fs if font_type == 'mono' else 0.60 * fs
    print(f"=== {box_name} (box_w={box_w}, fs={fs}, type={font_type}, char_w={char_w:.2f}) ===")
    joined = " ".join(lines)
    # verify joined text matches original without extra spaces
    orig_clean = " ".join(text.split())
    assert joined == orig_clean, f"Mismatch:\nOrig:   '{orig_clean}'\nJoined: '{joined}'"
    
    max_w = 0
    for i, line in enumerate(lines):
        w = len(line) * char_w
        pad = (box_w - w) / 2 # if centered
        left_pad = 20 # if left-aligned
        right_pad = box_w - (left_pad + w)
        if w > max_w:
            max_w = w
        print(f"  Line {i+1} ({len(line)} chars, {w:.1f}px): '{line}' -> left_pad={left_pad}px, right_pad={right_pad:.1f}px")
        assert right_pad >= 16, f"Padding right {right_pad:.1f} < 16px in line '{line}'!"
        assert left_pad >= 16, f"Padding left {left_pad} < 16px!"
    print(f"  Max width: {max_w:.1f}px, min margin inside box: {box_w - max_w - 20:.1f}px\n")

print("Checking layout math...")
