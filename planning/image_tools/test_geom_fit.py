#!/usr/bin/env python3

def test_exact_fit():
    # Columns setup:
    # Margin left = 45, Margin right = 45 -> 90 px
    # 3 gaps of 25 px -> 75 px
    # Total available = 1600 - 90 - 75 = 1435 px
    
    # Col 1: pre_tasks -> w = 360
    # Col 2: tasks     -> w = 425
    # Col 3: handlers  -> w = 325
    # Col 4: post_tasks -> w = 325
    # Sum = 360 + 425 + 325 + 325 = 1435 px. Exactly 1435!
    
    cols = {
        "pre_tasks": (45, 360),
        "tasks": (45 + 360 + 25, 425),
        "handlers": (45 + 360 + 25 + 425 + 25, 325),
        "post_tasks": (45 + 360 + 25 + 425 + 25 + 325 + 25, 325)
    }
    
    for name, (x, w) in cols.items():
        print(f"Col {name}: x={x}, w={w}, right_edge={x+w}")
    print("Final right margin:", 1600 - (cols["post_tasks"][0] + cols["post_tasks"][1]))

test_exact_fit()
