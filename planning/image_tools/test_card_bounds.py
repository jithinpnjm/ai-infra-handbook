# Verify all cards, all lines, all bounds
from build_svg import col1_wrapped, col2_wrapped, col3_wrapped

# Layout values:
c1_x, c2_x, c3_x = 40, 560, 1080
card_w = 448
pad_x = 24

# Column 1 cards:
# y_starts:
c1_cards = [
    {"lines": col1_wrapped[0], "y": 245, "h": 184, "pad_top": 20},
    {"lines": col1_wrapped[1], "y": 245 + 184 + 9, "h": 244, "pad_top": 20},
    {"lines": col1_wrapped[2], "y": 245 + 184 + 9 + 244 + 8, "h": 214, "pad_top": 20},
    {"lines": col1_wrapped[3], "y": 245 + 184 + 9 + 244 + 8 + 214 + 9, "h": 154, "pad_top": 20}
]

# Column 2 cards:
c2_cards = [
    {"lines": col2_wrapped[0], "y": 245, "h": 424, "pad_top": 20},
    {"lines": col2_wrapped[1], "y": 245 + 424 + 15, "h": 124, "pad_top": 20},
    {"lines": col2_wrapped[2], "y": 245 + 424 + 15 + 124 + 15, "h": 244, "pad_top": 20}
]

# Column 3 cards:
c3_cards = [
    {"lines": col3_wrapped[0], "y": 245, "h": 134, "pad_top": 40},
    {"lines": col3_wrapped[1], "y": 245 + 134 + 25, "h": 194, "pad_top": 40},
    {"lines": col3_wrapped[2], "y": 245 + 134 + 25 + 194 + 26, "h": 194, "pad_top": 40},
    {"lines": col3_wrapped[3], "y": 245 + 134 + 25 + 194 + 26 + 194 + 25, "h": 224, "pad_top": 40}
]

for col_idx, (col_x, cards) in enumerate([(c1_x, c1_cards), (c2_x, c2_cards), (c3_x, c3_cards)]):
    card_x = col_x + 16
    print(f"=== Col {col_idx+1} ===")
    for c_idx, c in enumerate(cards):
        cy = c["y"]
        ch = c["h"]
        lines = c["lines"]
        pad_t = c["pad_top"]
        first_y = cy + pad_t + 20
        last_y = first_y + (len(lines) - 1) * 30
        bot_pad = (cy + ch) - (last_y + 4) # 4px descent
        max_len = max(len(l) for l in lines)
        max_px = max_len * 14.4
        right_pad = card_w - (pad_x + max_px)
        print(f"  Card {c_idx+1}: y={cy}..{cy+ch} (h={ch}), lines={len(lines)}, top_pad={pad_t}px, bot_pad={bot_pad:.1f}px, left_pad={pad_x}px, right_pad={right_pad:.1f}px")
        assert pad_t >= 16, f"Top pad too small in Col {col_idx+1} Card {c_idx+1}"
        assert bot_pad >= 16, f"Bot pad too small in Col {col_idx+1} Card {c_idx+1}"
        assert pad_x >= 16, f"Left pad too small in Col {col_idx+1} Card {c_idx+1}"
        assert right_pad >= 16, f"Right pad too small in Col {col_idx+1} Card {c_idx+1}"

print("\nALL PADDING CHECKS PASSED! Every single side of every card has >= 16px padding!")
