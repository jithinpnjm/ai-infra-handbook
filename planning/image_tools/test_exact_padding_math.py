def test_node_pads(card_h, lines_info):
    # lines_info: list of (text, font_size, is_bold)
    # Icon is at left: x=20..76 (56x56 px), vertically centered in card_h
    # Text starts at x=88, card width = 710. Right edge = 710 - 20 = 690.
    # Available text width = 690 - 88 = 602 px.
    
    # Let's compute text block vertical bounds:
    # First line cap-height ~ 0.72 * fs1
    # Line heights: 30px -> 36px line height; 24px -> 30px line height
    num_lines = len(lines_info)
    fs1 = lines_info[0][1]
    
    # Total height of text block:
    # If 1 line:
    if num_lines == 1:
        text_h = fs1 * 0.72
        top_pad = (card_h - text_h) / 2
        bot_pad = top_pad
        baseline = top_pad + text_h
        baselines = [baseline]
    elif num_lines == 2:
        lh = 32
        text_h = fs1 * 0.72 + lh
        top_pad = (card_h - text_h) / 2
        baseline1 = top_pad + fs1 * 0.72
        baseline2 = baseline1 + lh
        baselines = [baseline1, baseline2]
        bot_pad = card_h - (baseline2 + lines_info[1][1] * 0.2)
    elif num_lines == 3:
        lh = 30
        text_h = fs1 * 0.72 + 2 * lh
        top_pad = (card_h - text_h) / 2
        baseline1 = top_pad + fs1 * 0.72
        baseline2 = baseline1 + lh
        baseline3 = baseline2 + lh
        baselines = [baseline1, baseline2, baseline3]
        bot_pad = card_h - (baseline3 + lines_info[2][1] * 0.2)
        
    print(f"Card H={card_h}, Lines={num_lines}: top_pad={top_pad:.1f}px, bot_pad={bot_pad:.1f}px")
    for idx, (t, fs, b) in enumerate(lines_info):
        w = len(t) * 0.6 * fs
        print(f"  Line {idx+1} (fs={fs}, y_base={baselines[idx]:.1f}, w={w:.1f}px/602px): '{t}'")
    return top_pad >= 16 and bot_pad >= 16

# Test R1_Q1 in 125 px height
print("--- R1_Q1 ---")
test_node_pads(125, [
    ("Is there a purpose-built module", 30, True),
    ("(package, service, user, file, lineinfile,", 24, False),
    ("template, sysctl, systemd, mount, cron)?", 24, False)
])
