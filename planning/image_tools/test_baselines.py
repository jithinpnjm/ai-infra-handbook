def calc_card_text_y(card_y, card_h, num_lines, dy=28, font_size=24):
    text_block_h = font_size + (num_lines - 1) * dy
    pad_top = (card_h - text_block_h) / 2
    # Baseline for first line is pad_top + font_size * 0.8
    first_baseline = card_y + pad_top + 20
    # Last line baseline is first_baseline + (num_lines - 1) * dy
    last_baseline = first_baseline + (num_lines - 1) * dy
    # Bottom margin = card_y + card_h - (last_baseline + font_size * 0.2)
    pad_bottom = card_y + card_h - (last_baseline + 5)
    print(f"h={card_h}, lines={num_lines}: pad_top={pad_top:.1f}, pad_bottom={pad_bottom:.1f}")
    return first_baseline

print("P1 cards:")
p1_h = [86, 172, 144, 116, 144, 86]
p1_lines = [2, 5, 4, 3, 4, 2]
for h, nl in zip(p1_h, p1_lines):
    calc_card_text_y(0, h, nl)

print("\nP2 cards:")
p2_h = [125, 155, 125, 95, 125]
p2_lines = [3, 4, 3, 2, 3]
for h, nl in zip(p2_h, p2_lines):
    calc_card_text_y(0, h, nl)
