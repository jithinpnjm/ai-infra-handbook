def check_text_box(box_name, lines, font_size, x_start, box_right, icon_right=None):
    print(f"=== {box_name} ===")
    all_ok = True
    for i, line in enumerate(lines, 1):
        w = len(line) * 0.6 * font_size
        r = x_start + w
        pad_r = box_right - r
        pad_l = x_start - (icon_right if icon_right else 0)
        ok = (pad_r >= 16) and (pad_l >= 16)
        if not ok:
            all_ok = False
        print(f"  Line {i}: '{line}' (len={len(line)}) -> w={w:.1f}px, r={r:.1f}px, pad_l={pad_l:.1f}px, pad_r={pad_r:.1f}px [{'OK' if ok else 'FAIL'}]")
    return all_ok

# Rule Box
rule_lines = [
    "The request rate shows at once whether a",
    "slowdown comes with more load (a load problem)",
    "or with the same load (architecture or",
    "resources)"
]
check_text_box("Rule Box", rule_lines, 24, 150, 920, icon_right=118)

# Side List
side_lines = [
    "Also track: tokens/s, batch size,",
    "KV-cache utilisation, preemptions",
    "and evictions"
]
check_text_box("Side List", side_lines, 24, 1040, 1560, icon_right=1010)

# Card 1 (text-anchor="middle" at x=218, box x=40..396, width=356)
def check_centered_box(box_name, lines, font_size, cx, box_left, box_right):
    print(f"=== {box_name} (centered) ===")
    all_ok = True
    for i, line in enumerate(lines, 1):
        w = len(line) * 0.6 * font_size
        left = cx - w/2
        right = cx + w/2
        pad_l = left - box_left
        pad_r = box_right - right
        ok = (pad_l >= 16) and (pad_r >= 16)
        if not ok:
            all_ok = False
        print(f"  Line {i}: '{line}' (len={len(line)}) -> w={w:.1f}px, pad_l={pad_l:.1f}px, pad_r={pad_r:.1f}px [{'OK' if ok else 'FAIL'}]")
    return all_ok

c1_lines = [
    "waiting before",
    "service starts:",
    "arrivals exceed",
    "capacity, or the",
    "batch scheduler",
    "holds batches for",
    "a fill timeout"
]
check_centered_box("Card 1 (Queue)", c1_lines, 24, 218, 40, 396)

c2_lines = [
    "prompt processing and",
    "everything before",
    "the first token"
]
check_centered_box("Card 2 (TTFT)", c2_lines, 24, 606, 428, 784)

c3_lines = [
    "steady generation",
    "speed per token"
]
check_centered_box("Card 3 (TPOT)", c3_lines, 24, 994, 816, 1172)

c4_lines = [
    "what the user feels"
]
check_centered_box("Card 4 (Total)", c4_lines, 24, 1382, 1204, 1560)
