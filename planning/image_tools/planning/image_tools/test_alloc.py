#!/usr/bin/env python3

def test_allocation():
    sections = [
        ("Section 1", 125, 200), # 125 to 325
        ("Section 2", 365, 275), # 365 to 640
        ("Section 3", 680, 185), # 680 to 865
        ("Section 4", 905, 150), # 905 to 1055
        ("Bottom bar", 1095, 65) # 1095 to 1160
    ]
    
    prev_end = 0
    for name, y, h in sections:
        gap = y - prev_end if prev_end > 0 else 0
        print(f"{name:12s}: y={y:4d} to {y+h:4d} (h={h}) | gap from prev = {gap}px")
        prev_end = y + h
        
    print(f"Bottom margin: {1200 - prev_end}px")

test_allocation()
