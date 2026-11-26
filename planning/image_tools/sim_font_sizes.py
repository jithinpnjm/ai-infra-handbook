def check_lines(text, width, font_size, is_bold=True):
    char_w = 0.6 * font_size
    usable_w = width - 32
    max_chars = int(usable_w / char_w)
    words = text.split(' ')
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur and (cur_len + 1 + len(w)) > max_chars:
            lines.append(' '.join(cur))
            cur = [w]
            cur_len = len(w)
        else:
            cur.append(w)
            cur_len = len(' '.join(cur))
    if cur:
        lines.append(' '.join(cur))
    overflow = False
    for i, l in enumerate(lines):
        px = len(l) * char_w
        if px > usable_w:
            overflow = True
        print(f"  Line {i+1} ({len(l)} chars, {px:.1f}px / {usable_w}px): '{l}'")
    if overflow:
        print("  !!! OVERFLOW !!!")
    return len(lines), max(len(l)*char_w for l in lines)

print("--- Col 0 at 30 px, width = 270 ---")
check_lines("Ethernet with TCP (front end, storage, control plane)", 270, 30)
check_lines("RoCE v2", 270, 30)
check_lines("InfiniBand", 270, 30)
check_lines("NVLink / NVSwitch", 270, 30)
check_lines("PCIe", 270, 30)

print("\n--- Col 0 at 26 px, width = 270 ---")
check_lines("Ethernet with TCP (front end, storage, control plane)", 270, 26)

