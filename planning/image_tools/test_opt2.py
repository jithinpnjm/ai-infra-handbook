#!/usr/bin/env python3

def test_saving():
    cur_y = 108
    gap = 5
    
    # Steps:
    # Step 1: 5 lines (fs 30, 24, 24, 24, 24)
    # Step 2: 5 lines (fs 30, 24, 24, 24, 24)
    # Step 3: 4 lines (fs 30, 24, 24, 24)
    # Step 4: 3 lines (fs 30, 24, 24)
    # Step 5: 1 line (fs 30)
    # Step 6: 2 lines (fs 30, 24)
    # Step 7: 3 lines (fs 30, 24, 24)
    
    steps_info = [
        ("step-1", 5, [30, 24, 24, 24, 24]),
        ("step-2", 5, [30, 24, 24, 24, 24]),
        ("step-3", 4, [30, 24, 24, 24]),
        ("step-4", 3, [30, 24, 24]),
        ("step-5", 1, [30]),
        ("step-6", 2, [30, 24]),
        ("step-7", 3, [30, 24, 24])
    ]
    
    for name, num_lines, fonts in steps_info:
        y0 = cur_y + 36 # top = cur_y + 36 - 22.5 = cur_y + 13.5 (tpad = 13.5)
        # wait, let's test y0 = cur_y + 39 (tpad = 16.5)
        y0 = cur_y + 39
        y_lines = [y0 + i * 23 for i in range(num_lines)]
        last_y = y_lines[-1]
        bot = last_y + (7.5 if fonts[-1] == 30 else 6.0)
        bh = int((bot - cur_y) + 16.5)
        tpad = (y0 - 0.75 * fonts[0]) - cur_y
        bpad = (cur_y + bh) - bot
        print(f"{name}: by={cur_y} bh={bh} tpad={tpad:.1f} bpad={bpad:.1f}")
        cur_y += bh + gap
        
    steps_bot = cur_y - gap
    print(f"\nSteps bottom: {steps_bot}")
    
    # Right panel matches steps_bot
    right_h = steps_bot - 108
    print(f"Right panel: y=108 h={right_h}")
    
    pub_y = steps_bot + 10
    pub_h = 114
    pub_bot = pub_y + pub_h
    print(f"Public CA strip: y={pub_y} h={pub_h} bot={pub_bot}")
    
    bar_y = pub_bot + 10
    bar_h = 50
    bar_bot = bar_y + bar_h
    print(f"Bottom bar: y={bar_y} h={bar_h} bot={bar_bot}")
    
    bm = 1200 - bar_bot
    print(f"Canvas bottom margin: {bm}px (>= 40: {bm >= 40})")

test_saving()
