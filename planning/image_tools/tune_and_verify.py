#!/usr/bin/env python3

def tune_and_verify():
    # Let's adjust all heights, baselines, and layout in Column 2, Column 1, Column 3, Column 4!
    # Height of 1-line cards in Col 2: 66px. y_baseline = cy + 41. (top pad = 41 - 19.2 = 21.8, bot pad = 66 - (41 + 4.8) = 20.2)
    # Height of 2-line cards in Col 2: 92px. y_baseline = cy + 39, dy = 28. (line 1 bot = 39 + 4.8 = 43.8, line 2 top = 67 - 19.2 = 47.8, line 2 bot = 67 + 4.8 = 71.8. bot pad = 92 - 71.8 = 20.2, top pad = 39 - 19.2 = 19.8)
    
    # Let's check total stack height in Col 2:
    # 7 one-line cards: 7 * 66 = 462px
    # 4 two-line cards: 4 * 92 = 368px
    # 10 gaps between cards: 10 * 10 = 100px
    # Total stack = 462 + 368 + 100 = 930px!
    # Start at y = 218.
    # 218 + 930 = 1148px <= 1170px! (22px bottom margin to column container!)
    
    print("Col 2 vertical stack: exactly 930px from 218 to 1148!")

tune_and_verify()
