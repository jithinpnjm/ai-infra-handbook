#!/usr/bin/env python3

def solve_canvas_heights():
    # Total available: 1200
    # Top title: y = 46 to 98
    # Section 1: y = 120 to 300 (h = 180)
    # Section 2: y = 340 to 620 (h = 280) -> 3 rows of h=82
    # Section 3: y = 660 to 860 (h = 200)
    # Section 4: y = 900 to 1055 (h = 155)
    # Bottom bar: y = 1095 to 1160 (h = 65)
    # Margin bottom: 40
    # Gaps between sections:
    # 340 - 300 = 40
    # 660 - 620 = 40
    # 900 - 860 = 40
    # 1095 - 1055 = 40
    print("Heights and 40px gaps:")
    sections = [
        ("Section 1", 120, 180),
        ("Section 2", 340, 280),
        ("Section 3", 660, 200),
        ("Section 4", 900, 155),
        ("Bottom bar", 1095, 65)
    ]
    for name, y, h in sections:
        print(f"  {name:12s}: y={y:4d} to {y+h:4d} (h={h})")
    print(f"Bottom margin: {1200 - 1160}px")

solve_canvas_heights()
