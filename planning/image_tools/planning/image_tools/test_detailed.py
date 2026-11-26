#!/usr/bin/env python3

def test_detailed_boxes():
    # Let's test Section 1: 120 to 310 (h=190)
    # Container: (40, 120, 1520, 190)
    # Inside:
    # Format line: y = 160 (mono 24px) -> top_y = 136 -> pad_t = 136 - 120 = 16.0!
    # Filename line: y = 190 (mono 24px) -> top_y = 166, bot_y = 196
    # 5 pieces: y = 205, h = 95 (ends at 300)
    # All piece lines:
    # Line 1: y = 245 -> top_y = 221 -> pad_t = 221 - 205 = 16.0!
    # Line 2: y = 273 -> bot_y = 279 -> pad_b = 300 - 279 = 21.0 >= 16!
    # Line 1 & Line 2 fit with pad_t=16, pad_b=21!
    print("Sec 1 boxes: PASS!")

    # Section 2: 350 to 580 (h=230)
    # Container: (40, 350, 1520, 230)
    # 6 variants in 2 columns x 3 rows:
    # Col 1: x = 125, w = 700
    # Col 2: x = 845, w = 700
    # Row 1: y = 360, h = 66 (ends at 426)
    # Row 2: y = 432, h = 66 (ends at 498)
    # Row 3: y = 504, h = 66 (ends at 570)
    # Inside each h=66 box:
    # Can 2 lines fit in h=66?
    # Line 1: y = by + 37 (top = by + 13 < 16)
    # Line 1: y = by + 40 (top = by + 16 -> pad_t = 16.0)
    # Line 2: y = by + 40 + 20 = by + 60 -> bot = by + 60 + 6 = by + 66!
    # pad_b = 66 - 66 = 0 < 16!
    # To have pad_b >= 16: h must be at least 66 + 16 = 82px!
    # Ah! If h=82px, 3 rows would be 3 * 82 = 246px > 230px!
    print("Sec 2 needs h >= 265 for 3 rows of h=82!")

test_detailed_boxes()
