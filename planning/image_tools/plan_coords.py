#!/usr/bin/env python3

def plan_layout():
    # Canvas
    W, H = 1600, 1200
    
    # Title: y=30 to 115
    title_y1 = 52
    title_y2 = 106
    
    # Left steps
    # Card width: 1030 (x=40..1070)
    # Right panel: x=1095, w=465, y=130..986 (h=856)
    
    steps = [
        ("Step 1", 146, 5), # 5 lines
        ("Step 2", 168, 6), # 6 lines
        ("Step 3", 122, 4), # 4 lines
        ("Step 4", 100, 3), # 3 lines
        ("Step 5",  64, 1), # 1 line
        ("Step 6",  82, 2), # 2 lines
        ("Step 7", 100, 3)  # 3 lines
    ]
    
    gap = 12
    cur_y = 130
    for name, h, num_lines in steps:
        print(f"{name}: y={cur_y} h={h} bottom={cur_y + h}")
        cur_y += h + gap
    
    steps_bottom = cur_y - gap
    print(f"Steps bottom: {steps_bottom}")
    
    # Public CA strip
    pub_y = steps_bottom + 16
    pub_h = 122
    pub_bottom = pub_y + pub_h
    print(f"Public CA strip: y={pub_y} h={pub_h} bottom={pub_bottom}")
    
    # Bottom bar
    bar_y = pub_bottom + 14
    bar_h = 56
    bar_bottom = bar_y + bar_h
    print(f"Bottom bar: y={bar_y} h={bar_h} bottom={bar_bottom}")
    print(f"Remaining bottom margin: {H - bar_bottom}")

plan_layout()
