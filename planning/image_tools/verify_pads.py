#!/usr/bin/env python3

def verify_all_paddings():
    # 1. Canvas margins
    H = 1200
    W = 1600
    
    # Title
    t_y1 = 46
    t_y2 = 96
    
    # Steps
    step_y = 118
    # heights:
    h1 = 144
    h2 = 144
    h3 = 124
    h4 = 102
    h5 = 62
    h6 = 80
    h7 = 102
    gap = 7
    
    steps = [h1, h2, h3, h4, h5, h6, h7]
    y = step_y
    for i, h in enumerate(steps, 1):
        print(f"Step {i}: y={y}..{y+h} (h={h})")
        y += h + gap
    
    steps_bottom = y - gap
    print(f"Steps bottom: {steps_bottom}")
    
    right_y = 118
    right_h = steps_bottom - right_y
    print(f"Right panel: y={right_y}..{right_y+right_h} (h={right_h})")
    
    pub_y = steps_bottom + 14
    pub_h = 116
    pub_bottom = pub_y + pub_h
    print(f"Public CA strip: y={pub_y}..{pub_bottom} (h={pub_h})")
    
    bar_y = pub_bottom + 12
    bar_h = 50
    bar_bottom = bar_y + bar_h
    print(f"Bottom bar: y={bar_y}..{bar_bottom} (h={bar_h})")
    
    bm = H - bar_bottom
    print(f"Bottom margin: {bm}px (>= 40: {bm >= 40})")
    assert bm >= 40

verify_all_paddings()
