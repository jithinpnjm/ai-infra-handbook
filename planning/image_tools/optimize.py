#!/usr/bin/env python3

def optimize_steps():
    # We want tpad >= 16 and bpad >= 16 for all boxes.
    # For a title line at fs=30, ascender = 22.5.
    # First baseline y0 = by + 39 (top = by + 16.5, tpad = 16.5 >= 16)
    # Subsequent lines at fs=24, line spacing = 24.
    # Last line y_last: descender = 6.0.
    # bot = y_last + 6.0
    # To get bpad >= 16: bh >= (bot - by) + 16.
    
    steps_info = [
        ("step-1", 5, [30, 24, 24, 24, 24]),
        ("step-2", 5, [30, 24, 24, 24, 24]),
        ("step-3", 4, [30, 24, 24, 24]),
        ("step-4", 4, [30, 24, 24, 24]),
        ("step-5", 1, [30]), # 1 line
        ("step-6", 2, [30, 24]),
        ("step-7", 3, [30, 24, 24])
    ]
    
    cur_y = 118
    gap = 7
    total_steps = []
    
    for name, num_lines, fonts in steps_info:
        y0 = cur_y + 39
        y_lines = [y0 + i * 24 for i in range(num_lines)]
        last_y = y_lines[-1]
        bot = last_y + (7.5 if fonts[-1] == 30 else 6.0)
        min_bh = int((bot - cur_y) + 17)
        tpad = (y0 - 0.75 * fonts[0]) - cur_y
        bpad = (cur_y + min_bh) - bot
        total_steps.append((name, cur_y, min_bh, y_lines, tpad, bpad))
        print(f"{name}: by={cur_y} bh={min_bh} y_lines={y_lines} tpad={tpad:.1f} bpad={bpad:.1f}")
        cur_y += min_bh + gap
        
    steps_bot = cur_y - gap
    print(f"\nSteps bottom: {steps_bot}")
    
    pub_y = steps_bot + 14
    # Public CA strip has 4 lines of fs=24:
    # First line at pub_y + 34 (top = pub_y + 34 - 18 = pub_y + 16, tpad = 16)
    # y_lines = pub_y + 34 + i * 24 (last = pub_y + 106, bot = pub_y + 112)
    # pub_h = 112 + 18 = 130 (bpad = 18)
    pub_h = 130
    pub_bot = pub_y + pub_h
    print(f"Public CA strip: y={pub_y} bh={pub_h} bot={pub_bot}")
    
    bar_y = pub_bot + 12
    # Bottom bar has 1 line of fs=26:
    # y = bar_y + 35 (top = bar_y + 35 - 19.5 = bar_y + 15.5, bot = bar_y + 35 + 6.5 = bar_y + 41.5)
    # bar_h = 58 (bpad = 16.5)
    bar_h = 58
    bar_bot = bar_y + bar_h
    print(f"Bottom bar: y={bar_y} bh={bar_h} bot={bar_bot}")
    
    bm = 1200 - bar_bot
    print(f"Canvas bottom margin: {bm}px (>= 40: {bm >= 40})")

optimize_steps()
