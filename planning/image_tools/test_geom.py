#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def test_full_geometry():
    # Card X coords
    step_x = 40
    step_w = 1030 # ends at 1070
    right_x = 1090
    right_w = 470 # ends at 1560
    
    # Check Step 1 to 7 Y coords
    steps = [
        ("Step 1", 130, 126),
        ("Step 2", 264, 126),
        ("Step 3", 398, 106),
        ("Step 4", 512, 86),
        ("Step 5", 606, 56),
        ("Step 6", 670, 72),
        ("Step 7", 750, 92)
    ]
    for i in range(len(steps)-1):
        gap = steps[i+1][1] - (steps[i][1] + steps[i][2])
        print(f"Gap {steps[i][0]} to {steps[i+1][0]}: {gap}px")
    
    right_y = 130
    right_h = 712 # ends at 842
    
    pub_y = 862
    pub_h = 164 # ends at 1026
    
    bar_y = 1046
    bar_h = 66 # ends at 1112
    
    print(f"Bottom margin: {1200 - (bar_y + bar_h)}px")
    assert 1200 - (bar_y + bar_h) >= 40

test_full_geometry()
